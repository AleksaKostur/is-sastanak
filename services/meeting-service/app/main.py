from fastapi import FastAPI
from .routers import meetings, agenda, participants, calendar, notifications

app = FastAPI(title="Meeting Service")

app.include_router(meetings.router,       prefix="/meetings",      tags=["meetings"])
app.include_router(agenda.router,         prefix="/meetings",      tags=["agenda"])
app.include_router(participants.router,   prefix="/meetings",      tags=["participants"])
app.include_router(calendar.router,       prefix="/calendar",      tags=["calendar"])
app.include_router(notifications.router,  prefix="/notifications", tags=["notifications"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "meeting-service"}
