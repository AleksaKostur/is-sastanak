from fastapi import FastAPI

app = FastAPI(title="Report Service")

@app.get("/health")
def health():
    return {"status": "ok", "service": "report"}
