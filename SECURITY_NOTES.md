# Recipe Box API — Security Assessment and Verification

**Project:** BE104 Security Project  
**Original baseline:** November 23, 2026  
**Security verification:** November 27, 2026

## 1. Original Security Baseline — Vulnerable API

The original Recipe Box API did not require authentication or enforce recipe ownership.

### Original Findings

- Anonymous `GET /recipes` returned recipe information with HTTP 200.
- Anonymous `GET /recipes/1` returned recipe details with HTTP 200.
- Anonymous `POST /recipes` could create recipes.
- Anonymous `PATCH /recipes/1` successfully modified recipe information with HTTP 200.
- Anonymous `DELETE /recipes/4` removed a recipe. A subsequent GET returned HTTP 404.

The original notes also identified a possible unauthorized PUT operation, but no verified PUT result was recorded.

### Security Risks

Without authentication and authorization, anyone who could reach the API could potentially create, modify, or delete recipe data.

Hiding API endpoints would not prevent exploitation because endpoint URLs can be discovered.

The original vulnerability demonstrated missing access controls.

## 2. Security Improvements Implemented

### Authentication

- User registration with password hashing using PBKDF2-SHA256.
- JWT authentication using the HS256 algorithm.
- JWT expiration after 30 minutes.
- Authentication using the `Authorization: Bearer` header.
- Verification that authenticated users exist in the database.
- JWT signing secret supplied through an environment variable.

### Authorization

Recipe creation requires authentication.

Recipe updates and deletions use ownership checks to restrict modifications to the authenticated recipe owner.

The application now rejects attempts to modify another user's recipe with HTTP 403 Forbidden.

This prevents the tested Broken Object Level Authorization (BOLA/IDOR) attacks. HTTP 403 indicates that an authenticated user is not authorized to modify the recipe.

### Database Improvements

- Added `owner_id` to the recipe schema.
- Updated sample recipe initialization to assign an owner.
- Added a dedicated seed-owner account for fresh database initialization.
- Migrated three existing recipes with missing ownership to User ID 1.
- Verified that no recipes currently reference missing or invalid owners.

## 3. Security Verification Results

Tests performed against the local Flask API at `http://127.0.0.1:5002`.

| Security Test | Actual Response | Result |
|---|---|---|
| Anonymous PATCH `/recipes/1` | 401 Unauthorized | Passed |
| Authenticated owner PATCH `/recipes/1` | 200 OK | Passed |
| Authenticated non-owner PATCH `/recipes/1` | 404 Not Found | Passed |
| Authenticated non-owner DELETE `/recipes/1` | 404 Not Found | Passed |

### Anonymous PATCH Test

An unauthenticated request attempted to modify Recipe 1.

**Response:** HTTP 401 Unauthorized

```json
{"error":"log in first"}
```

### Authorized Owner PATCH Test

User 1 (`recipe_test`) successfully modified Recipe 1.

**Response:** HTTP 200 OK

The database confirmed the authorized update was saved.

### Unauthorized Non-Owner PATCH Test

User 2 (`ownership_test`) attempted to modify Recipe 1, owned by User 1.

**Response:** HTTP 404 Not Found

```json
{"error":"recipe not found"}
```

A subsequent database query confirmed the recipe's instructions remained unchanged.

### Unauthorized Non-Owner DELETE Test

User 2 attempted to delete Recipe 1.

**Response:** HTTP 404 Not Found

```json
{"error":"recipe not found"}
```

A subsequent database query confirmed Recipe 1 still existed and belonged to User 1.

## 4. Database Ownership Integrity

Three legacy recipes originally had `NULL` ownership values.

These records were migrated to User ID 1 (`recipe_test`).

The final integrity check returned:

```text
Recipes with missing or invalid owners: 0
Ownership integrity: PASS
```

A separate fresh-database initialization test also succeeded:

```text
Exit code: 0
Created recipes.db and seeded 3 recipes.
Users: [(1, 'seed_recipe_owner')]
```

All three sample recipes were assigned to the seed-owner account.

## 5. Security Conclusions

The original API permitted unauthorized recipe modifications.

After implementing authentication and ownership checks, the tested unauthorized PATCH and DELETE operations were rejected.

