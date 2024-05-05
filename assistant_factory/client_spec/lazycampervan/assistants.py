from assistant_factory.client_spec.lazycampervan.instructions import PERSONAL_ASSISTANT
from assistant_factory.config import ClientAssistantConfig

personal_assistant = ClientAssistantConfig(
    client_id="lazycampervan",
    assistant_name="faq-assistant",
    instructions=PERSONAL_ASSISTANT,
    initial_message="Hello! I'm Lazy Camper Van's AI assistant. I can help answer your questions.",
    model="gpt-4-turbo",
    retrieval=True,
    file_paths=["FAQ.pdf"],
)
# sk-proj-nUZNd2W5fcn3fkqOLhFhT3BlbkFJKo6Mtqss8yMmcLsqloVu
