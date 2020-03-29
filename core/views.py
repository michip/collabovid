from django.shortcuts import render, HttpResponse, get_object_or_404, reverse
from django.http import HttpResponseNotFound
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from data.models import Paper, Category, Topic
from analyze import PaperAnalyzer

#analyzer = PaperAnalyzer()

PAPER_PAGE_COUNT = 10

def home(request):

    if request.method == "GET":
        return render(request, "core/home.html")
    elif request.method == "POST":

        search_query = request.POST.get("query", "")

        #related = analyzer.related(search_query, top=10)

        #new_related = list()
        #
        #for paper, score in related:
        #    new_related.append((paper, score*100))

        return render(request, "core/partials/_custom_topic_search_result.html", {'relations': []})



def explore(request):
    if request.method == "GET":
        papers = Paper.objects.all()
        categories = Category.objects.all()

        paginator = Paginator(papers, 25) # Show 25 contacts per page.

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, "core/explore.html",
                      {'papers': page_obj, 'categories': categories, 'search_url': reverse("explore")})

    elif request.method == "POST":
        category_names = request.POST.getlist("categories")
        search_query = request.POST.get("search", "")

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        categories = Category.objects.filter(name__in=category_names)

        papers = Paper.get_paper_for_query(search_query, start_date, end_date, categories).all().order_by("-title")

        if papers.count() > PAPER_PAGE_COUNT:
            paginator = Paginator(papers, PAPER_PAGE_COUNT)
            try:
                page_number = request.POST.get('page')
                page_obj = paginator.get_page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = None
        else:
            page_obj = papers

        return render(request, "core/partials/_search_results.html", {'papers': page_obj})

    return HttpResponseNotFound()


def about(request):
    return render(request, "core/about.html")


def topic(request, id):
    topic = get_object_or_404(Topic, pk=id)

    if request.method == "GET":
        categories = set()
        for paper in topic.papers.all():
            categories.add(paper.category)

        papers = topic.papers.order_by('-topic_score')
        return render(request, "core/topic.html",
                      {'topic': topic, 'categories': categories, 'search_url': reverse("topic", args=(topic.pk,)), 'papers': papers})

    elif request.method == "POST":

        category_names = request.POST.getlist("categories")
        search_query = request.POST.get("search", "")

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        categories = Category.objects.filter(name__in=category_names)

        papers = Paper.get_paper_for_query(search_query, start_date, end_date, categories).filter(topic=topic)

        if papers.count() > PAPER_PAGE_COUNT:
            paginator = Paginator(papers, PAPER_PAGE_COUNT)
            try:
                page_number = request.POST.get('page')
                page_obj = paginator.get_page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = None
        else:
            page_obj = papers

        return render(request, "core/partials/_search_results.html", {'papers': page_obj})

    return HttpResponseNotFound()


def topic_overview(request):
    return render(request, "core/topic_overview.html", {'topics': Topic.objects.all()})
