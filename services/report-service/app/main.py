from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import reports

app = FastAPI(title="Report Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router, prefix="/reports", tags=["reports"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "report-service"}
