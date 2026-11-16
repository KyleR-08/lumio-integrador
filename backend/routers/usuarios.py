from fastapi import APIRouter,Depends,HTTPException,status
from sqlmodel import Session,select
from db import get_session
from models import Usuario,Imagen
from auth import login,encriptar
from schemas.usuario import UsuarioCrear,UsuarioActualizar,UsuarioLogin,UsuarioLeer

router=APIRouter(prefix="/usuarios",tags=["usuarios"])

@router.get("/",response_model=list[UsuarioLeer])
def get_usuarios(session:Session=Depends(get_session)):
    return session.exec(select(Usuario)).all()

@router.get("/{usuario_id}",response_model=UsuarioLeer)
def get_usuario(usuario_id:int,session:Session=Depends(get_session)):
    usuario=session.get(Usuario,usuario_id)
    if not usuario:
        raise HTTPException(status_code=404,detail="Usuario no encontrado")
    return usuario

@router.post("/",response_model=UsuarioLeer,status_code=status.HTTP_201_CREATED)
def create_usuario(data:UsuarioCrear,session:Session=Depends(get_session)):
    existe=session.exec(select(Usuario).where(Usuario.correo==data.correo)).first()
    if existe:
        raise HTTPException(status_code=400,detail="El correo ya está registrado")
    datos=data.model_dump()
    datos["contrasena"]=encriptar(datos["contrasena"])
    usuario=Usuario(**datos)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

@router.patch("/{usuario_id}",response_model=UsuarioLeer)
def update_usuario(usuario_id:int,data:UsuarioActualizar,session:Session=Depends(get_session)):
    usuario=session.get(Usuario,usuario_id)
    if not usuario:
        raise HTTPException(status_code=404,detail="Usuario no encontrado")
    datos=data.model_dump(exclude_unset=True)
    if "contrasena" in datos:
        datos["contrasena"]=encriptar(datos["contrasena"])
    usuario.sqlmodel_update(datos)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

@router.delete("/{usuario_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(usuario_id:int,session:Session=Depends(get_session)):
    usuario=session.get(Usuario,usuario_id)
    if not usuario:
        raise HTTPException(status_code=404,detail="Usuario no encontrado")
    imagen=session.exec(select(Imagen).where(Imagen.usuario_id==usuario_id)).first()
    if imagen:
        raise HTTPException(status_code=400,detail="El usuario tiene imágenes y no se puede eliminar")
    session.delete(usuario)
    session.commit()

@router.post("/login",response_model=UsuarioLeer)
def login_usuario(data:UsuarioLogin,session:Session=Depends(get_session)):
    return login(data.correo,data.contrasena,session)
