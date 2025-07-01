from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import downloads, tags, config, media_managers
from src.database import init_db

app = FastAPI()

# Configure CORS - more permissive configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Disable credentials requirement
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize database
init_db()

# Include routers
app.include_router(downloads.router)
app.include_router(tags.router)
app.include_router(config.router)
app.include_router(media_managers.router)

@app.get("/")
async def root():
    return {"message": "Media Downloader API"}
