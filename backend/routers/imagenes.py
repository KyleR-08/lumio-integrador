from typing import Optional
from fastapi import APIRouter,Depends,HTTPException,status,UploadFile,File,Form
from sqlmodel import Session,select
from db import get_session
from models import Imagen,Categoria,Usuario
from storage import guardar_archivo,borrar_archivo
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
        url="/uploads/"+imagen.nombre_archivo
    )

@router.get("/",response_model=list[ImagenLeer])
def get_imagenes(categoria_id:Optional[int]=None,usuario_id:Optional[int]=None,buscar:str="",session:Session=Depends(get_session)):
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
def get_imagen(imagen_id:int,session:Session=Depends(get_session)):
    imagen=session.get(Imagen,imagen_id)
    if not imagen:
        raise HTTPException(status_code=404,detail="Imagen no encontrada")
    return armar(imagen)

@router.post("/",response_model=ImagenLeer,status_code=status.HTTP_201_CREATED)
def create_imagen(archivo:UploadFile=File(...),titulo:str=Form(...),descripcion:str=Form(""),categoria_id:int=Form(...),usuario_id:int=Form(...),session:Session=Depends(get_session)):
    if not session.get(Categoria,categoria_id):
        raise HTTPException(status_code=404,detail="Categoría no encontrada")
    if not session.get(Usuario,usuario_id):
        raise HTTPException(status_code=404,detail="Usuario no encontrado")
    nombre_archivo=guardar_archivo(archivo)
    imagen=Imagen(titulo=titulo,nombre_archivo=nombre_archivo,descripcion=descripcion,categoria_id=categoria_id,usuario_id=usuario_id)
    session.add(imagen)
    session.commit()
    session.refresh(imagen)
    return armar(imagen)

@router.patch("/{imagen_id}",response_model=ImagenLeer)
def update_imagen(imagen_id:int,data:ImagenActualizar,session:Session=Depends(get_session)):
    imagen=session.get(Imagen,imagen_id)
    if not imagen:
        raise HTTPException(status_code=404,detail="Imagen no encontrada")
    datos=data.model_dump(exclude_unset=True)
    if "categoria_id" in datos and not session.get(Categoria,datos["categoria_id"]):
        raise HTTPException(status_code=404,detail="Categoría no encontrada")
    imagen.sqlmodel_update(datos)
    session.add(imagen)
    session.commit()
    session.refresh(imagen)
    return armar(imagen)

@router.delete("/{imagen_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_imagen(imagen_id:int,session:Session=Depends(get_session)):
    imagen=session.get(Imagen,imagen_id)
    if not imagen:
        raise HTTPException(status_code=404,detail="Imagen no encontrada")
    borrar_archivo(imagen.nombre_archivo)
    session.delete(imagen)
    session.commit()
