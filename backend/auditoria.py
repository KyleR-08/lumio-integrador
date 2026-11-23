import logging
from sqlmodel import Session
from models import EventoAuditoria

# CS-07: registro de auditoría de la aplicación (eventos de negocio de Lumio).
# No reemplaza a AWS CloudTrail: CloudTrail registra llamadas a la API de AWS (S3, IAM),
# este registro guarda quién hizo qué dentro de Lumio. Nunca se guardan contraseñas ni tokens.
log=logging.getLogger("lumio.auditoria")

def registrar(session:Session,accion:str,resultado:str,correo:str="",usuario_id:int=None,recurso:str="",ip:str="",detalle:str=""):
    evento=EventoAuditoria(accion=accion,resultado=resultado,correo=correo or "",usuario_id=usuario_id,recurso=recurso,ip=ip,detalle=detalle)
    session.add(evento)
    session.commit()
    log.warning("AUDITORIA accion=%s resultado=%s correo=%s usuario_id=%s recurso=%s ip=%s detalle=%s",accion,resultado,correo,usuario_id,recurso,ip,detalle)
