# todo/views.py
import time
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db import transaction
from .models import Todo


def get_todo_context(filter_type="all", query=""):
    todos = Todo.objects.filter(is_deleted=False)

    # Apply search filter if query exists
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
    query = request.GET.get("q", "")  # Get the search parameter
    context = get_todo_context(filter_type, query)
    template = (
        "todo/partials/list.html"
        if request.headers.get("HX-Request")
        else "todo/todos.html"
    )
    return render(request, template, context)


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


@require_http_methods(["POST"])
def undo_delete(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.is_deleted = False
    todo.save()

    context = {
        "todo": todo,
        "count": Todo.objects.filter(is_deleted=False, is_done=False).count(),
        "update_count": True,
    }
    todo_html = render_to_string("todo/partials/todo.html", context, request=request)

    response = HttpResponse(todo_html)
    response["HX-Retarget"] = "#todos"
    response["HX-Reswap"] = "afterbegin"
    return response


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
    counter_html = render_to_string("todo/partials/counter.html", {"count": context["count"]}, request=request)
    
    response_html = list_html + counter_html
    
    if batch_id:
        toast_html = render_to_string("todo/partials/toast.html", 
            {"message": "Cleared completed tasks", "undo_batch_id": batch_id}, request=request)
        response_html += toast_html

    return HttpResponse(response_html)

@require_http_methods(["POST"])
def undo_clear(request, batch_id):
    # 1. Restore the items belonging to this batch
    Todo.objects.filter(note=batch_id).update(is_deleted=False, note="")
    
    # 2. Extract the search query sent via hx-include
    query = request.POST.get("q", "")
    
    # 3. Get context (we default to 'all' to show the restored items)
    context = get_todo_context("all", query)
    
    # 4. Render and return the partials
    list_html = render_to_string("todo/partials/list.html", context, request=request)
    counter_html = render_to_string("todo/partials/counter.html", {"count": context["count"]}, request=request)
    
    return HttpResponse(list_html + counter_html)


@require_http_methods(["GET"])
def edit_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    return render(request, "todo/partials/todo_edit.html", {"todo": todo})
