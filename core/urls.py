# core/urls.py
from django.contrib import admin
from django.urls import path
from todo import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.todos, name='todos'),
    path('filter/<str:filter_type>/', views.todos, name='filter_todos'),
    path('add-todo/', views.add_todo, name='add_todo'),
    path('update-todo/<int:pk>/', views.update_todo, name='update_todo'),
    path('delete-todo/<int:pk>/', views.delete_todo, name='delete_todo'),
    path('toggle-all/', views.toggle_all, name='toggle_all'),
    path('clear-completed/', views.clear_completed, name='clear_completed'),
]