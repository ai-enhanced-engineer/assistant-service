# Assistant Service

This repository contains the code for the assistant service.

## Development setup
1. Create the virtual environment and install dependencies:
   ```bash
   make environment-create
   ```
2. Run the tests:
   ```bash
   make test
   ```
3. Format and lint the code:
   ```bash
   make format
   make lint
   ```

Refer to `AGENTS.md` for automated contributor guidelines.

## FastAPI backend

The API lives in `assistant_engine/api.py` and exposes two endpoints:

* `GET /start` – create a new chat thread and return its ID
* `POST /chat` – send a message to the thread and receive the echoed response

Run the server during development with:

```bash
uvicorn assistant_engine.api:app --reload
```

## Custom React UI

The `frontend` folder contains a simple React/Vite app that talks to the FastAPI
server. The UI fetches a new thread ID on load and posts messages to `/chat`.

Useful Make targets:

```bash
make frontend-install  # install Node dependencies
make frontend-test     # run Vitest unit tests
make ui-run            # build the UI and serve with Chainlit
```

The compiled build is served by Chainlit via `.chainlit/config.toml` which sets
`custom_build = "./frontend/dist"`.
