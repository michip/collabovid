from django.shortcuts import render
from django.http import HttpResponseNotFound, JsonResponse
from django.core.paginator import EmptyPage, PageNotAnInteger
from data.models import GeoCity, GeoCountry, Paper, Author, Category, Journal, GeoLocation, Topic
from statistics import PaperStatistics, CategoryStatistics
from django.template.loader import render_to_string
import json

from django.utils.timezone import datetime
import requests

from django.conf import settings
from search.request_helper import SearchRequestHelper, SimilarPaperRequestHelper
from django.shortcuts import get_object_or_404

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value as V
from django.db.models.functions import Concat, Greatest
from django.db.models import Count, Max

import json

PAPER_PAGE_COUNT = 10


def home(request):
    if request.method == "GET":
        statistics = PaperStatistics(Paper.objects.all())

        latest_date = Paper.objects.filter(published_at__lte=datetime.now().date()).latest('published_at').published_at

        most_recent_papers = Paper.objects.filter(published_at=latest_date)
        return render(request, "core/home.html", {'statistics': statistics,
                                                  'most_recent_papers': most_recent_papers.order_by('-created_at'),
                                                  'most_recent_paper_statistics': PaperStatistics(most_recent_papers),
                                                  'most_recent_paper_date': latest_date})


def paper(request, doi):
    current_paper = get_object_or_404(Paper, doi=doi)
    similar_request = SimilarPaperRequestHelper(doi, number_papers=10)
    similar_paper = []
    if not similar_request.error:
        similar_paper = similar_request.paginator.page(1)
    return render(request, "core/paper.html", {
        "paper": current_paper,
        "similar_papers": similar_paper,
        "error": similar_request.error
    })


def embedding_visualization(request):
    topics = Topic.objects.all()
    topic_dict = {}
    for topic in topics:
        topic_dict[topic.pk] = [x['doi'] for x in topic.papers.values('doi')]
    return render(request, "core/embedding_visualization.html", {
        'topics': topics,
        'topic_dict': json.dumps(topic_dict)
    })


def paper_cards(request):
    dois = request.GET.get('dois', None)
    if not dois:
        return HttpResponseNotFound()
    dois = json.loads(dois)
    papers = Paper.objects.filter(pk__in=dois)
    papers = sorted(papers, key=lambda x: dois.index(x.doi))
    return render(template_name="core/partials/_search_results.html", request=request,
                  context={'papers': papers, 'show_score': False})



def about(request):
    paper_count = Paper.objects.count()
    return render(request, "core/about.html", {'paper_count': paper_count})


def imprint(request):
    if settings.IMPRINT_URL is None or len(settings.IMPRINT_URL) == 0:
        return HttpResponseNotFound()

    content = requests.get(settings.IMPRINT_URL).text

    return render(request, "core/imprint.html", {"content": content})


def privacy(request):
    if settings.DATA_PROTECTION_URL is None or len(settings.DATA_PROTECTION_URL) == 0:
        return HttpResponseNotFound()

    content = requests.get(settings.DATA_PROTECTION_URL).text
    return render(request, "core/data_protection.html", {"content": content})


def category_overview(request):
    category_statistics = [CategoryStatistics(category) for category in Category.objects.all()]

    return render(request, "core/categories_overview.html", {"category_statistics": category_statistics})


