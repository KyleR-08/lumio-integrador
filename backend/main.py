from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from db import create_db
from storage import CARPETA
from routers import usuarios,imagenes,categorias

URL_S3="http://CAMBIAR-NOMBRE-BUCKET.s3-website-us-east-1.amazonaws.com"

app=FastAPI(
    title="Lumio API",
    description="API de Galería Cloud Segura para gestionar imágenes, usuarios y categorías",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[URL_S3,"http://127.0.0.1:5500","http://localhost:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    create_db()

api_prefix="/api"

app.include_router(usuarios.router,prefix=api_prefix)
app.include_router(imagenes.router,prefix=api_prefix)
app.include_router(categorias.router,prefix=api_prefix)

app.mount("/uploads",StaticFiles(directory=CARPETA),name="uploads")
