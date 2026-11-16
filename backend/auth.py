import hashlib
from fastapi import HTTPException
from sqlmodel import Session,select
from models import Usuario

def encriptar(contrasena:str):
    return hashlib.sha256(contrasena.encode()).hexdigest()

def login(correo:str,contrasena:str,session:Session):
    statement=select(Usuario).where(Usuario.correo==correo)
    usuario=session.exec(statement).first()
    if not usuario or usuario.contrasena!=encriptar(contrasena):
        raise HTTPException(status_code=401,detail="Credenciales incorrectas")
    if usuario.estado!="Activo":
        raise HTTPException(status_code=403,detail="El usuario no está activo")
    return usuario
