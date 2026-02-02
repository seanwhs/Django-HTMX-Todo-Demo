# todo/views.py
import time
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db import transaction
from .models import Todo


def get_todo_context(filter_type="all", query=""):
    # If filter is 'deleted', show ONLY soft-deleted items. Otherwise, show non-deleted.
    if filter_type == "deleted":
        todos = Todo.objects.filter(is_deleted=True)
    else:
        todos = Todo.objects.filter(is_deleted=False)

    if query:
        todos = todos.filter(title__icontains=query)

    if filter_type == "active":
        todos = todos.filter(is_done=False)
    elif filter_type == "completed":
        todos = todos.filter(is_done=True)

    return {
        "todos": todos,
        "count": Todo.objects.filter(is_deleted=False, is_done=False).count(),
        "filter_type": filter_type,
        "query": query,
    }


def todos(request, filter_type="all"):
    query = request.GET.get("q", "")
    context = get_todo_context(filter_type, query)
    
    if request.headers.get("HX-Request"):
        # Render the list as the main response
        list_html = render_to_string("todo/partials/list.html", context, request=request)
        
        # Render the footer actions as an OOB swap
        footer_html = render_to_string("todo/partials/footer_actions.html", context, request=request)
        
        return HttpResponse(list_html + footer_html)
    
    return render(request, "todo/todos.html", context)


@require_http_methods(["POST"])
def add_todo(request):
    title = request.POST.get("title", "").strip()

    # 1. Validation Check
    error_msg = None
    if not title:
        error_msg = "Please enter a task name."
    elif len(title) < 3:
        error_msg = "Task is too short (min 3 chars)."
    elif len(title) > 50:
        error_msg = "Task is too long (max 50 chars)."

    if error_msg:
        # Return OOB fragment that unhides the error div
        return HttpResponse(
            f'<div id="todo-error" hx-swap-oob="true" class="text-red-500 text-xs font-bold px-1 block">{error_msg}</div>'
        )

    # 2. Success Logic
    todo = Todo.objects.create(title=title)
    context = {
        "todo": todo,
        "count": Todo.objects.filter(is_deleted=False, is_done=False).count(),
    }

    todo_html = render_to_string("todo/partials/todo.html", context, request=request)
    toast_html = render_to_string(
        "todo/partials/toast.html", {"message": "Task added!"}, request=request
    )

    # IMPORTANT: Include an empty OOB div to CLEAR previous errors on success
    clear_error_html = '<div id="todo-error" hx-swap-oob="true" class="hidden"></div>'

    return HttpResponse(todo_html + toast_html + clear_error_html)


@require_http_methods(["PUT", "POST"])
def update_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)

    if request.method == "POST" and "title" in request.POST:
        new_title = request.POST.get("title", "").strip()

        # Inline Validation for editing
        if not new_title:
            # Instead of a div, let's send a Toast error for inline edits!
            error_toast = render_to_string(
                "todo/partials/toast.html",
                {"message": "⚠️ Title cannot be empty!"},
                request=request,
            )
            return HttpResponse(error_toast)

        todo.title = new_title
    else:
        todo.is_done = not todo.is_done

    todo.save()

    # ... (rest of your existing update_todo logic)
    count = Todo.objects.filter(is_deleted=False, is_done=False).count()
    todo_html = render_to_string(
        "todo/partials/todo.html", {"todo": todo}, request=request
    )
    counter_html = render_to_string(
        "todo/partials/counter.html", {"count": count}, request=request
    )
    return HttpResponse(todo_html + counter_html)


@require_http_methods(["DELETE"])
def delete_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.is_deleted = True
    todo.save()

    count = Todo.objects.filter(is_deleted=False, is_done=False).count()
    counter_html = render_to_string(
        "todo/partials/counter.html", {"count": count}, request=request
    )
    toast_html = render_to_string(
        "todo/partials/toast.html",
        {"message": "Task deleted", "todo_id": todo.pk},
        request=request,
    )

    # Return empty string to remove the row, plus OOB updates for counter and toast
    return HttpResponse("" + counter_html + toast_html)


# todo/views.py


