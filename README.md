# Assistant Service

This repository contains the code for the assistant service.

## Configuration
Set the following environment variables before running the application:

- `OPENAI_API_KEY` - your OpenAI API key
- `PROJECT_ID` - Google Cloud project ID
- `BUCKET_ID` - Cloud Storage bucket storing configs
- `CLIENT_ID` - identifier for the assistant configuration
- `ASSISTANT_ID` - ID of the assistant to run

### Running locally
After exporting the variables above, start the Chainlit app with:

```bash
make local-run
```

This launches Chainlit on `http://localhost:8000` using the provided configuration.

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
