def run(output):
    import os
    import requests
    from analyze import get_sentence_transformer_analyzer, get_topic_assignment_analyzer

    from analyze.vectorizer import TitleSentenceVectorizer, SentenceChunkVectorizer, PretrainedLDA

    URLS = {
        "lda-model":
            {
                "download": "https://covid-publications.s3.amazonaws.com/resources/lda/lda.pkl",
                "destination": os.path.join(PretrainedLDA.LDA_BASE_DIR,
                                            "lda.pkl")
            },
        "lda-vectorizer":
            {
                "download": "https://covid-publications.s3.amazonaws.com/resources/lda/vectorizer.pkl",
                "destination": os.path.join(PretrainedLDA.LDA_BASE_DIR,
                                            "vectorizer.pkl")
            },
        "lda-paper-matrix":
            {
                "download": "https://covid-publications.s3.amazonaws.com/resources/lda/paper_matrix.pkl",
                "destination": os.path.join(PretrainedLDA.LDA_BASE_DIR,
                                            "paper_matrix.pkl")
            },
        "title-sentence-paper-matrix":
            {
                "download": "https://covid-publications.s3.amazonaws.com/resources/title_sentence_vectorizer/paper_matrix.pkl",
                "destination": os.path.join(TitleSentenceVectorizer.TITLE_SENTENCE_VECTORIZER_BASE_DIR,
                                            "paper_matrix.pkl")
            },
        "sentence-chunk-paper-matrix":
            {
                "download": "https://covid-publications.s3.amazonaws.com/resources/sentence_chunk_vectorizer/paper_matrix.pkl",
                "destination": os.path.join(SentenceChunkVectorizer.SENTENCE_CHUNK_VECTORIZER_BASE_DIR,
                                            "paper_matrix.pkl")
            }
    }

    def download_file(down, path):
        if os.path.exists(path):
            output(path, "exists, skipping...")
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            r = requests.get(down)
            with open(path, 'wb') as f:
                f.write(r.content)

    for key, config in URLS.items():
        output("Downloading", key)
        download_file(config["download"], config["destination"])

    analyzer = get_sentence_transformer_analyzer()
    analyzer.preprocess()

    topic_analyzer = get_topic_assignment_analyzer()
    topic_analyzer.preprocess()

    topic_analyzer.assign_to_topics()
    output("Vectorizer Setup Completed")

if __name__ == "__main__":
    import django
    django.setup()

    run(print)