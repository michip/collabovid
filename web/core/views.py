from django.db.models import Q
from django.shortcuts import render, get_object_or_404, reverse
from django.http import HttpResponseNotFound
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from data.models import Paper, Category, Topic
from data.statistics import Statistics

import requests

from django.conf import settings
from search.request_helper import SearchRequestHelper


PAPER_PAGE_COUNT = 10


def home(request):
    if request.method == "GET":
        statistics = Statistics(Paper.objects.all())
        most_recent_papers = Paper.objects.filter(~Q(preview_image=None)).order_by('-published_at')[:5]
        return render(request, "core/home.html", {'statistics': statistics,
                                                  'most_recent_papers': most_recent_papers})


def about(request):
    paper_count = Paper.objects.count()
    return render(request, "core/about.html", {'paper_count': paper_count})


def topic(request, id):
    topic = get_object_or_404(Topic, pk=id)

    if request.method == "GET":

        return render(request, "core/topic.html",
                      {'topic': topic,
                       'search_url': reverse("topic", args=(topic.pk,))})

    elif request.method == "POST":

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        sorted_by = request.POST.get("sorted_by", "")

        search_query = request.POST.get("search", "").strip()

        score_threshold = 0.0

        if sorted_by == "relevance":

            if len(search_query) > 0:
                sorted_by = Paper.SORTED_BY_SCORE
                score_threshold = 0.6
            else:
                sorted_by = Paper.SORTED_BY_TOPIC_SCORE
        else:
            sorted_by = Paper.SORTED_BY_NEWEST

        search_request = SearchRequestHelper(start_date, end_date, search_query, score_threshold)

        paginator = search_request.paginator_ordered_by(sorted_by, page_count=PAPER_PAGE_COUNT)

        try:
            page_number = request.POST.get('page')
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = None

        return render(request, "core/partials/_search_results.html",
                      {'papers': page_obj, 'show_score': True})

    return HttpResponseNotFound()


def topic_overview(request):
    return render(request, "core/topic_overview.html", {'topics': Topic.objects.all()})


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


def search(request):
    if request.method == "GET":

        start_date = request.GET.get("published_at_start", "")
        end_date = request.GET.get("published_at_end", "")
        tab = request.GET.get("tab", "top")

        if tab not in ["newest", "top", "statistics"]:
            tab = "top"

        search = request.GET.get("search", "").strip()

        form = {
            "start_date": start_date,
            "end_date": end_date,
            "search": search,
            "tab": tab
        }

        return render(request, "core/search.html", {'form': form})

    elif request.method == "POST":
        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        tab = request.POST.get("tab", "")

        search_query = request.POST.get("search", "").strip()
        search_request = SearchRequestHelper(start_date, end_date, search_query)

        if search_request.error:
            return render(request, "core/partials/_search_result_error.html")

        if tab == "statistics":
            statistics = Statistics(search_request.papers)
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