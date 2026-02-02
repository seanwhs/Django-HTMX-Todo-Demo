# todo/views.py 
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
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
    return render(request, "todo/partials/todo.html", context)

@require_http_methods(["GET"])
def edit_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    return render(request, "todo/partials/todo_edit.html", {"todo": todo})

def update_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    
    # Handle Title Update (from edit form)
    if request.method == "POST" and "title" in request.POST:
        todo.title = request.POST.get("title")
        todo.save()
    # Handle Toggle (from clicking the task)
    elif request.method == "PUT":
        todo.is_done = not todo.is_done
        todo.save()
    
    context = {
        "todo": todo, 
        "count": Todo.objects.filter(is_done=False).count(), 
        "update_count": True
    }
    return render(request, "todo/partials/todo.html", context)

@require_http_methods(["DELETE"])
def delete_todo(request, pk):
    get_object_or_404(Todo, pk=pk).delete()
    # When deleting, we need to return the counter OOB AND nothing for the row
    count = Todo.objects.filter(is_done=False).count()
    response = render(request, "todo/partials/counter.html", {"count": count})
    return response        

@require_http_methods(["POST"])
def toggle_all(request):
    active_exists = Todo.objects.filter(is_done=False).exists()
    Todo.objects.all().update(is_done=active_exists)
    return todos(request) # Re-render the list partial

@require_http_methods(["POST"])
def clear_completed(request):
    Todo.objects.filter(is_done=True).delete()
    return todos(request)