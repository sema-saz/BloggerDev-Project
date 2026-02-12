# BloggerDev - AI Agent Instructions

## Project Overview
BloggerDev is a Turkish-language blog platform with two main components:
- **BloggerDevWeb/** - Flask-based public-facing blog (read-only for visitors)
- **BloggerDev-AdminPaneli/** - Tkinter desktop admin panel for content management (CRUD operations)

Both applications connect to a SQL Server database (`BloggerDev`) using Windows Authentication via `pyodbc`.

## Architecture & Data Flow

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Admin Panel        │────▶│  SQL Server      │◀────│  Flask Web App  │
│  (Tkinter/MAIN.py)  │     │  (BloggerDev DB) │     │  (app.py)       │
│  - Create/Edit/Del  │     │  - ODBC Driver 17│     │  - Read-only    │
└─────────────────────┘     └──────────────────┘     └─────────────────┘
```

## Database Schema (Key Tables)
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `dbo.Post` | Blog posts | `post_id`, `post_title`, `post_content`, `users_id`, `categories_id` |
| `dbo.Users` | Authors | `users_id`, `users_name`, `users_email`, `role_id` |
| `dbo.Categories` | Post categories | `categories_id`, `categories_name` |
| `dbo.Tags` | Post tags | `tags_id`, `tag_name` |
| `dbo.Post_Tags` | Many-to-many junction | `post_id`, `tags_id` |
| `dbo.Comments` | User comments | `comment_id`, `post_id`, `users_id`, `comment_content` |

## Database Connection Pattern
Both apps use the same connection approach - always use `dbo.` schema prefix:
```python
# Connection string pattern (Windows Auth)
pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=SORA\\SQLEXPRESS;'
    'DATABASE=BloggerDev;'
    'Trusted_Connection=yes;'
)
```

## Flask Web App Conventions ([BloggerDevWeb/app.py](BloggerDevWeb/app.py))
- **Route pattern**: Create connection per request with `get_db()`, close before returning
- **Template variables**: Always pass `categories` for sidebar rendering
- **URL structure**: `/post/<int:post_id>`, `/category/<int:category_id>`, `/author/<int:author_id>`, `/tag/<int:tag_id>`
- **Templates**: Extend `base.html`, use Bootstrap 5 + Bootstrap Icons
- **Error handling**: Return tuple `("message", 404)` for not found items

## Tkinter Admin Panel Conventions ([BloggerDev-AdminPaneli/MAIN.py](BloggerDev-AdminPaneli/MAIN.py))
- **Window pattern**: Use `tk.Toplevel()` for secondary windows
- **CRUD operations**: Each entity has `open_*_window()` function with embedded load/add/edit/delete functions
- **UI framework**: Plain tkinter + ttk, color scheme uses `#2ecc71` (green), `#3498db` (blue), `#f0f0f0` (bg)
- **Data display**: Use `ttk.Treeview` with scrollbars for lists
- **Confirmation**: Always use `messagebox.askyesno()` before delete operations

## Running the Applications
```bash
# Flask web app (port 5000)
cd BloggerDevWeb
pip install -r requirements.txt
python app.py

# Tkinter admin panel
cd BloggerDev-AdminPaneli
python MAIN.py
```

## SQL Query Patterns
- Always use parameterized queries with `?` placeholders
- Use `LEFT JOIN` for optional relationships (author, category)
- Order posts by `post_date DESC` for recency
- Truncate long text in UI: `title[:50] + "..."` pattern

## Key Files
- [BloggerDevWeb/templates/base.html](BloggerDevWeb/templates/base.html) - Master template with navbar/sidebar
- [BloggerDev-AdminPaneli/BloggerDev.sql](BloggerDev-AdminPaneli/BloggerDev.sql) - Full database schema
- [BloggerDevWeb/requirements.txt](BloggerDevWeb/requirements.txt) - Flask dependencies
