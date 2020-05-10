from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect
from tasks.models import Task
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta
from django.utils import timezone
from dashboard.tasks.tasks import get_available_tasks
from dashboard.tasks.task_launcher import KubeTaskLauncher, LocalTaskLauncher
from django.conf import settings

from tasks.load import AVAILABLE_TASKS, get_task_by_id


@staff_member_required
def tasks(request):
    tasks = Task.objects.all().order_by('-started_at')
    return render(request, 'dashboard/tasks/task_overview.html', {'tasks': tasks})


@staff_member_required
def task_detail(request, id):
    task = Task.objects.get(pk=id)
    return render(request, 'dashboard/tasks/task_detail.html', {'task': task})


@staff_member_required
def select_task(request):
    if request.method == 'GET':
        return render(request, 'dashboard/tasks/task_select.html', {'services_with_tasks': AVAILABLE_TASKS})

    return HttpResponseNotFound()


@staff_member_required
def create_task(request, task_id):

    task_definition = get_task_by_id(task_id)

    if not task_definition:
        return HttpResponseNotFound()

    if request.method == 'GET':
        return render(request, 'dashboard/tasks/task_create.html', {'definition': task_definition})
    elif request.method == 'POST':
        task_name = request.POST.get('task')
        if task_name in AVAILABLE_TASKS.keys():

            if settings.TASK_LAUNCHER_LOCAL:
                task_launcher = LocalTaskLauncher()
            else:
                task_launcher = KubeTaskLauncher()

            task_config = AVAILABLE_TASKS[task_name]
            task_launcher.launch_task(name=task_name, config=task_config)
            messages.add_message(request, messages.SUCCESS, 'Task started.')
            return redirect('tasks')
        else:
            messages.add_message(request, messages.ERROR, 'Unknown Task name')
            return redirect('task_create')
    return HttpResponseNotFound()


@staff_member_required
def delete_task(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        print(id)
        query = Task.objects.filter(pk=id)
        if query.count() > 0:
            query.delete()
            messages.add_message(request, messages.SUCCESS, 'Deleted Task.')
        else:
            messages.add_message(request, messages.ERROR, 'Failed to delete Task: Unknown Task.')
        return redirect('tasks')
    return HttpResponseNotFound()


@staff_member_required
def delete_all_finished(request):
    if request.method == 'POST':
        days = 1
        date_limit = timezone.now() - timedelta(days=days)
        query = Task.objects.filter(status=Task.STATUS_FINISHED, ended_at__lte=date_limit)
        if query.count() > 0:
            query.delete()
            messages.add_message(request, messages.SUCCESS, 'Deleted All Finished Tasks.')
        else:
            messages.add_message(request, messages.WARNING, 'No Tasks to delete.')
        return redirect('tasks')
    return HttpResponseNotFound()
