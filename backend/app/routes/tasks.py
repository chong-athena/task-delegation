from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal, Task, Client

router = APIRouter()

@router.get("/tasks")
def get_tasks():
    """
    Return all tasks from DB so the frontend can display them.
    """
    db = SessionLocal()
    try:
        return db.query(Task).all()
    finally:
        db.close()


@router.post("/tasks")
def add_task(payload: dict):
    """
    Expects JSON like:
      { 
        "title": "write an email", 
        "owner": "Alice", 
        "due_date": "2025-01-15 10:00", 
        "status": "pending" 
      }
    """
    db: Session = SessionLocal()
    try:
        new_task = Task(
            title=payload.get("title", ""),
            owner=payload.get("owner", ""),  # <--- store it
            description=payload.get("description", ""),
            due_date=payload.get("due_date"),
            status=payload.get("status", "pending"),
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task  # <--- Return the whole model, which includes owner
    finally:
        db.close()


@router.get("/tasks/{task_id}/instructions")
def get_instructions(task_id: int):
    """
    Placeholder route. 
    In the future, call your separate instructions service here.
    For now, we just return a dummy string.
    """
    # e.g. fake example if we want to do something like:
    # instructions = call_instructions_microservice(task_id)
    instructions = "Some generated instructions (fetched from another service)."
    return {"task_id": task_id, "instructions": instructions}


@router.put("/tasks/{task_id}")
def update_task(task_id: int, payload: dict):
    """
    Update a task by ID. 
    Expects a JSON payload with some or all of: 
      { "title": ..., "description": ..., "due_date": ..., "status": ... }
    """
    print(f"saving the data {payload}")
    db: Session = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Update fields that are present in payload
        if "title" in payload:
            task.title = payload["title"]
        if "description" in payload:
            task.description = payload["description"]
        if "owner" in payload:
            task.owner = payload["owner"]
        if "due_date" in payload:
            task.due_date = payload["due_date"]
        if "status" in payload:
            task.status = payload["status"]

        print(f"the new task {task}")

        db.commit()
        db.refresh(task)
        return task
    finally:
        db.close()


@router.post("/clients")
def register_client(name: str, slack_id: str = None, email: str = None):
    """
    Register a new client with Slack ID and/or email.
    """
    db = SessionLocal()
    try:
        if slack_id and db.query(Client).filter_by(slack_id=slack_id).first():
            raise HTTPException(status_code=400, detail="Slack ID already exists.")
        if email and db.query(Client).filter_by(email=email).first():
            raise HTTPException(status_code=400, detail="Email already exists.")

        new_client = Client(name=name, slack_id=slack_id, email=email)
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        return {"message": "Client registered successfully.", "client": new_client}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/clients")
def list_clients():
    """
    List all registered clients.
    """
    db = SessionLocal()
    try:
        clients = db.query(Client).all()
        return clients
    finally:
        db.close()