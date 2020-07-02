from django.conf import settings
from django.db.models import Q, QuerySet

from data.models import Paper, Author
from .search import Search, PaperResult

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from django.db.models import Max

from nltk.corpus import words

ENGLISH_WORDS = set(words.words())


class AuthorSearch(Search):

    def find(self, query: str, papers: QuerySet, score_min):
        """

        :param query:
        :param papers:
        :param score_min:
        :return:
        """

        if settings.USING_POSTGRES:

            result_papers = Paper.objects.none()
            possible_authors = Author.objects.all()

            new_query = []  # This will contained a cleaned query which excludes the author names

            for word in query.split():

                authors = possible_authors.annotate(
                    similarity=TrigramSimilarity('last_name', word)).filter(
                    Q(similarity__gt=score_min))

                if authors:

                    max_similarity = authors.aggregate(Max('similarity'))['similarity__max']

                    if max_similarity < 0.85 or word in ENGLISH_WORDS:
                        new_query.append(word)

                    result_papers = result_papers.union(papers.filter(authors__in=authors))
                else:
                    authors = possible_authors.annotate(
                        similarity=TrigramSimilarity('first_name', word)).filter(Q(similarity__gt=score_min))

                    max_similarity = 0

                    if authors:
                        max_similarity = authors.aggregate(Max('similarity'))['similarity__max']

                    print(word, word in ENGLISH_WORDS)

                    if max_similarity < 0.85 or word in ENGLISH_WORDS:
                        # Word is not similar to any first or last name or an common english word
                        new_query.append(word)

            result_papers = result_papers.all()
            return [PaperResult(paper_doi=paper.doi, score=1) for paper in result_papers], " ".join(new_query)
        else:
            return [], query

    @property
    def weight(self):
        return .3