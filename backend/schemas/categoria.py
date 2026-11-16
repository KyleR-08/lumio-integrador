from typing import Optional
from sqlmodel import SQLModel

class CategoriaCrear(SQLModel):
    nombre:str
    descripcion:str=""

class CategoriaActualizar(SQLModel):
    nombre:Optional[str]=None
    descripcion:Optional[str]=None
