from fastapi import APIRouter,Depends,HTTPException,status
from sqlmodel import Session,select
from db import get_session
from models import Categoria,Imagen
from schemas.categoria import CategoriaCrear,CategoriaActualizar

router=APIRouter(prefix="/categorias",tags=["categorias"])

@router.get("/",response_model=list[Categoria])
def get_categorias(session:Session=Depends(get_session)):
    return session.exec(select(Categoria)).all()

@router.get("/{categoria_id}",response_model=Categoria)
def get_categoria(categoria_id:int,session:Session=Depends(get_session)):
    categoria=session.get(Categoria,categoria_id)
    if not categoria:
        raise HTTPException(status_code=404,detail="Categoría no encontrada")
    return categoria

@router.post("/",response_model=Categoria,status_code=status.HTTP_201_CREATED)
def create_categoria(data:CategoriaCrear,session:Session=Depends(get_session)):
    categoria=Categoria(**data.model_dump())
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria

@router.patch("/{categoria_id}",response_model=Categoria)
def update_categoria(categoria_id:int,data:CategoriaActualizar,session:Session=Depends(get_session)):
    categoria=session.get(Categoria,categoria_id)
    if not categoria:
        raise HTTPException(status_code=404,detail="Categoría no encontrada")
    categoria.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria

@router.delete("/{categoria_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(categoria_id:int,session:Session=Depends(get_session)):
    categoria=session.get(Categoria,categoria_id)
    if not categoria:
        raise HTTPException(status_code=404,detail="Categoría no encontrada")
    imagen=session.exec(select(Imagen).where(Imagen.categoria_id==categoria_id)).first()
    if imagen:
        raise HTTPException(status_code=400,detail="La categoría tiene imágenes y no se puede eliminar")
    session.delete(categoria)
    session.commit()
