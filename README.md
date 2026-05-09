# fridge-gpt

Personal No Frills checkout capture tool.

This repo contains:

- `extension/`: an unpacked Chrome Manifest V3 extension that scrapes visible checkout/cart item data from `nofrills.ca`.
- `backend/`: a FastAPI app that stores captured checkout snapshots in SQLite.

## Backend

```bash
nix develop path:.
uvicorn app.main:app --reload
```

The Nix dev shell provides Python, FastAPI, Uvicorn, pytest, Node, and these defaults:

```text
FRIDGE_GPT_DATABASE_URL=sqlite:///./fridge_gpt.db
FRIDGE_GPT_TOKEN=dev-token
Authorization: Bearer dev-token
```

Run checks from the dev shell:

```bash
pytest backend/tests
node --check extension/content.js
node --check extension/popup.js
```

Clear saved checkout snapshots:

```bash
python backend/scripts/clear_database.py
```

## Chrome Extension

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Click **Load unpacked**.
4. Select the `extension/` directory.
5. Visit a No Frills checkout/cart page and click the extension button.

The popup defaults to:

- API URL: `http://127.0.0.1:8000`
- Bearer token: `dev-token`

You can change both values from the popup.