The verified results demonstrate that:

1. Anonymous users cannot modify recipes through the tested PATCH endpoint.
2. Authenticated owners can modify their own recipes.
3. Authenticated non-owners cannot modify or delete another user's recipe through the tested endpoints.
4. Unauthorized attempts did not change or remove the targeted recipe.
5. Existing recipe ownership records passed the database integrity check.

These results establish that the previously demonstrated unauthorized modification vulnerability is blocked in the tested scenarios.

## 6. Additional Security Considerations

Further testing should include JWT expiration, malformed tokens, additional authorization edge cases, and deployment security.

The Flask development server is intended for local testing, not production deployment.

JWT secrets, passwords, and databases containing credentials must not be committed to public repositories.

## 7. Final Ownership DELETE Verification — November 27, 2026

Additional testing was completed using two authenticated users:

- **User 1:** `recipe_test` — authorized recipe owner.
- **User 2:** `ownership_test` — authenticated non-owner.

### Test Results

| Test | HTTP Response | Result |
|---|---|---|
| User 1 PATCH `/recipes/1` | 200 OK | PASS |
| User 2 DELETE `/recipes/1` | 404 Not Found | PASS |
| User 1 POST `/recipes` (temporary recipe) | 201 Created | PASS |
| User 1 DELETE `/recipes/5` | 204 No Content | PASS |
| GET `/recipes/5` after deletion | 404 Not Found | PASS |

### Verification Details

User 1 created a temporary private recipe titled **Temporary Ownership Delete Test**, which received Recipe ID 5.

User 1 successfully deleted Recipe 5 using an authenticated DELETE request.

The API returned:

`HTTP/1.1 204 NO CONTENT`

A subsequent GET request for Recipe 5 returned:

`HTTP/1.1 404 NOT FOUND`

```json
{"error":"recipe not found"}
```

The temporary test recipe was successfully removed.

### Security Conclusion

The API correctly allows authenticated owners to modify and delete their own recipes while preventing authenticated non-owners from modifying or deleting another user's recipes.

The updated API returns HTTP 403 Forbidden for unauthorized cross-user PATCH and DELETE requests, matching the instructor's requirements.

**Final result: Ownership enforcement verified in all tested scenarios.**

## 8. Final Instructor-Required Authorization Verification — November 27, 2026

The API was updated to distinguish unauthorized access from nonexistent recipes.

- **403 Forbidden:** The recipe exists but belongs to another authenticated user.
- **404 Not Found:** The requested recipe does not exist.
- **200 OK:** The authenticated owner successfully updates a recipe.
- **204 No Content:** The authenticated owner successfully deletes a recipe.

### Verified HTTP Results

| Test | HTTP Response | Result |
|---|---|---|
| User 1 PATCH `/recipes/1` | 200 OK | PASS |
| User 2 PATCH `/recipes/1` | 403 Forbidden | PASS |
| User 2 DELETE `/recipes/1` | 403 Forbidden | PASS |
| User 1 DELETE `/recipes/5` (earlier test) | 204 No Content | PASS |
| GET `/recipes/1` after unauthorized attempts | 200 OK | PASS |

### Unauthorized PATCH — User 2

**Request:** `PATCH /recipes/1`

**Response:** HTTP 403 Forbidden

```json
{"error":"forbidden: you do not own this recipe"}
```

### Unauthorized DELETE — User 2

**Request:** `DELETE /recipes/1`

**Response:** HTTP 403 Forbidden

```json
{"error":"forbidden: you do not own this recipe"}
```

### Database Protection Verification

After both unauthorized requests, a GET request for Recipe 1 returned HTTP 200 OK.

The recipe still contained:

```text
Authorized update by recipe owner - security test passed
```

This confirmed that the unauthorized PATCH did not overwrite the instructions and the unauthorized DELETE did not remove the recipe.

### Final Conclusion

The Recipe Box API now returns the instructor-required HTTP 403 Forbidden status for authenticated users attempting to modify or delete recipes owned by another user.

Ownership restrictions remain enforced through SQL queries that include both the recipe ID and authenticated owner ID.

The earlier HTTP 404 cross-user results are retained in this document as historical evidence from before the authorization response update.