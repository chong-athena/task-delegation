import time
import base64
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.database import SessionLocal, Task, ProcessedEmail  # Your database session and task model
from app.config import settings
from openai import OpenAI

from app.prompt_template_profile import generate_prompt_email

CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "../credentials/credentials.json")
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "../credentials/token.json")


# Scopes required for Gmail API
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# OpenAI API client
openai_client = OpenAI(api_key=settings.OPEN_AI_API_KEY)

def authenticate_gmail():
    """
    Authenticate with the Gmail API and return a service object.
    """
    creds = None
    # Load saved credentials if they exist
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If no valid credentials, authenticate and save them
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=8181)
        # Save the credentials for the next run
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def fetch_emails_from_sender(service, sender_email):
    """
    Fetch emails from the Gmail inbox sent by a specific sender.
    """
    query = f"from:{sender_email}"  # Gmail query to filter by sender
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    return messages

def extract_email_content(service, message_id):
    """
    Extract the content of an email.
    """
    message = service.users().messages().get(userId="me", id=message_id).execute()
    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    body_data = payload.get("body", {}).get("data")
    parts = payload.get("parts", [])
    
    if body_data:
        body = base64.urlsafe_b64decode(body_data).decode("utf-8")
    elif parts:
        body = base64.urlsafe_b64decode(parts[0].get("body", {}).get("data", "")).decode("utf-8")
    else:
        body = ""
    
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
    
    return subject, sender, body

def infer_task_from_email(subject, body):
    """
    Use OpenAI to extract a task from the email subject and body.
    """
    prompt = generate_prompt_email(subject, body)


    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "system", "content": prompt}]
    )
    print(f"LLM response is {response}")
    llm_response = response.choices[0].message.content.strip()
    try:
        task_data = json.loads(llm_response)
        return task_data
    except json.JSONDecodeError:
        print("Error: Could not parse LLM response as JSON.")
        return None

def save_task_to_db(task_data):
    """
    Save the inferred task to the database with 'owner' and 'source'.
    """
    db = SessionLocal()
    try:
        new_task = Task(
            title=task_data.get("title", ""),
            description=task_data.get("description", ""),
            due_date=task_data.get("due_date"),
            status="pending",
            owner=task_data.get("owner"),  # Set the email sender as the owner
            source=task_data.get("source"),  # Set source as "email"
        )
        db.add(new_task)
        db.commit()
        print(f"Task saved: {new_task.title} from {new_task.source}")
    except Exception as e:
        db.rollback()
        print(f"Error saving task to database: {e}")
    finally:
        db.close()

def is_message_processed(message_id):
    """
    Check if a message has already been processed.
    """
    db = SessionLocal()
    try:
        return db.query(ProcessedEmail).filter_by(message_id=message_id).first() is not None
    finally:
        db.close()

def mark_message_as_processed(message_id):
    """
    Mark a message as processed by saving its ID in the database.
    """
    db = SessionLocal()
    try:
        processed_message = ProcessedEmail(message_id=message_id)
        db.add(processed_message)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error marking message as processed: {e}")
    finally:
        db.close()

def monitor_gmail(sender_email):
    """
    Continuously monitor Gmail inbox for new emails from a specific sender,
    extract tasks, and save them.
    """
    service = authenticate_gmail()
    while True:
        try:
            # Fetch emails from the specified sender
            messages = fetch_emails_from_sender(service, sender_email)
            for msg in messages:
                message_id = msg["id"]
                if is_message_processed(message_id):
                    continue  # Skip already processed messages

                # Extract email content
                subject, sender, body = extract_email_content(service, message_id)

                # Infer task from email
                task_data = infer_task_from_email(subject, body)
                if task_data:
                    task_data["owner"] = sender  # Set email sender as owner
                    task_data["source"] = "email"  # Set source as "email"
                    save_task_to_db(task_data)

                # Mark the message as processed
                mark_message_as_processed(message_id)
                print(f"Processed email from {sender}: {subject}")

            # Wait 10 seconds before checking for new emails
            time.sleep(10)
        except Exception as e:
            print(f"Error in monitor_gmail: {e}")
            time.sleep(10)