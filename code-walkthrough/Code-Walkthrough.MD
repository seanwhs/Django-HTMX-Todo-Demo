# 📝 Django + HTMX Reactive Todo App — Complete Code Walkthrough

This project is a **reactive task management system** built with Django, HTMX, and Tailwind CSS. I hope to integrate Alpine.js in future. This demonstrates the **DHA Stack** approach: server-driven HTML, micro-interactivity, and zero JavaScript build tools.

> Goal: Achieve SPA-like interactivity while keeping **all business logic in Django**. HTMX handles DOM swaps, Alpine.js handles small local UI behaviors, and Tailwind provides utility-based styling.

---

## 1️⃣ Why HTMX over React

The key idea is **Locality of Behavior (LoB)**:

| Pain in React                                                        | DHA / HTMX Solution                                       |
| -------------------------------------------------------------------- | --------------------------------------------------------- |
| Maintaining client-state sync with backend (Redux/Zustand headaches) | Server is source-of-truth; HTMX updates HTML fragments    |
| Two-language problem (TypeScript frontend + Python backend)          | All logic in Django                                       |
| Node build and hydration overhead                                    | HTMX + Alpine via CDN, instant interactivity              |
| Debugging complex component chains                                   | HTML is self-documenting (`<button hx-delete="/todo/5">`) |

**Takeaway:** HTMX gives the benefits of SPA interactivity without the complexity of frontend state management.

---

## 2️⃣ DHA Stack Roles


| Technology       | Role      | Purpose                                                     |
| ---------------- | --------- | ----------------------------------------------------------- |
| **Django**       | Brain     | Business logic & data management                            |
| **HTMX**         | Engine    | AJAX requests & partial DOM updates                         |
| **Alpine.js**    | Sprinkles | Micro-interactivity: modals, transitions, local UI behavior |
| **Tailwind CSS** | Skin      | Utility-first styling, fast iterations                      |

> Feature velocity: a single developer can implement database, view, and UI.

---

## 3️⃣ Project Structure Overview

```
django-htmx-todo/
├── todo/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── templates/
│   │   └── todo/
│   │       ├── todos.html         # Main page
│   │       ├── partials/
│   │       │   ├── list.html      # Task list loop
│   │       │   ├── todo.html      # Single task row
│   │       │   ├── todo_edit.html # Edit form for task
│   │       │   ├── toast.html     # Undo notifications
│   │       │   └── counter.html   # Items left counter
├── manage.py
└── requirements.txt
```

---

## 4️⃣ Core Model (`models.py`)

```python
from django.db import models
import uuid

class Todo(models.Model):
    PRIORITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]

    title = models.CharField(max_length=200)
    is_done = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    batch_id = models.UUIDField(null=True, blank=True)  # for bulk undo
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
```

**Notes:**

* `is_deleted` allows **soft deletes**.
* `batch_id` groups tasks for bulk undo.
* `priority` demonstrates custom choice fields.

---

## 5️⃣ Views (`views.py`)

HTMX workflows require **partial HTML responses**, not JSON.

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Todo
from django.views.decorators.http import require_POST
import uuid

def todos(request):
    """Main todo view with filter and search."""
    filter_type = request.GET.get('filter', 'all')
    query = request.GET.get('q', '')

    todos = Todo.objects.filter(is_deleted=False)
    if filter_type == 'active':
        todos = todos.filter(is_done=False)
    elif filter_type == 'completed':
        todos = todos.filter(is_done=True)

    if query:
        todos = todos.filter(title__icontains=query)

    context = {'todos': todos}

    if request.headers.get('HX-Request'):  # HTMX request
        return render(request, 'todo/partials/list.html', context)
    return render(request, 'todo/todos.html', context)

@require_POST
def add_todo(request):
    title = request.POST.get('title')
    todo = Todo.objects.create(title=title)
    context = {'todo': todo}
    return render(request, 'todo/partials/todo.html', context)
