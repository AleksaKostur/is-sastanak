from fastapi import FastAPI
from .routers import reports

app = FastAPI(title="Report Service")

app.include_router(reports.router, prefix="/reports", tags=["reports"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "report-service"}
