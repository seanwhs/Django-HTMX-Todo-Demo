# 🧠 Django + HTMX Todo App — A Full Architectural Walkthrough

This document explains your application as a **complete system**, not just disconnected files. We'll break it down into three pillars:

**The Data** — Django models (what exists)  
**The Logic** — Django views & URLs (what happens)  
**The Magic** — HTMX + templates (how it feels instant)

## Core Philosophy

This is **not** an API + frontend app.  
**HTML is the API.** Django returns fragments, HTMX swaps them, and the UI stays consistent because **the server is always the source of truth.**

***

## 🧱 1. The Data Layer — `models.py`

Before HTMX, before views, before UX — we define what a Todo **is**.

```python
# todo/models.py
from django.db import models

class Todo(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
   
    title = models.CharField(max_length=255)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_done = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)  # for soft delete
    note = models.CharField(max_length=100, blank=True, db_index=True)  # for bulk undelete
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    class Meta:
        ordering = ['-created_at']
   
    def __str__(self):
        return self.title
```

### Key Design Decisions

**1. Soft Delete (`is_deleted`)**
```
Instead of: todo.delete()  # GONE FOREVER
We do:     todo.is_deleted = True  # Can be restored
```

**Benefits:**
- Trash view (`/filter/deleted/`)
- Undo delete (toast button)
- Batch restore (undo clear completed)
- Safer UX — nothing is lost immediately

**2. Undo Grouping via `note`**
```
Clear Completed → Set note="batch_1234567890" for ALL cleared todos
Undo Clear      → Find all note="batch_1234567890" → Restore
```

**Why brilliant:**
- No extra tables/models
- No client-side state management
- One field handles batch undo perfectly

**3. Priority as `choices`**
```
Stored: "high"    → {{ todo.priority }}
Display: "High"   → {{ todo.get_priority_display }}
```

Django auto-generates the display method. Templates stay clean.

***

## 🧭 2. URL Routing — `core/urls.py`

URLs are your **backend API**, but instead of JSON, they return **HTML fragments**.

```python
# core/urls.py
urlpatterns = [
    # Full page / partials
    path('', views.todos, name='todos'),
    path('filter/<str:filter_type>/', views.todos, name='filter_todos'),
    
    # Single todo actions
    path('add-todo/', views.add_todo, name='add_todo'),
    path('update-todo/<int:pk>/', views.update_todo, name='update_todo'),
    path('delete-todo/<int:pk>/', views.delete_todo, name='delete_todo'),
    
    # Undo system
    path('undo-delete/<int:pk>/', views.undo_delete, name='undo_delete'),
    path('undo-clear/<str:batch_id>/', views.undo_clear, name='undo_clear'),
    
    # Bulk actions
    path('toggle-all/', views.toggle_all, name='toggle_all'),
    path('clear-completed/', views.clear_completed, name='clear_completed'),
    path('empty-trash/', views.empty_trash, name='empty_trash'),
]
```

### Mental Model
```
Each URL = One User Intent
Templates: {% url 'add_todo' %} → /add-todo/
HTMX:     Decides WHERE response goes (hx-target)
Django:   Decides WHAT HTML to return
```

***

## 🧠 3. The Engine — Views & Context

### A. The Source of Truth: `get_todo_context()`

**All** filtering, searching, sorting lives here. No duplication.

```python
def get_todo_context(filter_type="all", query=""):
    # 1. Deleted vs Active todos
    if filter_type == "deleted":
        todos = Todo.objects.filter(is_deleted=True)
    else:
        todos = Todo.objects.filter(is_deleted=False)

    # 2. Search
    if query:
        todos = todos.filter(title__icontains=query)

    # 3. Status filter
    if filter_type == "active":
        todos = todos.filter(is_done=False)
    elif filter_type == "completed":
        todos = todos.filter(is_done=True)

    # 4. Priority-aware sorting (High=3, Medium=2, Low=1)
    todos = todos.annotate(
        priority_order=Case(
            When(priority='high', then=Value(3)),
            When(priority='medium', then=Value(2)),
            When(priority='low', then=Value(1)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('-priority_order', '-created_at')

    return {
        "todos": todos,
        "count": Todo.objects.filter(is_deleted=False, is_done=False).count(),
        "filter_type": filter_type,
        "query": query,
    }
```

**Why this single function prevents chaos:**
- ✅ **Same rules everywhere** (add, toggle, search, filter)
- ✅ **Database sorting** — no Python `sorted()`
- ✅ **Context consistent** across all views
- ✅ **Search preserved** during bulk operations

```
User clicks "Clear Completed" → Still respects search query
User toggles todo → List re-sorts by priority/date
User searches "milk" → Filter buttons still work
```

