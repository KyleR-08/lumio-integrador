from typing import Optional
from datetime import datetime
from fastapi import APIRouter,Depends
from sqlmodel import Session,SQLModel,select
from db import get_session
from models import EventoAuditoria,Usuario
from permisos import requiere_admin

router=APIRouter(prefix="/auditoria",tags=["auditoria"])

class EventoLeer(SQLModel):
    id:int
    fecha_hora:datetime
    usuario_id:Optional[int]
    correo:str
    accion:str
    resultado:str
    recurso:str
    ip:str
    detalle:str

@router.get("/",response_model=list[EventoLeer])
def get_eventos(accion:Optional[str]=None,resultado:Optional[str]=None,limite:int=100,admin:Usuario=Depends(requiere_admin),session:Session=Depends(get_session)):
    statement=select(EventoAuditoria).order_by(EventoAuditoria.id.desc()).limit(min(limite,500))
    if accion:
        statement=statement.where(EventoAuditoria.accion==accion)
    if resultado:
        statement=statement.where(EventoAuditoria.resultado==resultado)
    return session.exec(statement).all()
