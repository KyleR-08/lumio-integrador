from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel

class ImagenActualizar(SQLModel):
    titulo:Optional[str]=None
    descripcion:Optional[str]=None
    categoria_id:Optional[int]=None

class ImagenLeer(SQLModel):
    id:int
    titulo:str
    nombre_archivo:str
    descripcion:str
    fecha_registro:datetime
    categoria_id:int
    usuario_id:int
    categoria_nombre:str
    usuario_nombre:str
    url:str
