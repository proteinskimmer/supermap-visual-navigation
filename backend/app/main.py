from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, navigation, reports, risks, routes, simulations, supermap, tasks, vision
from app.api.errors import http_exception_handler, unhandled_exception_handler, validation_exception_handler

app = FastAPI(title="SuperMap Low-Altitude Planning API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

for router in [
    health.router,
    tasks.router,
    routes.router,
    risks.router,
    navigation.router,
    simulations.router,
    supermap.router,
    vision.router,
    reports.router,
]:
    app.include_router(router, prefix="/api")
