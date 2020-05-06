from django.urls import path, include
from django.shortcuts import redirect
from .views import *

urlpatterns = [
    path('', lambda request: redirect('tasks', permanent=False), name='dashboard'),
    path('tasks', tasks, name='tasks'),
    path('tasks/detail/<int:id>', task_detail, name='task_detail'),
    path('tasks/create/', create_task, name='task_create'),
    path('tasks/delete/', delete_task, name='task_delete'),
    path('tasks/delete-all/', delete_all_finished, name='task_delete_all')
]
