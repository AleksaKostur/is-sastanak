from fastapi import FastAPI

app = FastAPI(title="Meeting Service")

@app.get("/health")
def health():
    return {"status": "ok", "service": "meeting"}
