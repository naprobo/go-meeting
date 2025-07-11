import os
from fastapi import FastAPI
from routes import auth, reports, logs, meetings, users, admin, delivery
from database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

origins = [
    "https://meeting.xxxxxxx.xxx",  # Ensure the frontend URL is correct
    "http://xxx.xxx.xxx.xxx:5173"
]

# Allow LAN access
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow these origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(meetings.router, prefix="/api")  # Add meeting management API
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(reports.router)
app.include_router(logs.router, prefix="/api/logs")  # Add log API
app.include_router(delivery.router, prefix="/api/delivery")

# Handle `static` directory path to ensure compatibility with Docker and local environments
static_dir = os.path.abspath("static")  # Default is `backend/static`
if os.getenv("DOCKER_ENV"):  # If running in Docker
    static_dir = "/app/backend/static"

if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

# Mount static files directory, frontend will access via `/`
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
