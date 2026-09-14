from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routers import system_router

name = "LiveGraph Backend"
version = "0.1.0"
app =  FastAPI(title= name, version= version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(system_router.router)

