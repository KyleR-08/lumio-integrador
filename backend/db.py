import os
from sqlmodel import SQLModel,Session,create_engine,select
from models import Categoria,Usuario
from auth import hash_contrasena

ruta=os.getenv("LUMIO_DB") or os.path.join(os.path.dirname(__file__),"lumio.db")
sqlite_url="sqlite:///"+ruta
engine=create_engine(sqlite_url)

def create_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if not session.exec(select(Categoria)).first():
            session.add(Categoria(nombre="Arte",descripcion="Pinturas, esculturas e ilustraciones"))
            session.add(Categoria(nombre="Hogar",descripcion="Interiores y decoración"))
            session.add(Categoria(nombre="Viajes",descripcion="Paisajes y lugares"))
            session.add(Categoria(nombre="Arquitectura",descripcion="Edificios y espacios"))
        if not session.exec(select(Usuario)).first():
            session.add(Usuario(nombre="Administrador Lumio",correo="admin@lumio.app",contrasena=hash_contrasena("admin123"),rol="Administrador",estado="Activo"))
        session.commit()

def get_session():
    with Session(engine) as session:
        yield session
