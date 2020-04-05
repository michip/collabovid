import joblib
import en_core_sci_md
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_splitter import SentenceSplitter
import os

from analyze.similarity import JensonShannonSimilarity, CosineDistance
from data.models import Paper
from analyze.splitter import TextToChunksSplitter

class TextVectorizer:

    def __init__(self, matrix_file_name, *args, **kwargs):
        self.matrix_file_name = matrix_file_name
        self._similarity_computer = None
        self._paper_matrix = None

    @property
    def similarity_computer(self):
        if not self._similarity_computer:
            raise AttributeError("Similarity computer not set")
        return self._similarity_computer

    @similarity_computer.setter
    def similarity_computer(self, value):
        self._similarity_computer = value

    @property
    def paper_matrix(self):

        if not self._paper_matrix:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            matrix_path = os.path.join(dir_path, os.path.join('res', self.matrix_file_name))
            if os.path.exists(matrix_path):
                self._paper_matrix = joblib.load(matrix_path)

        return self._paper_matrix

    @paper_matrix.setter
    def paper_matrix(self, value):
        self._paper_matrix = value

    def _calculate_paper_matrix(self, papers):
        matrix = self.vectorize_paper(papers)
        print(matrix.shape)
        return {'matrix': matrix}

    def generate_paper_matrix(self, force_recompute=False):
        matrix_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   os.path.join('res', self.matrix_file_name))

        # initialize the id_map with saved values if possible
        if self.paper_matrix is not None and os.path.exists(matrix_path):
            print(matrix_path, "exists, overwriting..")
            id_map = self._paper_matrix['id_map']
        else:
            id_map = {}

        # determines if a paper needs an update
        def needs_update(paper):
            return force_recompute

        # all papers
        papers = Paper.objects.all()

        # papers that need to be recomputed
        filtered_papers = []

        # represents the index where the paper should be inserted in the final matrix
        new_matrix_idx = len(id_map)
        newly_added = 0
        for p in papers:
            if p.doi not in id_map:
                # paper was not in existing matrix, it needs recomputation and we will append the result
                id_map[p.doi] = new_matrix_idx
                filtered_papers.append(p)
                new_matrix_idx += 1
                newly_added += 1
            elif needs_update(p):
                # paper is in existing matrix, so just mark it for recomputing. An index is already saved in the id_map.
                filtered_papers.append(p)

        if len(filtered_papers) > 0:
            # construct index array based on id map
            index_arr = [''] * len(id_map)
            for doi, idx in id_map.items():
                index_arr[idx] = doi
            paper_matrix = {
                'id_map': id_map,
                'index_arr': index_arr,
            }

            # for every new embedding matrix that is computed, we extend the old one
            for key, computed_matrix in self._calculate_paper_matrix(filtered_papers).items():
                # dimension of newly computed values
                matrix = np.zeros((newly_added, computed_matrix.shape[1]))

                if self.paper_matrix is not None:
                    # extend old matrix with dimensions of newly computed values
                    matrix = np.append(self.paper_matrix[key], computed_matrix, axis=0)

                for i, paper in enumerate(filtered_papers):
                    # get the matrix index for the computed value from the id map
                    matrix_idx = id_map[paper.doi]
                    # replace it with the new computed value
                    matrix[matrix_idx] = computed_matrix[i]
                paper_matrix[key] = matrix

            self.paper_matrix = paper_matrix
            joblib.dump(self.paper_matrix, matrix_path)
            print("Paper matrix exported completed")
        else:
            print("No recomputing of matrix necessary")

    def compute_similarity_scores(self, embedding_vec):
        matrix = self.paper_matrix['matrix']
        similarity_scores = self.similarity_computer.similarities(matrix, embedding_vec)
        return self.paper_matrix['index_arr'], similarity_scores

    def vectorize(self, texts):
        raise NotImplementedError()

    def vectorize_paper(self, paper):
        texts = [p.title + ". " + p.abstract for p in paper]
        return self.vectorize(texts)

    def vectorize_topics(self, topics):
        texts = [t.name + ". " + t.description for t in topics]
        return self.vectorize(texts)


