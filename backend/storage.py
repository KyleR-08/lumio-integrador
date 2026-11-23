import os
import uuid
from urllib.parse import quote
import boto3
from botocore.exceptions import BotoCoreError,ClientError
from dotenv import load_dotenv
from fastapi import HTTPException,UploadFile

load_dotenv()

BUCKET=os.getenv("S3_BUCKET","lumio-imagenes-uide")
REGION=os.getenv("AWS_REGION","us-east-1")
TIPOS={"image/jpeg":".jpg","image/png":".png","image/webp":".webp"}
MAXIMO=10*1024*1024

s3=boto3.client("s3",region_name=REGION)

def tipo_real(contenido:bytes):
    # CS-06: el tipo se decide por los bytes iniciales del archivo (firma), no por el encabezado que envía el cliente
    if contenido[:3]==b"\xff\xd8\xff":
        return "image/jpeg"
    if contenido[:8]==b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if contenido[:4]==b"RIFF" and contenido[8:12]==b"WEBP":
        return "image/webp"
    return None

def guardar_archivo(archivo:UploadFile,carpeta:str):
    if archivo.content_type not in TIPOS:
        raise HTTPException(status_code=400,detail="Solo se permiten imágenes JPG, PNG o WEBP")
    contenido=archivo.file.read(MAXIMO+1)
    if len(contenido)>MAXIMO:
        raise HTTPException(status_code=400,detail="La imagen supera los 10 MB")
    real=tipo_real(contenido)
    if real is None or real!=archivo.content_type:
        raise HTTPException(status_code=400,detail="El contenido del archivo no corresponde a una imagen JPG, PNG o WEBP válida")
    carpeta=carpeta.strip().lower().replace(" ","-")
    nombre=carpeta+"/"+uuid.uuid4().hex+TIPOS[real]
    try:
        s3.put_object(Bucket=BUCKET,Key=nombre,Body=contenido,ContentType=archivo.content_type)
    except (BotoCoreError,ClientError):
        raise HTTPException(status_code=502,detail="No se pudo subir la imagen al bucket de S3")
    url="https://"+BUCKET+".s3."+REGION+".amazonaws.com/"+quote(nombre)
    return nombre,url

def borrar_archivo(nombre:str):
    try:
        s3.delete_object(Bucket=BUCKET,Key=nombre)
    except (BotoCoreError,ClientError):
        pass
