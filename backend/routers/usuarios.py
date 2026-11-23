from fastapi import APIRouter,Depends,HTTPException,Request,status
from sqlmodel import Session,select
from db import get_session
from models import Usuario,Imagen
from auth import login,hash_contrasena,validar_contrasena,crear_token
from auditoria import registrar
from permisos import usuario_actual,requiere_admin,denegar,ip_de
from schemas.usuario import UsuarioCrear,UsuarioActualizar,UsuarioLogin,UsuarioLeer,UsuarioRegistro,UsuarioSesion

router=APIRouter(prefix="/usuarios",tags=["usuarios"])

@router.post("/login",response_model=UsuarioSesion)
def login_usuario(data:UsuarioLogin,request:Request,session:Session=Depends(get_session)):
    usuario=login(data.correo,data.contrasena,session,ip_de(request))
    return UsuarioSesion(id=usuario.id,nombre=usuario.nombre,correo=usuario.correo,rol=usuario.rol,estado=usuario.estado,token=crear_token(usuario.id))

@router.post("/registro",response_model=UsuarioLeer,status_code=status.HTTP_201_CREATED)
def registro_usuario(data:UsuarioRegistro,request:Request,session:Session=Depends(get_session)):
    validar_contrasena(data.contrasena)
    existe=session.exec(select(Usuario).where(Usuario.correo==data.correo)).first()
    if existe:
        registrar(session,"REGISTRO_USUARIO","FALLO",correo=data.correo,recurso="POST /api/usuarios/registro",ip=ip_de(request),detalle="Correo ya registrado")
        raise HTTPException(status_code=400,detail="No se pudo completar el registro con esos datos")
    usuario=Usuario(nombre=data.nombre,correo=data.correo,contrasena=hash_contrasena(data.contrasena),rol="Usuario",estado="Activo")
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    registrar(session,"REGISTRO_USUARIO","EXITO",correo=usuario.correo,usuario_id=usuario.id,recurso="POST /api/usuarios/registro",ip=ip_de(request))
    return usuario

@router.get("/",response_model=list[UsuarioLeer])
def get_usuarios(admin:Usuario=Depends(requiere_admin),session:Session=Depends(get_session)):
    return session.exec(select(Usuario)).all()

@router.get("/{usuario_id}",response_model=UsuarioLeer)
def get_usuario(usuario_id:int,request:Request,actual:Usuario=Depends(usuario_actual),session:Session=Depends(get_session)):
    if actual.rol!="Administrador" and actual.id!=usuario_id:
        denegar(session,request,actual,"Intento de consultar a otro usuario")
    usuario=session.get(Usuario,usuario_id)
    if not usuario:
        raise HTTPException(status_code=404,detail="Usuario no encontrado")
    return usuario

@router.post("/",response_model=UsuarioLeer,status_code=status.HTTP_201_CREATED)
def create_usuario(data:UsuarioCrear,request:Request,admin:Usuario=Depends(requiere_admin),session:Session=Depends(get_session)):
    validar_contrasena(data.contrasena)
    existe=session.exec(select(Usuario).where(Usuario.correo==data.correo)).first()
    if existe:
        raise HTTPException(status_code=400,detail="El correo ya está registrado")
    datos=data.model_dump()
    datos["contrasena"]=hash_contrasena(datos["contrasena"])
    usuario=Usuario(**datos)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    registrar(session,"USUARIO_CREADO","EXITO",correo=admin.correo,usuario_id=admin.id,recurso="usuario:"+str(usuario.id),ip=ip_de(request),detalle="Rol asignado: "+usuario.rol)
    return usuario

@router.patch("/{usuario_id}",response_model=UsuarioLeer)
def update_usuario(usuario_id:int,data:UsuarioActualizar,request:Request,actual:Usuario=Depends(usuario_actual),session:Session=Depends(get_session)):
    es_admin=actual.rol=="Administrador"
    if not es_admin and actual.id!=usuario_id:
        denegar(session,request,actual,"Intento de modificar a otro usuario")
    datos=data.model_dump(exclude_unset=True)
    if not es_admin and ("rol" in datos or "estado" in datos):
        denegar(session,request,actual,"Intento de cambiar rol o estado sin ser administrador")
    usuario=session.get(Usuario,usuario_id)
    if not usuario:
        raise HTTPException(status_code=404,detail="Usuario no encontrado")
    rol_anterior=usuario.rol
    if "contrasena" in datos:
        validar_contrasena(datos["contrasena"])
        datos["contrasena"]=hash_contrasena(datos["contrasena"])
    usuario.sqlmodel_update(datos)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    registrar(session,"USUARIO_MODIFICADO","EXITO",correo=actual.correo,usuario_id=actual.id,recurso="usuario:"+str(usuario.id),ip=ip_de(request),detalle="Campos: "+", ".join(sorted(datos.keys())))
    if usuario.rol!=rol_anterior:
        registrar(session,"CAMBIO_ROL","EXITO",correo=actual.correo,usuario_id=actual.id,recurso="usuario:"+str(usuario.id),ip=ip_de(request),detalle=rol_anterior+" -> "+usuario.rol)
    return usuario

@router.delete("/{usuario_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(usuario_id:int,request:Request,admin:Usuario=Depends(requiere_admin),session:Session=Depends(get_session)):
    usuario=session.get(Usuario,usuario_id)
    if not usuario:
        raise HTTPException(status_code=404,detail="Usuario no encontrado")
    imagen=session.exec(select(Imagen).where(Imagen.usuario_id==usuario_id)).first()
    if imagen:
        raise HTTPException(status_code=400,detail="El usuario tiene imágenes y no se puede eliminar")
    session.delete(usuario)
    session.commit()
    registrar(session,"USUARIO_ELIMINADO","EXITO",correo=admin.correo,usuario_id=admin.id,recurso="usuario:"+str(usuario_id),ip=ip_de(request))
