from fastapi import APIRouter,Depends,HTTPException,Request,status
from sqlmodel import Session,select
from db import get_session
from models import Categoria,Imagen,Usuario
from auditoria import registrar
from permisos import usuario_actual,requiere_admin,ip_de
from schemas.categoria import CategoriaCrear,CategoriaActualizar

router=APIRouter(prefix="/categorias",tags=["categorias"])

@router.get("/",response_model=list[Categoria])
def get_categorias(actual:Usuario=Depends(usuario_actual),session:Session=Depends(get_session)):
    return session.exec(select(Categoria)).all()

@router.get("/{categoria_id}",response_model=Categoria)
def get_categoria(categoria_id:int,actual:Usuario=Depends(usuario_actual),session:Session=Depends(get_session)):
    categoria=session.get(Categoria,categoria_id)
    if not categoria:
        raise HTTPException(status_code=404,detail="Categoría no encontrada")
    return categoria

@router.post("/",response_model=Categoria,status_code=status.HTTP_201_CREATED)
def create_categoria(data:CategoriaCrear,request:Request,admin:Usuario=Depends(requiere_admin),session:Session=Depends(get_session)):
    categoria=Categoria(**data.model_dump())
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    registrar(session,"CATEGORIA_CREADA","EXITO",correo=admin.correo,usuario_id=admin.id,recurso="categoria:"+str(categoria.id),ip=ip_de(request))
    return categoria

@router.patch("/{categoria_id}",response_model=Categoria)
def update_categoria(categoria_id:int,data:CategoriaActualizar,request:Request,admin:Usuario=Depends(requiere_admin),session:Session=Depends(get_session)):
    categoria=session.get(Categoria,categoria_id)
    if not categoria:
        raise HTTPException(status_code=404,detail="Categoría no encontrada")
    categoria.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    registrar(session,"CATEGORIA_MODIFICADA","EXITO",correo=admin.correo,usuario_id=admin.id,recurso="categoria:"+str(categoria.id),ip=ip_de(request))
    return categoria

@router.delete("/{categoria_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(categoria_id:int,request:Request,admin:Usuario=Depends(requiere_admin),session:Session=Depends(get_session)):
    categoria=session.get(Categoria,categoria_id)
    if not categoria:
        raise HTTPException(status_code=404,detail="Categoría no encontrada")
    imagen=session.exec(select(Imagen).where(Imagen.categoria_id==categoria_id)).first()
    if imagen:
        raise HTTPException(status_code=400,detail="La categoría tiene imágenes y no se puede eliminar")
    session.delete(categoria)
    session.commit()
    registrar(session,"CATEGORIA_ELIMINADA","EXITO",correo=admin.correo,usuario_id=admin.id,recurso="categoria:"+str(categoria_id),ip=ip_de(request))
