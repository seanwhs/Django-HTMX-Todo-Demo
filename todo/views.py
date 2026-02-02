# todo/views.py
import time
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db import transaction
from .models import Todo

def get_todo_context(filter_type='all'):
    todos = Todo.objects.filter(is_deleted=False) 
    if filter_type == 'active':
        todos = todos.filter(is_done=False)
    elif filter_type == 'completed':
        todos = todos.filter(is_done=True)
    
    return {
        "todos": todos,
        "count": Todo.objects.filter(is_deleted=False, is_done=False).count(),
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
    context = {"todo": todo, "count": Todo.objects.filter(is_deleted=False, is_done=False).count(), "update_count": True}
    
    todo_html = render_to_string("todo/partials/todo.html", context, request=request)
    toast_html = render_to_string("todo/partials/toast.html", {"message": "Task added!"}, request=request)
    return HttpResponse(todo_html + toast_html)

@require_http_methods(["PUT", "POST"])
def update_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if request.method == "POST" and "title" in request.POST:
        todo.title = request.POST.get("title")
    else:
        todo.is_done = not todo.is_done
    todo.save()
    
    # Get fresh count for the footer
    count = Todo.objects.filter(is_deleted=False, is_done=False).count()
    
    # Render the todo row (context doesn't need update_count anymore)
    todo_html = render_to_string("todo/partials/todo.html", {"todo": todo}, request=request)
    
    # Render the counter (this has hx-swap-oob="true" inside it)
    counter_html = render_to_string("todo/partials/counter.html", {"count": count}, request=request)
    
    # Return both combined. HTMX swaps the row and then scans for the OOB ID to update the footer.
    return HttpResponse(todo_html + counter_html)

@require_http_methods(["DELETE"])
def delete_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.is_deleted = True 
    todo.save()
    
    count = Todo.objects.filter(is_deleted=False, is_done=False).count()
    counter_html = render_to_string("todo/partials/counter.html", {"count": count}, request=request)
    toast_html = render_to_string("todo/partials/toast.html", {
        "message": "Task deleted",
        "todo_id": todo.pk
    }, request=request)
    
    # Return empty string to remove the row, plus OOB updates for counter and toast
    return HttpResponse("" + counter_html + toast_html)

@require_http_methods(["POST"])
def undo_delete(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.is_deleted = False
    todo.save()
    
    context = {
        "todo": todo, 
        "count": Todo.objects.filter(is_deleted=False, is_done=False).count(),
        "update_count": True
    }
    todo_html = render_to_string("todo/partials/todo.html", context, request=request)
    
    response = HttpResponse(todo_html)
    response['HX-Retarget'] = '#todos'
    response['HX-Reswap'] = 'afterbegin'
    return response

@require_http_methods(["POST"])
def toggle_all(request):
    # Determine if we are marking all as done or all as active
    active_exists = Todo.objects.filter(is_deleted=False, is_done=False).exists()
    Todo.objects.filter(is_deleted=False).update(is_done=active_exists)
    
    # Get fresh data
    context = get_todo_context('all')
    
    # 1. Render the rows for the #todos container
    list_html = render_to_string("todo/partials/list.html", context, request=request)
    
    # 2. Render the counter (which has hx-swap-oob="true" inside it)
    counter_html = render_to_string("todo/partials/counter.html", {"count": context['count']}, request=request)
    
    # Return both together
    return HttpResponse(list_html + counter_html)

@require_http_methods(["POST"])
def clear_completed(request):
    # Find all completed tasks that aren't already soft-deleted
    completed_todos = Todo.objects.filter(is_done=True, is_deleted=False)
    
    if not completed_todos.exists():
        return HttpResponse(status=204)

    # Tag this specific group with a batch timestamp
    batch_id = f"batch_{int(time.time())}"
    
    # Use transaction.atomic if you want to be extra safe
    with transaction.atomic():
        completed_todos.update(is_deleted=True, note=batch_id)
    
    # Refresh data for the UI components
    context = get_todo_context('all')
    
    # 1. The main list (replaces current #todos innerHTML)
    list_html = render_to_string("todo/partials/list.html", context, request=request)
    
    # 2. The counter (OOB swap)
    counter_html = render_to_string("todo/partials/counter.html", {"count": context['count']}, request=request)
    
    # 3. The Bulk Toast (OOB swap)
    toast_html = render_to_string("todo/partials/toast.html", {
        "message": "Cleared completed tasks",
        "undo_batch_id": batch_id
    }, request=request)
    
    # Combine everything in one response
    return HttpResponse(list_html + counter_html + toast_html)

@require_http_methods(["POST"])
def undo_clear(request, batch_id):
    Todo.objects.filter(note=batch_id).update(is_deleted=False, note="")
    # Re-using the main todos view works because it includes the counter context
    return todos(request)
    # 1. Update DB
    Todo.objects.filter(note=batch_id).update(is_deleted=False, note="")
    # 2. Return todos(request)
    return todos(request)

@require_http_methods(["GET"])
def edit_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    return render(request, "todo/partials/todo_edit.html", {"todo": todo})