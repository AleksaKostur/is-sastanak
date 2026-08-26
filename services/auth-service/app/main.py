from fastapi import FastAPI
from .routers import users, auth, roles

app = FastAPI(title="Auth Service")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(roles.router, prefix="/roles", tags=["roles"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth"}