@require_http_methods(["POST"])
def undo_delete(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.is_deleted = False
    todo.save()

    count = Todo.objects.filter(is_deleted=False, is_done=False).count()

    # 1. The restored row (to be added to the list)
    todo_html = render_to_string(
        "todo/partials/todo.html", {"todo": todo}, request=request
    )

    # 2. The counter update
    counter_html = render_to_string(
        "todo/partials/counter.html", {"count": count}, request=request
    )

    # 3. This is the magic: An OOB swap that deletes the "deleted version"
    # of the row from the current view immediately.
    remove_old_row = f'<article id="todo-{pk}" hx-swap-oob="delete"></article>'

    # Combine everything
    return HttpResponse(todo_html + counter_html + remove_old_row)


@require_http_methods(["DELETE"])
def delete_permanent(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.delete()  # Actually removes from DB

    toast_html = render_to_string(
        "todo/partials/toast.html",
        {"message": "Task permanently removed"},
        request=request,
    )
    return HttpResponse("" + toast_html)

@require_http_methods(["POST"])
def empty_trash(request):
    # 1. Purge the records
    deleted_items = Todo.objects.filter(is_deleted=True)
    count = deleted_items.count()
    deleted_items.delete()
    
    # 2. Prepare the response for the "deleted" view
    # This ensures the "No tasks found!" message appears immediately
    context = get_todo_context(filter_type="deleted")
    list_html = render_to_string("todo/partials/list.html", context, request=request)
    
    toast_html = render_to_string(
        "todo/partials/toast.html", 
        {"message": f"Purged {count} items from trash"}, 
        request=request
    )
    
    return HttpResponse(list_html + toast_html)

@require_http_methods(["POST"])
def toggle_all(request):
    # Determine if we are marking all as done or all as active
    active_exists = Todo.objects.filter(is_deleted=False, is_done=False).exists()
    Todo.objects.filter(is_deleted=False).update(is_done=active_exists)

    # Get fresh data
    context = get_todo_context("all")

    # 1. Render the rows for the #todos container
    list_html = render_to_string("todo/partials/list.html", context, request=request)

    # 2. Render the counter (which has hx-swap-oob="true" inside it)
    counter_html = render_to_string(
        "todo/partials/counter.html", {"count": context["count"]}, request=request
    )

    # Return both together
    return HttpResponse(list_html + counter_html)

@require_http_methods(["POST"])
def clear_completed(request):
    completed_todos = Todo.objects.filter(is_done=True, is_deleted=False)

    # Change this: instead of 204, just let it process normally
    # so list.html can render the "No tasks found" message.
    if completed_todos.exists():
        batch_id = f"batch_{int(time.time())}"
        with transaction.atomic():
            completed_todos.update(is_deleted=True, note=batch_id)
    else:
        batch_id = None

    query = request.POST.get("q", "")
    context = get_todo_context("all", query)

    list_html = render_to_string("todo/partials/list.html", context, request=request)
    counter_html = render_to_string(
        "todo/partials/counter.html", {"count": context["count"]}, request=request
    )

    response_html = list_html + counter_html

    if batch_id:
        toast_html = render_to_string(
            "todo/partials/toast.html",
            {"message": "Cleared completed tasks", "undo_batch_id": batch_id},
            request=request,
        )
        response_html += toast_html

    return HttpResponse(response_html)


@require_http_methods(["POST"])
def undo_clear(request, batch_id):
    Todo.objects.filter(note=batch_id).update(is_deleted=False, note="")
    query = request.POST.get("q", "")
    context = get_todo_context("all", query)

    list_html = render_to_string("todo/partials/list.html", context, request=request)
    counter_html = render_to_string(
        "todo/partials/counter.html", {"count": context["count"]}, request=request
    )

    # Optional: You could send back a fresh toast saying "Tasks restored!"
    success_toast = render_to_string(
        "todo/partials/toast.html", {"message": "Tasks restored!"}, request=request
    )

    return HttpResponse(list_html + counter_html + success_toast)

@require_http_methods(["GET"])
def edit_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    return render(request, "todo/partials/todo_edit.html", {"todo": todo})
