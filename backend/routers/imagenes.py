from typing import Optional
from fastapi import APIRouter,Depends,HTTPException,Request,status,UploadFile,File,Form
from sqlmodel import Session,select
from db import get_session
from models import Imagen,Categoria,Usuario
from storage import guardar_archivo,borrar_archivo
from auditoria import registrar
from permisos import usuario_actual,denegar,ip_de
from schemas.imagen import ImagenActualizar,ImagenLeer

router=APIRouter(prefix="/imagenes",tags=["imagenes"])

def armar(imagen:Imagen):
    return ImagenLeer(
        id=imagen.id,
        titulo=imagen.titulo,
        nombre_archivo=imagen.nombre_archivo,
        descripcion=imagen.descripcion,
        fecha_registro=imagen.fecha_registro,
        categoria_id=imagen.categoria_id,
        usuario_id=imagen.usuario_id,
        categoria_nombre=imagen.categoria.nombre,
        usuario_nombre=imagen.usuario.nombre,
        url=imagen.url
    )

def puede_modificar(actual:Usuario,imagen:Imagen):
    return actual.rol=="Administrador" or imagen.usuario_id==actual.id

@router.get("/",response_model=list[ImagenLeer])
def get_imagenes(categoria_id:Optional[int]=None,usuario_id:Optional[int]=None,buscar:str="",actual:Usuario=Depends(usuario_actual),session:Session=Depends(get_session)):
    statement=select(Imagen).order_by(Imagen.fecha_registro.desc())
    if categoria_id:
        statement=statement.where(Imagen.categoria_id==categoria_id)
    if usuario_id:
        statement=statement.where(Imagen.usuario_id==usuario_id)
    if buscar:
        statement=statement.where(Imagen.titulo.contains(buscar))
    imagenes=session.exec(statement).all()
    return [armar(imagen) for imagen in imagenes]

@router.get("/{imagen_id}",response_model=ImagenLeer)
def get_imagen(imagen_id:int,actual:Usuario=Depends(usuario_actual),session:Session=Depends(get_session)):
    imagen=session.get(Imagen,imagen_id)
    if not imagen:
        raise HTTPException(status_code=404,detail="Imagen no encontrada")
    return armar(imagen)

@router.post("/",response_model=ImagenLeer,status_code=status.HTTP_201_CREATED)
def create_imagen(request:Request,archivo:UploadFile=File(...),titulo:str=Form(...),descripcion:str=Form(""),categoria_id:int=Form(...),usuario_id:Optional[int]=Form(None),actual:Usuario=Depends(usuario_actual),session:Session=Depends(get_session)):
    # el responsable es siempre el usuario de la sesión; el usuario_id del formulario no se usa para decidir
    if usuario_id is not None and usuario_id!=actual.id and actual.rol!="Administrador":
        denegar(session,request,actual,"Intento de registrar una imagen a nombre de otro usuario")
    categoria=session.get(Categoria,categoria_id)
    if not categoria:
        raise HTTPException(status_code=404,detail="Categoría no encontrada")
    try:
        nombre_archivo,url=guardar_archivo(archivo,categoria.nombre)
    except HTTPException as error:
        if error.status_code==400:
            registrar(session,"ARCHIVO_RECHAZADO","DENEGADO",correo=actual.correo,usuario_id=actual.id,recurso="POST /api/imagenes/",ip=ip_de(request),detalle="Archivo: "+str(archivo.filename)+" | tipo declarado: "+str(archivo.content_type)+" | motivo: "+str(error.detail))
        raise
    imagen=Imagen(titulo=titulo,nombre_archivo=nombre_archivo,url=url,descripcion=descripcion,categoria_id=categoria_id,usuario_id=actual.id)
    session.add(imagen)
    session.commit()
    session.refresh(imagen)
    registrar(session,"IMAGEN_SUBIDA","EXITO",correo=actual.correo,usuario_id=actual.id,recurso="imagen:"+str(imagen.id),ip=ip_de(request),detalle=nombre_archivo)
    return armar(imagen)

@router.patch("/{imagen_id}",response_model=ImagenLeer)
def update_imagen(imagen_id:int,data:ImagenActualizar,request:Request,actual:Usuario=Depends(usuario_actual),session:Session=Depends(get_session)):
    imagen=session.get(Imagen,imagen_id)
    if not imagen:
        raise HTTPException(status_code=404,detail="Imagen no encontrada")
    if not puede_modificar(actual,imagen):
        denegar(session,request,actual,"Intento de modificar la imagen "+str(imagen_id)+" de otro usuario")
    datos=data.model_dump(exclude_unset=True)
    if "categoria_id" in datos and not session.get(Categoria,datos["categoria_id"]):
        raise HTTPException(status_code=404,detail="Categoría no encontrada")
    imagen.sqlmodel_update(datos)
    session.add(imagen)
    session.commit()
    session.refresh(imagen)
    registrar(session,"IMAGEN_MODIFICADA","EXITO",correo=actual.correo,usuario_id=actual.id,recurso="imagen:"+str(imagen.id),ip=ip_de(request),detalle="Campos: "+", ".join(sorted(datos.keys())))
    return armar(imagen)

@router.delete("/{imagen_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_imagen(imagen_id:int,request:Request,actual:Usuario=Depends(usuario_actual),session:Session=Depends(get_session)):
    imagen=session.get(Imagen,imagen_id)
    if not imagen:
        raise HTTPException(status_code=404,detail="Imagen no encontrada")
    if not puede_modificar(actual,imagen):
        denegar(session,request,actual,"Intento de eliminar la imagen "+str(imagen_id)+" de otro usuario")
    nombre=imagen.nombre_archivo
    borrar_archivo(nombre)
    session.delete(imagen)
    session.commit()
    registrar(session,"IMAGEN_ELIMINADA","EXITO",correo=actual.correo,usuario_id=actual.id,recurso="imagen:"+str(imagen_id),ip=ip_de(request),detalle=nombre)
