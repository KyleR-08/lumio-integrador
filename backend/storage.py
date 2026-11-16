import os
import uuid
from fastapi import HTTPException,UploadFile

CARPETA=os.path.join(os.path.dirname(__file__),"uploads")
TIPOS={"image/jpeg":".jpg","image/png":".png","image/webp":".webp"}
MAXIMO=10*1024*1024

os.makedirs(CARPETA,exist_ok=True)

def guardar_archivo(archivo:UploadFile):
    if archivo.content_type not in TIPOS:
        raise HTTPException(status_code=400,detail="Solo se permiten imágenes JPG, PNG o WEBP")
    contenido=archivo.file.read()
    if len(contenido)>MAXIMO:
        raise HTTPException(status_code=400,detail="La imagen supera los 10 MB")
    nombre=uuid.uuid4().hex+TIPOS[archivo.content_type]
    with open(os.path.join(CARPETA,nombre),"wb") as destino:
        destino.write(contenido)
    return nombre

def borrar_archivo(nombre:str):
    ruta=os.path.join(CARPETA,nombre)
    if os.path.exists(ruta):
        os.remove(ruta)
