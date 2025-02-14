from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
from contextlib import asynccontextmanager

from app.routes.example import router as example_router
from app.routes.tasks import router as tasks_router
from app.slack_service import monitor_slack_channel
from app.gmail_service import monitor_gmail  # Import the Gmail monitor

SENDER_EMAIL = "sunchong@gmail.com"  # Replace with the sender email to monitor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Launch the Slack monitoring in a background thread
    slack_thread = Thread(target=monitor_slack_channel, daemon=True)
    slack_thread.start()

    # Launch the Gmail monitoring in a background thread
    gmail_thread = Thread(target=monitor_gmail, args=(SENDER_EMAIL,), daemon=True)
    gmail_thread.start()

    print("Background threads for Slack and Gmail monitoring started.")

    # Yield control back to FastAPI to continue processing requests
    yield

    # Cleanup logic can go here if necessary (e.g., stop threads)
    print("Application shutting down...")

# Initialize the FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to FastAPI with Next.js!"}

# Attach other routes
app.include_router(example_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")