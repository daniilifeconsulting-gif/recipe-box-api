
# Security Baseline – Open API

Date: 2026-11-23

## Findings

- Anonymous requester can GET `/recipes` → returns full list of recipes (200 OK).
- Anonymous requester can GET `/recipes/1` → returns single recipe details (200 OK).
- Anonymous requester can POST `/recipes` → creates a new recipe (confirm status code).
- Anonymous requester can PUT `/recipes/1` → updates a recipe (verify result).
- Anonymous requester can DELETE `/recipes/1` → deletes a recipe (verify result).

## Security Risks

The API currently allows requests without verifying the user's identity or permissions.

Hiding an endpoint does not make it secure because attackers can still discover the URL.

## Security Improvements Needed

1. Add authentication to identify users.
2. Add authorization to control who can create, edit, or delete recipes.
3. Protect sensitive API endpoints.
4. Test unauthorized requests to confirm they are rejected.