### B. The Dual-Purpose View: `todos()`

**One URL serves two masters:**

```python
def todos(request, filter_type="all"):
    query = request.GET.get("q", "")
    context = get_todo_context(filter_type, query)
   
    if request.headers.get("HX-Request"):  # HTMX partial
        return HttpResponse(list_html + footer_html)
    return render(request, "todo/todos.html", context)  # Full page
```

```
Browser loads /           → Full HTML page
Filter clicks /filter/all/ → Same URL, fragments only
Search ?q=milk            → Same URL, fragments only
```

**Key insight:** Same logic, different response shape.

***

## ⚡ 4. The Magic — HTMX Patterns

### A. Out-of-Band (OOB) Swaps

**Update multiple page parts from one response:**

```html
<!-- Counter partial -->
<span id="todo-count" hx-swap-oob="true">
    {{ count }} item{{ count|pluralize }} left
</span>

<!-- One response updates: -->
<!-- 1. Main target (#todos list) -->
<!-- 2. OOB: counter -->
<!-- 3. OOB: toast -->
<!-- 4. OOB: footer actions -->
```

```
HTMX finds existing #todo-count → Replaces it
Ignores hx-target completely
Pure magic ✨
```

### B. The Signal Pattern (`HX-Trigger`)

**Views emit events, UI listens:**

```python
# In views (after mutations)
response["HX-Trigger"] = "todoUpdated"
```

```html
<!-- In main template -->
<div id="todos"
     hx-get="{% url 'todos' %}"
     hx-trigger="todoUpdated from:body"
     hx-include="[name='q']">
```

**Flow:**
```
1. User adds todo
2. View: Todo.objects.create() + response["HX-Trigger"] = "todoUpdated"
3. HTMX: Fires "todoUpdated" event on <body>
4. #todos hears it → hx-get /todos/?q= (preserves search)
5. List refreshes → Correct sort order ✨
```

**Result:** Zero client-side state. Server always knows truth.

***

## 🖼️ 5. Templates as Components

### `todos.html` — The Shell
```
Rendered once on load
Everything swaps inside via hx-target
```

**Key features:**
```html
<!-- Debounced search -->
hx-trigger="keyup changed delay:500ms"

<!-- Global CSRF -->
document.body.addEventListener('htmx:configRequest', (e) => {
    e.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
});

<!-- Toast container -->
<div id="toast-container"></div>
```

### `list.html` — The Loop
```html
{% for todo in todos %}
    {% include "todo/partials/todo.html" %}
{% empty %}
    📝 No tasks found!
{% endfor %}
```

### `todo.html` vs `todo_edit.html` — In-Place Editing

```
1. Click ✏️ → hx-get /edit-todo/5/
2. Row ← Form (hx-swap="outerHTML")
3. Edit + Save → hx-post /update-todo/5/
4. Form ← Row (hx-swap="outerHTML")
5. List auto-refreshes (HX-Trigger)

No modals. No JS state. Zero bugs.
```

### `toast.html` — UX Without JavaScript
```html
<div hx-swap-oob="beforeend:#toast-container">
    <div id="toast-{{ now|date:'Uu' }}">  <!-- Unique ID -->
        ✨ Task deleted
        <button hx-post="{% url 'undo_delete' todo_id %}">Undo</button>
    </div>
</div>
```

**Self-contained action system.**

***

## 🔁 6. Action Views — The Behavior Layer

| Action | HTTP | What Server Returns | HTMX Effect |
|--------|------|-------------------|-------------|
| **Add** | POST | Toast + `HX-Trigger` | List refresh |
| **Toggle** | PUT | Row + Counter + `HX-Trigger` | Row swap + refresh |
| **Edit** | GET | Edit form | Row → Form |
| **Delete** | DELETE | Counter + Toast | Row removed |
| **Undo** | POST | Row + OOB delete old | Toast → Row |
| **Clear** | POST | List + Counter + Undo toast | Batch delete |

**Every mutation pattern:**
```python
1. @require_http_methods(["POST", "PUT", "DELETE"])
2. Mutate model(s)
3. render_to_string() fragments
4. HttpResponse(fragments)
5. Optionally: response["HX-Trigger"] = "todoUpdated"
```

***

## 🧠 7. Why This Architecture Scales

```
✅ No frontend state bugs — server = truth
✅ No duplicated filtering logic 
✅ Undo system is trivial (note field)
✅ Sorting authoritative (DB annotate/order_by)
✅ Templates = dumb components
✅ Views = readable functions
✅ Zero JavaScript (except CSRF)
```

## The Mental Model

```
Server = Brain (logic, state, sorting)
HTML   = Contract (what goes where)
HTMX   = Transport (smart swapping)
```