```

**Key Patterns:**

* `HX-Request` detection → return HTML fragments for partial swaps.
* Server sends the exact DOM element needed → no JSON parsing.
* Soft deletes and undo are handled using **OOB swaps and batch IDs**.

---

## 6️⃣ Partial Templates Walkthrough

### 6.1 `todo.html` — Single Task Row

```html
<li id="todo-{{ todo.id }}" class="flex items-center justify-between">
    <input type="checkbox" hx-post="/todo/{{ todo.id }}/toggle" hx-target="#todo-{{ todo.id }}" hx-swap="outerHTML" {% if todo.is_done %}checked{% endif %}>
    <span class="{% if todo.is_done %}line-through{% endif %}">{{ todo.title }}</span>
    <button hx-delete="/todo/{{ todo.id }}" hx-target="#todo-{{ todo.id }}" hx-swap="outerHTML">Delete</button>
</li>
```

**HTMX Attributes Explained:**

| Attribute   | Meaning                                                          |
| ----------- | ---------------------------------------------------------------- |
| `hx-post`   | Makes a POST request to toggle task completion                   |
| `hx-delete` | Sends DELETE request on button click                             |
| `hx-target` | Replaces the targeted element (task row)                         |
| `hx-swap`   | How the HTML is swapped (`outerHTML` replaces the entire `<li>`) |

---

### 6.2 `list.html` — Task List Loop

```html
<ul id="todo-list">
    {% for todo in todos %}
        {% include "todo/partials/todo.html" %}
    {% empty %}
        <li>No tasks found!</li>
    {% endfor %}
</ul>
```

* Supports **dynamic refresh** via HTMX.
* Only the updated portion of the page is re-rendered.

---

### 6.3 `toast.html` — Undo Notifications

```html
<div hx-swap-oob="true" class="toast">
    <span>Task deleted</span>
    <button hx-post="/undo/{{ batch_id }}">Undo</button>
</div>
```

* `hx-swap-oob="true"` → updates an element outside the current target.
* Multiple parts of the page (task list + counter + toast) can be updated in one response.

---

### 6.4 `counter.html` — Items Left

```html
<span hx-swap-oob="true" id="items-left">{{ todos|length }} items left</span>
```

* Server updates the counter automatically whenever tasks are modified.
* Alpine.js can optionally animate the counter change.

---

## 7️⃣ Advanced Features

| Feature              | How it works                                                                |
| -------------------- | --------------------------------------------------------------------------- |
| **Debounced Search** | `hx-trigger="keyup changed delay:500ms"` → waits 500ms before sending query |
| **Bulk Undo**        | Assign `batch_id` on deletion, allow undo for all tasks in that batch       |
| **Soft Delete**      | `is_deleted=True` instead of DB deletion, with optional restore             |
| **Transitions**      | Alpine.js `x-transition` fades tasks in/out                                 |

---

## 8️⃣ Frontend Setup

No build tools required. All dependencies via CDN in `todos.html`:

```html
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
<script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

**Example: Debounced Search Bar**

```html
<input type="text" placeholder="Search" 
       hx-get="/todos" 
       hx-trigger="keyup changed delay:500ms" 
       hx-target="#todo-list" 
       hx-swap="innerHTML">
```

**Workflow:**

1. User types in search field.
2. After 500ms pause, HTMX sends GET request to `/todos?q=...`.
3. Server returns filtered `list.html`.
4. Only `#todo-list` content is replaced.

---

## 9️⃣ How HTMX Works

| Concept                            | Explanation                                                     |
| ---------------------------------- | --------------------------------------------------------------- |
| `hx-get` / `hx-post` / `hx-delete` | HTTP request method to URL                                      |
| `hx-target`                        | Element selector where response HTML is inserted                |
| `hx-swap`                          | Swap strategy (`innerHTML`, `outerHTML`, `beforeend`)           |
| `hx-swap-oob`                      | Out-of-band swaps to update multiple areas                      |
| `HX-Trigger`                       | Server can trigger client events (used for sorting / re-render) |

---

## 10️⃣ Installation & Run

```bash
git clone <repo-url>
cd django-htmx-todo
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

*Visit `http://127.0.0.1:8000/` to see a fully reactive todo app.*

---

## ✅ Summary

This project shows **how to build an SPA-like experience without SPA frameworks**:

* Server-driven HTML keeps logic centralized.
* HTMX enables granular partial updates and OOB swaps.
* Alpine.js (future add-on) handles micro-interactions.
* Tailwind CSS accelerates styling and iteration.

> **Learning Outcome:** I can now build reactive Django applications with **minimal JavaScript**, fully leveraging HTMX for modern interactivity.

