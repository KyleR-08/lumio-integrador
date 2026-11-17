from typing import Optional
from sqlmodel import SQLModel

class UsuarioCrear(SQLModel):
    nombre:str
    correo:str
    contrasena:str
    rol:str="Usuario"
    estado:str="Activo"

class UsuarioRegistro(SQLModel):
    nombre:str
    correo:str
    contrasena:str

class UsuarioActualizar(SQLModel):
    nombre:Optional[str]=None
    correo:Optional[str]=None
    contrasena:Optional[str]=None
    rol:Optional[str]=None
    estado:Optional[str]=None

class UsuarioLogin(SQLModel):
    correo:str
    contrasena:str

class UsuarioLeer(SQLModel):
    id:int
    nombre:str
    correo:str
    rol:str
    estado:str
