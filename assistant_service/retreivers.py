import logging

from google.cloud import secretmanager

logger = logging.getLogger(__name__)

PROJECT_ID = "botbrewers"


class BotBrewersSecretRetriever:
    def __init__(self, client_id: str):
        self.client = secretmanager.SecretManagerServiceClient()
        self.client_id = client_id

    def access_secret(self, suffix: str, secret_version_path: str = "latest"):
        secret_id = self.client_id + suffix
        path = self.client.secret_version_path(PROJECT_ID, secret_id, secret_version_path)
        response = self.client.access_secret_version(name=path)
        logger.info(f"Retrieved secret at: {path}")
        secret = response.payload.data.decode("UTF-8")

        return secret
