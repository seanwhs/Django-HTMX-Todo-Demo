# Django + HTMX Todo App

This project is a modern, reactive Todo application built to demonstrate the powerful synergy between **Django** and **HTMX**. It moves away from the complexity of heavy JavaScript frameworks, opting for server-side logic that delivers a seamless single-page application (SPA) experience.

---

## 🚀 What is HTMX?

**HTMX** is a lightweight library that gives you access to modern browser features (AJAX, CSS Transitions, WebSockets) directly in your HTML using simple attributes.

In traditional HTML, only `<a>` and `<form>` can make HTTP requests, and only `click` and `submit` events can trigger them. HTMX breaks these constraints: **any element** can trigger a request from **any event**, and the response can be swapped into **any part** of the page.

---

## ⚛️ Why I moved from React to HTMX

As a former React developer, the transition to HTMX represents a shift toward "The How" of the original web:

* **Unified Language:** Instead of maintaining a Python backend and a JavaScript/TypeScript frontend, the logic stays entirely within Django.
* **No More State Synchronization:** In React, you often struggle to keep the frontend state in sync with the database. With HTMX, the **Server is the Source of Truth**. When data changes, the server simply sends the updated HTML.
* **Goodbye Build Tools:** I no longer need `npm`, `webpack`, or `Vite` for basic interactivity. There is no "hydration" or complex client-side routing.
* **Locality of Behavior (LoB):** I can look at a single HTML element and see exactly what it does, where it sends data, and what it updates—no more jumping between five files to trace a single click handler.

---

## 🛠 How it Works in Django

1. **The Script:** A single `<script>` tag in the header.
2. **The Header Check:** Django views check `request.headers.get('HX-Request')`.
3. **The Fragment:** If it's an HTMX request, Django returns a small HTML partial (like `todo.html`) instead of the full `base.html` shell.

---

## ✨ Application Features

### 1. AJAX CRUD Operations

* **Add:** Prepend tasks to the list without a refresh (`hx-swap="afterbegin"`).
* **Update:** Toggles "done" status and swaps the individual item's HTML.
* **Delete:** Removes items with a smooth 300ms CSS fade-out transition.

### 2. Out-of-Band (OOB) Swaps

Using `hx-swap-oob="true"`, the server can update multiple parts of the page in one request. For example, when you delete a task, the server sends the instruction to remove the item *and* an updated "Items Left" counter for the footer.

### 3. Smart Filtering

The app supports **All**, **Active**, and **Completed** views. HTMX fetches the filtered list and swaps the container dynamically, keeping the UI fast and responsive.

### 4. Bulk Actions

* **Toggle All:** Instantly mark every task as complete or incomplete.
* **Clear Completed:** Purge finished tasks with one click, utilizing `hx-confirm` for a native browser safety check.

### 5. Seamless CSRF Integration

The app handles Django’s security by attaching the CSRF token to every HTMX request header:

```javascript
document.body.addEventListener('htmx:configRequest', (e) => {
    e.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
});

```

---

## 📂 Project Structure

* `todos.html`: The main application shell.
* `partials/list.html`: The container loop for tasks.
* `partials/todo.html`: The interactive task component.
* `partials/counter.html`: The OOB-ready count indicator.

---

## 🔮 What's Next?

To expand this project, consider:

1. **Inline Editing:** Swap a title for an `<input>` on double-click.
2. **Search:** Add a search bar with `hx-trigger="keyup changed delay:500ms"`.
3. **Validation:** Show server-side validation errors without reloading.

---

## 📄 License

This project is licensed under the **MIT License**.

