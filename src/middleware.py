
import logging
import time

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware




def register_middleware(app: FastAPI):
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins = ["https://linuxserver.tailea0f78.ts.net", "https://documentmanagementservice.ru"],
        allow_methods = ["GET", "POST", "PUT", "DELETE"],
        allow_headers = ["Content-Type", "Authorization"]
    )
    
    async def custom_logging(request: Request, call_next):
        if request.client:
            start_time = time.time()

            response = await call_next(request)
            processing_time = time.time() - start_time

            message = f"{request.client.host}:{request.client.port} - {request.method} - {request.url.path} - {response.status_code} completed after {processing_time}s"

        print(message)
        return response