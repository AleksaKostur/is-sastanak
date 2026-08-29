from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import users, auth, roles

app = FastAPI(title="Auth Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(roles.router, prefix="/roles", tags=["roles"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth"}