def search(request):
    if request.method == "GET":

        categories = Category.objects.all().order_by("pk")
        selected_categories = request.GET.get("categories", None)

        start_date = request.GET.get("published_at_start", "")
        end_date = request.GET.get("published_at_end", "")

        authors_connection = request.GET.get("authors-connection", "one")

        if authors_connection not in ["one", "all"]:
            authors_connection = "one"

        tab = request.GET.get("tab", "top")

        if tab not in ["newest", "top", "statistics"]:
            tab = "top"

        article_type = request.GET.get("article-type", "all")

        if article_type not in ["all", "reviewed", 'preprints']:
            article_type = "all"

        location_ids = request.GET.get("locations")

        try:
            location_ids = [int(pk) for pk in location_ids.split(',')] if location_ids else []
        except ValueError:
            location_ids = []

        locations = GeoLocation.objects.filter(pk__in=location_ids).annotate(paper_count=Count('papers')).order_by(
            '-paper_count')

        journal_ids = request.GET.get("journals", None)

        try:
            journal_ids = [int(pk) for pk in journal_ids.split(',')] if journal_ids else []
        except ValueError:
            journal_ids = []

        journals = Journal.objects.filter(pk__in=journal_ids).annotate(paper_count=Count('papers')).order_by(
            '-paper_count')

        try:
            selected_categories = [int(pk) for pk in selected_categories.split(',')] if selected_categories else []
        except ValueError:
            selected_categories = []

        author_ids = request.GET.get("authors", None)
        try:
            if author_ids:
                author_ids = [int(pk) for pk in author_ids.split(',')]
            else:
                author_ids = []
        except ValueError:
            author_ids = []

        authors = Author.objects.filter(pk__in=author_ids).annotate(name=Concat('first_name', V(' '), 'last_name'))

        search_query = request.GET.get("search", "").strip()

        form = {
            "start_date": start_date,
            "end_date": end_date,
            "search": search_query,
            "categories": categories,
            'selected_categories': selected_categories,
            "tab": tab,
            "authors": json.dumps(authors_to_json(authors)),
            "authors-connection": authors_connection,
            "journals": json.dumps(journals_to_json(journals)),
            "locations": json.dumps(locations_to_json(locations)),
            "article_type": article_type
        }

        return render(request, "core/search.html", {'form': form})

    elif request.method == "POST":

        categories = request.POST.get("categories", None)

        try:
            categories = [int(pk) for pk in categories.split(',')] if categories else []
        except ValueError:
            categories = []

        if len(categories) == 0:
            categories = [category.pk for category in Category.objects.all()]

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        tab = request.POST.get("tab", "")

        authors = request.POST.get("authors", "")
        authors_connection = request.POST.get("authors-connection", "one")

        if authors_connection not in ["one", "all"]:
            authors_connection = "one"

        journals = request.POST.get("journals")
        locations = request.POST.get("locations")

        search_query = request.POST.get("search", "").strip()

        article_type = request.POST.get("article-type", "all")

        search_request = SearchRequestHelper(start_date, end_date,
                                             search_query, authors, authors_connection, journals,
                                             categories, locations, article_type)

        if search_request.error:
            return render(request, "core/partials/_search_result_error.html",
                          {'message': 'We encountered an unexpected error. Please try again.'})

        if tab == "statistics":
            statistics = PaperStatistics(search_request.papers)
            return render(request, "core/partials/statistics/_statistics.html", {'statistics': statistics})
        else:
            if tab == "top":
                sorted_by = Paper.SORTED_BY_SCORE
            else:
                sorted_by = Paper.SORTED_BY_NEWEST

            paginator = search_request.paginator_ordered_by(sorted_by, page_count=PAPER_PAGE_COUNT)
            try:
                page_number = request.POST.get('page')
                page_obj = paginator.get_page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = None

            return render(request, "core/partials/_search_results.html", {'papers': page_obj,
                                                                          'show_score': False, })


def locations(request):
    countries = GeoCountry.objects.all()

    countries = [
        {
            'pk': country.pk,
            'alpha2': country.alpha_2,
            'count': country.count,
            'displayname': country.displayname
        }
        for country in countries
    ]

    cities = GeoCity.objects.all()

    cities = [
        {
            'pk': city.pk,
            'name': city.name,
            'longitude': city.longitude,
            'latitude': city.latitude,
            'count': city.count,
            'displayname': city.displayname
        }
        for city in cities
    ]

    total_loc_related = Paper.objects.exclude(locations=None).count()
    top_countries = GeoCountry.objects.order_by('-count')[:3]

    return render(
        request,
        "core/map.html",
        {
            "countries": json.dumps(countries),
            "cities": json.dumps(cities),
            "total_loc_related": total_loc_related,
            "top_countries": [
                {
                    "name": x.alias,
                    "count": x.count
                }

                for x in top_countries]
        }
    )


def authors_to_json(authors):
    return_json = []

    for author in authors:
        return_json.append({
            "value": author.name,
            "pk": author.pk
        })
    return return_json


def list_authors(request):
    query = request.GET.get('query', '')

    if query:
        possible_authors = Author.objects.all().annotate(name=Concat('first_name', V(' '), 'last_name'))
        authors = possible_authors.annotate(similarity=TrigramSimilarity('name', query)).order_by(
            '-similarity')[:6]
    else:
        authors = []

    return JsonResponse({"authors": authors_to_json(authors)})


def journals_to_json(journals):
    return_json = []
    for journal in journals:
        return_json.append({
            "pk": journal.pk,
            "value": journal.displayname,
            "count": journal.paper_count
        })
    return return_json


def list_journals(request):
    journals = Journal.objects.all().annotate(paper_count=Count('papers'))

    query = request.GET.get('query', '')

    if query:
        journals = journals.annotate(similarity_name=TrigramSimilarity('name', query)).annotate(
            similarity_alias=TrigramSimilarity('alias', query)).annotate(
            similarity=Greatest('similarity_name', 'similarity_alias')).order_by('-similarity')[:6]
    else:
        journals = journals.order_by('-paper_count')[:6]

    return JsonResponse({"journals": journals_to_json(journals)})


def locations_to_json(locations):
    return [
        {
            "pk": location.pk,
            "value": location.displayname,
            "count": location.paper_count
        }
        for location in locations.all()
    ]


def list_locations(request):
    locations = GeoLocation.objects.all().annotate(paper_count=Count('papers'))

    query = request.GET.get('query', '')

    if query:
        locations = locations.annotate(similarity_name=TrigramSimilarity('name', query)).annotate(
            similarity_alias=TrigramSimilarity('alias', query)).annotate(
            similarity=Greatest('similarity_name', 'similarity_alias')).order_by('-similarity')[:6]
    else:
        locations = locations.order_by('-paper_count')[:6]

    return JsonResponse({"locations": locations_to_json(locations)})
