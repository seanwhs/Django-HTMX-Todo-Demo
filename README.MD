# Django + HTMX Reactive Todo App

I developed this reactive task management system using Django-HTMX-TailwindCSS to learn the  **DHA Stack** (Django, HTMX, Alpine.js). It serves as a blueprint for me to build web applications that deliver a seamless Single-Page Application (SPA) feel while keeping the business logic firmly on the server. By leveraging these tools, I’ve entirely bypassed the complexity of modern JavaScript build chains.

---

## ⚛️ Why I Moved from React to HTMX

The shift from React to HTMX was a conscious move toward **Locality of Behavior (LoB)** and architectural simplicity.

* **Eliminating the "State Sync" Nightmare:** In React, 50% of development time is spent keeping client-side state (Redux/Zustand) in sync with the database. With HTMX, the **Server is the Source of Truth**. The server sends HTML fragments; there is no JSON to parse and no fragile client state to reconcile.
* **Unified Language:** I eliminated the "Split Brain" problem. Instead of managing a Python backend and a TypeScript frontend with a complex API contract between them, all logic lives in one place: **Django**.
* **Zero Build Overhead:** I deleted `npm`, `webpack`, and `Vite`. There is no "hydration" delay or complex client-side routing. The application is interactive the second the HTML hits the browser.
* **Transparent Code:** I can read one line of HTML and understand its full network intent.
> *Example:* `<button hx-delete="/todo/5">` is self-documenting. In React, this same action requires tracing through components, event handlers, API utilities, and reducers.



---

## 🏗 The Power of DHA (Django, HTMX, Alpine.js)

When manpower is scarce, the **Django-React** approach is a liability. It requires two sets of expertise, two deployments, and double the maintenance. **DHA** is the "Indie Hacker" superpower:

| Technology | Role | What it solves |
| --- | --- | --- |
| **HTMX** | **The Engine** | Solves the "Full Page Refresh" problem of traditional MPAs. It allows any HTML element to make AJAX requests and swap parts of the page with server-rendered HTML. |
| **Alpine.js** | **The Polish** | Solves the "Heavy JS" problem. It handles client-side UI logic (dropdowns, modals, transitions) using a declarative syntax directly in your HTML, requiring zero compilation. |
| **Tailwind CSS** | **The Skin** | Solves the "Context Switching" problem. Instead of writing custom CSS files, you style elements using utility classes directly in the markup, leading to faster design iterations. |

**Feature Velocity:** A single developer can build an entire feature (Database  View  UI) in a very short time.

---

## ✨ Full Feature Breakdown

### 1. Macro-Interactivity (HTMX)

HTMX transforms this from a standard Multi-Page Application (MPA) into a reactive experience by utilizing multiple endpoints that return HTML fragments rather than whole pages.

* **Smart CRUD:** Tasks are added, toggled, and edited via AJAX. Only the specific modified DOM elements are swapped.
* **Out-of-Band (OOB) Swaps:** Using `hx-swap-oob="true"`, the server can update multiple disparate parts of the page (e.g., the task list *and* the footer counter) in a single HTTP response.
* **The Signal Pattern:** After an update, the server sends an `HX-Trigger: todoUpdated` header. The frontend listens for this to refresh the list, ensuring complex **Database-level sorting** (e.g., ) is always respected.

### 2. Advanced Logic & Safety

* **Soft Deletes & Undo:** Instead of permanent deletion, tasks are flagged as `is_deleted`. A "Toast" notification appears with an "Undo" button, allowing users to restore tasks within a 5-second window.
* **Bulk Undo (Batch IDs):** When "Clear Completed" is triggered, tasks are assigned a unique `batch_id`. This allows a single undo action to restore an entire group of tasks simultaneously.
* **Debounced Search:** The search bar uses `hx-trigger="keyup changed delay:500ms"`, waiting for the user to stop typing before querying the server.

### 3. Micro-Interactivity (Alpine.js)

Alpine handles the "feel" of the app for things that don't require server logic:

* **Dynamic Modals:** Creating confirmation dialogs (like "Are you sure you want to delete?") instantly without hitting the network.
* **Transitions:** Using `x-transition` to smoothly fade out deleted items or slide in new ones, giving the app a premium feel.

---

## 🛠 Zero-Config Installation & Setup

This project requires no Node.js. You can edit the frontend immediately without a watcher.

### 1. Requirements

* Python 3.10+
* Django 5.0+

### 2. Quick Start

```bash
# Clone the repository
git clone <your-repo-url>
cd django-htmx-todo

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Django
pip install django

# Run migrations and start server
python manage.py migrate
python manage.py runserver

```

### 3. The "No-Build" Frontend

The application pulls dependencies via CDN in `todos.html`:

```html
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
<script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>

```

---

## 📂 Project Structure

* **`models.py`**: Contains the `Todo` model with priority choices, soft-delete fields, and `note` fields for batch IDs.
* **`views.py`**: The heart of the app. Views detect `HX-Request` and return specialized HTML partials instead of full pages.
* **`partials/`**:
* `list.html`: The main loop rendering todos.
* `todo.html`: The individual task row with HTMX triggers.
* `todo_edit.html`: The in-place form for updating tasks.
* `toast.html`: The notification system using OOB swaps for Undo.
* `counter.html`: A tiny fragment that keeps the "Items Left" count in sync.



