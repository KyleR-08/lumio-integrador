from typing import Optional,List
from datetime import datetime,timezone
from sqlmodel import SQLModel,Field,Relationship

class Categoria(SQLModel,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    nombre:str
    descripcion:str
    imagenes:List["Imagen"]=Relationship(back_populates="categoria")

class Usuario(SQLModel,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    nombre:str
    correo:str
    contrasena:str
    rol:str
    estado:str
    imagenes:List["Imagen"]=Relationship(back_populates="usuario")

class Imagen(SQLModel,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    titulo:str
    nombre_archivo:str
    url:str
    descripcion:str
    fecha_registro:datetime=Field(default_factory=lambda:datetime.now(timezone.utc))
    categoria_id:int=Field(foreign_key="categoria.id")
    usuario_id:int=Field(foreign_key="usuario.id")
    categoria:Optional[Categoria]=Relationship(back_populates="imagenes")
    usuario:Optional[Usuario]=Relationship(back_populates="imagenes")


class EventoAuditoria(SQLModel,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    fecha_hora:datetime=Field(default_factory=lambda:datetime.now(timezone.utc),index=True)
    usuario_id:Optional[int]=None
    correo:str=""
    accion:str
    resultado:str
    recurso:str=""
    ip:str=""
    detalle:str=""
