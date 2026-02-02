# todo/views.py
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Todo

def get_todo_context(filter_type='all'):
    todos = Todo.objects.all()
    if filter_type == 'active':
        todos = todos.filter(is_done=False)
    elif filter_type == 'completed':
        todos = todos.filter(is_done=True)
    
    return {
        "todos": todos,
        "count": Todo.objects.filter(is_done=False).count(),
        "filter_type": filter_type
    }

def todos(request, filter_type='all'):
    context = get_todo_context(filter_type)
    template = "todo/partials/list.html" if request.headers.get('HX-Request') else "todo/todos.html"
    return render(request, template, context)

@require_http_methods(["POST"])
def add_todo(request):
    title = request.POST.get("title", "").strip()
    if not title: return HttpResponse(status=204)
    
    todo = Todo.objects.create(title=title)
    context = {"todo": todo, "count": Todo.objects.filter(is_done=False).count(), "update_count": True}
    
    todo_html = render_to_string("todo/partials/todo.html", context, request=request)
    toast_html = render_to_string("todo/partials/toast.html", {"message": "Task added!"})
    return HttpResponse(todo_html + toast_html)

@require_http_methods(["PUT", "POST"])
def update_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    
    if request.method == "POST" and "title" in request.POST:
        todo.title = request.POST.get("title")
    else:
        todo.is_done = not todo.is_done
    
    todo.save()
    context = {"todo": todo, "count": Todo.objects.filter(is_done=False).count(), "update_count": True}
    return render(request, "todo/partials/todo.html", context)

@require_http_methods(["DELETE"])
def delete_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.delete()
    
    count = Todo.objects.filter(is_done=False).count()
    counter_html = render_to_string("todo/partials/counter.html", {"count": count})
    toast_html = render_to_string("todo/partials/toast.html", {"message": "Task deleted"})
    return HttpResponse(counter_html + toast_html)

@require_http_methods(["POST"])
def toggle_all(request):
    active_exists = Todo.objects.filter(is_done=False).exists()
    Todo.objects.all().update(is_done=active_exists)
    return todos(request)

@require_http_methods(["POST"])
def clear_completed(request):
    deleted_count, _ = Todo.objects.filter(is_done=True).delete()
    context = get_todo_context()
    list_html = render_to_string("todo/partials/list.html", context, request=request)
    toast_html = render_to_string("todo/partials/toast.html", {"message": f"Cleared {deleted_count} tasks"})
    return HttpResponse(list_html + toast_html)

@require_http_methods(["GET"])
def edit_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    return render(request, "todo/partials/todo_edit.html", {"todo": todo})