class PretrainedLDA(TextVectorizer):
    def __init__(self, lda_file, vectorizer_file, *args, **kwargs):
        super(PretrainedLDA, self).__init__(*args, **kwargs)

        self.nlp = en_core_sci_md.load(disable=["tagger", "parser", "ner"])
        self.nlp.max_length = 2000000

        self.fix_imports()

        self.vectorizer = joblib.load(vectorizer_file)
        self.lda = joblib.load(lda_file)

        self.similarity_computer = JensonShannonSimilarity()

    def fix_imports(self):
        def spacy_tokenizer(sentence):
            return [word.lemma_ for word in self.nlp(sentence) if
                    not (word.like_num or word.is_stop or word.is_punct or word.is_space or len(word) == 1)]

        # add missing
        setattr(sys.modules['__main__'], 'spacy_tokenizer', spacy_tokenizer)

    def vectorize(self, texts):
        vectors = self.vectorizer.transform(texts)
        return self.lda.transform(vectors)


class SentenceVectorizer(TextVectorizer):
    def __init__(self, model_name='roberta-large-nli-stsb-mean-tokens',
                 title_similarity_factor=0.5,
                 abstract_similarity_factor=0.5,
                 *args, **kwargs):
        super(SentenceVectorizer, self).__init__(*args, **kwargs)

        self.model = SentenceTransformer(model_name, device='cpu')
        self.splitter = TextToChunksSplitter()

        self.similarity_computer = CosineDistance()

        self.title_similarity_factor = title_similarity_factor
        self.abstract_similarity_factor = abstract_similarity_factor

    def compute_similarity_scores(self, embedding_vec):
        title_matrix = self.paper_matrix['title_matrix']
        abstract_matrix = self.paper_matrix['abstract_matrix']

        title_similarity_scores = np.array(self.similarity_computer.similarities(title_matrix, embedding_vec))
        abstract_similarity_scores = np.array(self.similarity_computer.similarities(abstract_matrix, embedding_vec))

        return self.paper_matrix['index_arr'], title_similarity_scores * self.title_similarity_factor + \
               abstract_similarity_scores * self.abstract_similarity_factor

    def vectorize(self, texts):
        return self.model.encode(texts)

    def vectorize_paper(self, papers):
        abstract_embeddings = []

        all_chunks = []
        positions = []

        for paper in papers:
            chunks = self.splitter.split_into_chunks(paper.abstract)
            start = len(all_chunks)
            length = len(chunks)
            all_chunks += chunks
            positions.append((start, length))

        print("Extracted all sentences, calculating embedding")
        chunk_embeddings = self.model.encode(all_chunks, batch_size=32, show_progress_bar=True)

        print("Extracting Embedding")

        for start, length in positions:
            if length == 0:
                abstract_embeddings.append(np.zeros(1024))
            else:
                abstract_embeddings.append(np.mean(np.array(chunk_embeddings[start:start + length]), axis=0))

        print("Calculate Title Embedding")

        title_embedding = np.array(self.model.encode([paper.title for paper in papers], show_progress_bar=True))

        return title_embedding, np.array(abstract_embeddings)

    def vectorize_topics(self, topics):

        all_chunks = []
        positions = []

        for topic in topics:
            chunks = self.splitter.split_into_chunks(topic.description)
            start = len(all_chunks)
            length = len(chunks)
            all_chunks += chunks
            positions.append((start, length))

        chunk_embeddings = self.model.encode(all_chunks, batch_size=32, show_progress_bar=True)

        description_embeddings = list()

        for start, length in positions:
            if length == 0:
                description_embeddings.append(np.zeros(1024))
            else:
                description_embeddings.append(chunk_embeddings[start:start + length])

        title_embeddings = np.array(self.model.encode([t.name for t in topics]))

        return title_embeddings, np.array(description_embeddings)

    def _calculate_paper_matrix(self, papers):

        title_embeddings, abstract_embeddings = self.vectorize_paper(papers)

        print('title embeddings', title_embeddings.shape)
        print('abstract embeddings', abstract_embeddings.shape)
        return {'title_matrix': title_embeddings, 'abstract_matrix': abstract_embeddings}
