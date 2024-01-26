import os
import json
import prompts

def create_assistant(client):
  assistant_file_path = 'assistant.json'

  # Assistant does exists
  if os.path.exists(assistant_file_path):  
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
      print("Loaded existing assistant ID.")
  else:
    # Call to create assistant
    assistant = client.beta.assistants.create(
      instructions=prompts.MEDITATION_TEACHER_AGENT,
      model="gpt-4-1106-preview"
    )

    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

    assistant_id = assistant.id

  return assistant_id
