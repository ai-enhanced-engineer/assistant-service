# Enable Services for the Project: We have to enable services for Cloud Run using below set of commands
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# Create Service Accounts with Permissions: In order to deploy the app, let us create a service account and assign the
# permissions required to deploy the app using Google Cloud Run.

gcloud iam service-accounts create assistant-service-app \
    --display-name="assistant-service-app"

gcloud projects add-iam-policy-binding botbrewers \
    --member="serviceAccount:assistant-service-app@botbrewers.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding botbrewers \
    --member="serviceAccount:assistant-service-app@botbrewers.iam.gserviceaccount.com" \
    --role="roles/serviceusage.serviceUsageConsumer"

gcloud projects add-iam-policy-binding botbrewers \
    --member="serviceAccount:assistant-service-app@botbrewers.iam.gserviceaccount.com" \
    --role="roles/run.admin"

# Build docker
#DOCKER_BUILDKIT=1 docker build --target=runtime . -t northamerica-northeast1-docker.pkg.dev/botbrewers/assistant-service/assistant-service-app:latest

DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 -t northamerica-northeast1-docker.pkg.dev/botbrewers/assistant-service/assistant-service-app:latest .

# Create a repository clapp
gcloud artifacts repositories create assistant-service \
    --repository-format=docker \
    --location=northamerica-northeast1 \
    --description="Assistant service" \
    --async

# Assign authentication
gcloud auth configure-docker northamerica-northeast1-docker.pkg.dev

# Push the Container to Repository
docker push northamerica-northeast1-docker.pkg.dev/botbrewers/assistant-service/assistant-service-app:latest

# DEPLOY
gcloud run deploy assistant-service-app --image=northamerica-northeast1-docker.pkg.dev/botbrewers/assistant-service/assistant-service-app:latest \
    --set-env-vars=OPENAI_API_KEY=,ASSISTANT_ID= \
    --region=northamerica-northeast1 \
    --service-account=assistant-service-app@botbrewers.iam.gserviceaccount.com \
    --port=8000