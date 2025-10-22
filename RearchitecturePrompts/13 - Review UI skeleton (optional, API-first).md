Goal: Minimal web UI page (FastAPI + Jinja or simple static HTML) to resolve review items.

Add:

- GET /review (HTML): list pending items with link to detail
- GET /review/{id} (HTML): asset tech data, guessed title/ep, fields to assign title/episode
- POST /review/{id}/resolve -> redirects back

Acceptance criteria:

- Page loads and shows pending review items from DB.
- Submitting a resolution calls app service and updates ReviewQueue.status.

Files:

- src/retrovue/api/web/review_pages.py (or templates/)
- static/templates as needed
