# Existing Risk Files to Delete/Replace

Before extracting this rebuilt package over the repository, remove the old Risk implementation so obsolete modules do not remain beside the new architecture.

Delete the existing contents of:

```text
backend/apps/risk/
```

Then copy this package's `backend/apps/risk/` into the repository.

Also add/replace:

```text
backend/services/risk_service.py
```

Do NOT delete the existing Weather app or Core app.

After extraction, check these project-level files manually:

```text
backend/<project>/settings.py
backend/<project>/urls.py
```

Add Risk to `INSTALLED_APPS` and mount `backend.apps.risk.urls` under `/api/risk/` if those hooks are not already present.

Do not delete existing migrations belonging to unrelated apps.
