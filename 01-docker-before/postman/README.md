# Postman: collection, environment and automated tests

Collection of the API requests, with automated assertions (including bad credentials `401`, validation `400`, missing token `401` and PDF export `406`).

| File | What it is |
|---|---|
| `erudio.postman_collection.json` | 52 requests (Auth, person, book, file, e-Mail), each with `pm.test` assertions |
| `FASTAPI_PYTHON_ERUDIO.postman_environment.json` | Variables used by the collection (`baseUrl` = `http://localhost:8000`) |
| `files/` | Sample files used by the uploads (`sample.txt`, `people.csv`, `people.xlsx`) |

## Running

```bash
# with the API already running on localhost:8000
npx --yes newman@6.2.2 run postman/erudio.postman_collection.json \
  -e postman/FASTAPI_PYTHON_ERUDIO.postman_environment.json \
  --working-dir postman
```

A collection-level script signs in when there is no valid token, so the order of the requests does not matter. `sendEmails=true` turns on the two tests that really send an e-mail (they need `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `MAIL_HOST` and `MAIL_PORT` on the API); by default they are skipped.
