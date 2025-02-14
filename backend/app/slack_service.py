import time
import json
import traceback
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from openai import OpenAI

from app.config import settings
from app.database import SessionLocal, Task, ProcessedMessage  # Import your DB session + model

from app.prompt_template_profile import generate_prompt, generate_prompt_no_prpfile, USER_PROFILE


SLACK_TOKEN = settings.SLACK_TOKEN
CHANNEL_ID = settings.CHANNEL_ID
API_KEY = settings.OPEN_AI_API_KEY

# Slack + OpenAI clients
slack_client = WebClient(token=SLACK_TOKEN)
openai_client = OpenAI(api_key=API_KEY)

def monitor_slack_channel():
    """
    Continuously polls the Slack channel for new messages.
    Avoids processing duplicate messages using their 'ts' (timestamp).
    """
    last_timestamp = "0"
    while True:
        try:
            response = slack_client.conversations_history(
                channel=CHANNEL_ID,
                oldest=last_timestamp
            )
            messages = response.get("messages", [])
            for message in reversed(messages):
                last_timestamp = message["ts"]
                text = message.get("text", "")
                user = message.get("user", "unknown_user")  # Slack user ID

                # Skip already processed messages
                if is_message_processed(message["ts"]):
                    continue

                # Attempt to create a task via the LLM
                task_json_str = infer_task(text)
                print(f"the slack json response is {task_json_str} {text}")
                if task_json_str:
                    try:
                        task_data = json.loads(task_json_str)
                        task_data["owner"] = user
                        task_data["source"] = "slack"
                        save_new_task(task_data)
                        mark_message_as_processed(message["ts"])  # Mark the message as processed
                    except Exception as e:
                        print("Could not parse LLM response as JSON:", e)

            # Sleep 5s before checking Slack again
            time.sleep(5)

        except SlackApiError as e:
            print(f"Slack API Error: {e.response['error']}")
            time.sleep(5)
        except Exception as e:
            print("Error in monitor_slack_channel:", e)
            traceback.print_exc()
            time.sleep(5)


def is_message_processed(ts: str) -> bool:
    """
    Check if a message with the given 'ts' has already been processed.
    """
    db = SessionLocal()
    try:
        return db.query(ProcessedMessage).filter_by(ts=ts).first() is not None
    finally:
        db.close()


def mark_message_as_processed(ts: str):
    """
    Save the Slack message 'ts' to the processed_messages table.
    """
    db = SessionLocal()
    try:
        processed_message = ProcessedMessage(ts=ts)
        db.add(processed_message)
        db.commit()
        print(f"Marked message {ts} as processed.")
    except Exception as e:
        db.rollback()
        print("Error marking message as processed:", e)
    finally:
        db.close()

def infer_task(message: str) -> str:
    """
    Sends the Slack message to OpenAI, requesting a JSON with keys:
      { title, description, due_date }
    Returns the raw JSON string from the LLM, or None if no valid content.
    """
    # system_prompt = generate_prompt_no_prpfile()
    system_prompt = generate_prompt()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Message: {message}"}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview", #"gpt-3.5-turbo",
        messages=messages
    )
    llm_text = response.choices[0].message.content.strip()
    return llm_text if llm_text else None


def save_new_task(task_data: dict):
    """
    Saves a new Task row to DB, with added fields for 'owner' and 'source'.
    """
    db = SessionLocal()
    try:
        new_task = Task(
            title=task_data.get("title", ""),
            description=json.dumps(task_data.get("description", {})),
            due_date=task_data.get("due_date"),
            status="pending",
            owner=task_data.get("owner"),
            source=task_data.get("source"),
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        print(f"New Task saved: {new_task.title} from source {new_task.source}")
    except Exception as e:
        db.rollback()
        print("Error saving new task:", e)
    finally:
        db.close()
        db.close()