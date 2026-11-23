from fastapi import Depends,HTTPException,Request
from sqlmodel import Session
from db import get_session
from models import Usuario
from auth import leer_token
from auditoria import registrar

# CS-04 / CS-05: autorización validada en el servidor (token firmado + rol), no solo en el navegador

def ip_de(request:Request):
    return request.client.host if request.client else ""

def usuario_actual(request:Request,session:Session=Depends(get_session)):
    cabecera=request.headers.get("Authorization","")
    usuario=None
    if cabecera.startswith("Bearer "):
        usuario_id=leer_token(cabecera[7:])
        if usuario_id:
            usuario=session.get(Usuario,usuario_id)
    if not usuario or usuario.estado!="Activo":
        registrar(session,"ACCESO_DENEGADO","DENEGADO",recurso=request.method+" "+request.url.path,ip=ip_de(request),detalle="Sin sesión válida")
        raise HTTPException(status_code=401,detail="Sesión no válida o vencida")
    return usuario

def requiere_admin(request:Request,usuario:Usuario=Depends(usuario_actual),session:Session=Depends(get_session)):
    if usuario.rol!="Administrador":
        registrar(session,"ACCESO_DENEGADO","DENEGADO",correo=usuario.correo,usuario_id=usuario.id,recurso=request.method+" "+request.url.path,ip=ip_de(request),detalle="Rol "+usuario.rol+" sin permiso de administrador")
        raise HTTPException(status_code=403,detail="No tienes permiso para esta acción")
    return usuario

def denegar(session:Session,request:Request,usuario:Usuario,detalle:str):
    registrar(session,"ACCESO_DENEGADO","DENEGADO",correo=usuario.correo,usuario_id=usuario.id,recurso=request.method+" "+request.url.path,ip=ip_de(request),detalle=detalle)
    raise HTTPException(status_code=403,detail="No tienes permiso para esta acción")
