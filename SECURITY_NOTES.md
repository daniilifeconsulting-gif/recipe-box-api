# Security baseline – open API

Date: 2026-11-23

- Anonymous requester can GET `/recipes` → returns full list of recipes (200 OK).
- Anonymous requester can GET `/recipes/1` → returns single recipe details (200 OK).
- Anonymous requester can POST `/recipes` → creates a new recipe, which appears in list (201 Created or 200 OK depending on implementation).
- Anonymous requester can PATCH `/recipes/1` → updates title/instructions successfully (200 OK).
- Anonymous requester can DELETE `/recipes/4` → recipe is removed; subsequent GET `/recipes/4` returns 404 Not Found.
- No identity or authorization is required for any of these actions; correct JSON responses do not indicate any access control.
- Endpoint paths are discoverable; hiding or not documenting a route would not protect it without proper authorization checks.
