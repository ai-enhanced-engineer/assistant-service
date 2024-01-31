import json
import logging
import os

from nowisthetime import prompts

logger = logging.getLogger(__name__)


def create_assistant(client):
    assistant_file_path = "../assistant.json"

    # Assistant does exist
    if os.path.exists(assistant_file_path):
        try:
            with open(assistant_file_path) as file:
                assistant_data = json.load(file)
                assistant_id = assistant_data["assistant_id"]
            logger.info("Loaded existing assistant ID.")
        except FileNotFoundError:
            logger.warning("Assistant ID file not found. Creating new one...")
    else:
        # Call to create assistant
        assistant = client.beta.assistants.create(
            instructions=prompts.MEDITATION_TEACHER_AGENT, model="gpt-4-1106-preview"
        )

        with open(assistant_file_path, "w") as file:
            json.dump({"assistant_id": assistant.id}, file)
            logger.info("Created a new assistant and saved the ID.")

        assistant_id = assistant.id

    return assistant_id
