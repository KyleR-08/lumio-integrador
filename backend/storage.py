import os
import uuid
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

def guardar_archivo(archivo:UploadFile):
    if archivo.content_type not in TIPOS:
        raise HTTPException(status_code=400,detail="Solo se permiten imágenes JPG, PNG o WEBP")
    contenido=archivo.file.read()
    if len(contenido)>MAXIMO:
        raise HTTPException(status_code=400,detail="La imagen supera los 10 MB")
    nombre=uuid.uuid4().hex+TIPOS[archivo.content_type]
    try:
        s3.put_object(Bucket=BUCKET,Key=nombre,Body=contenido,ContentType=archivo.content_type)
    except (BotoCoreError,ClientError):
        raise HTTPException(status_code=502,detail="No se pudo subir la imagen al bucket de S3")
    url="https://"+BUCKET+".s3."+REGION+".amazonaws.com/"+nombre
    return nombre,url

def borrar_archivo(nombre:str):
    try:
        s3.delete_object(Bucket=BUCKET,Key=nombre)
    except (BotoCoreError,ClientError):
        pass
