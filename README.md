# Lumio - Galería Cloud Segura

Proyecto Integrador, Avance 3. Programación Web, UIDE.

Integrantes: Kyle Reinoso, Ariel Esparza y Alejandro Zambrano.

El frontend (HTML, CSS y JavaScript) se publica en Amazon S3. El backend (FastAPI) y la base de datos (SQLite) corren en el computador del equipo.

## Estructura

- frontend/: páginas HTML, style.css y app.js
- backend/main.py: crea la app, el CORS y las rutas
- backend/db.py: conexión a SQLite y datos iniciales
- backend/models.py: tablas Usuario, Categoria e Imagen
- backend/schemas/: datos que recibe y devuelve la API
- backend/routers/: endpoints de imagenes, usuarios y categorias
- backend/auth.py: login y encriptado de contraseñas
- backend/storage.py: subir y borrar las imágenes en el bucket de S3 lumio-imagenes-uide

## Cómo correr el backend

Desde la carpeta backend:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

La API queda en http://127.0.0.1:8000 y la documentación en http://127.0.0.1:8000/docs.

Al arrancar se crea lumio.db con 4 categorías (Arte, Hogar, Viajes, Arquitectura) y un administrador:

- Correo: admin@lumio.app
- Contraseña: admin123

## Cómo correr el frontend en local

Abrir la carpeta frontend con Live Server (puerto 5500) y entrar a index.html.

## Endpoints

Todos empiezan con /api.

| Recurso | Método y ruta | Qué hace |
|---|---|---|
| Imágenes | POST /imagenes/ | Registrar (formulario con archivo) |
| | GET /imagenes/ | Consultar todas (filtros: categoria_id, usuario_id, buscar) |
| | GET /imagenes/{id} | Detalle |
| | PATCH /imagenes/{id} | Actualizar título, descripción o categoría |
| | DELETE /imagenes/{id} | Eliminar (borra también el archivo) |
| Usuarios | POST /usuarios/ | Registrar |
| | GET /usuarios/ | Consultar todos |
| | GET /usuarios/{id} | Detalle |
| | PATCH /usuarios/{id} | Actualizar |
| | DELETE /usuarios/{id} | Eliminar |
| | POST /usuarios/login | Iniciar sesión |
| Categorías | POST /categorias/ | Registrar |
| | GET /categorias/ | Consultar todas |
| | GET /categorias/{id} | Detalle |
| | PATCH /categorias/{id} | Actualizar |
| | DELETE /categorias/{id} | Eliminar |

Reglas: el correo no se puede repetir, solo entran usuarios con estado Activo, no se elimina un usuario ni una categoría que tenga imágenes, y las imágenes deben ser JPG, PNG o WEBP de máximo 10 MB.

## Modelo de datos

- Usuario: id, nombre, correo, contrasena, rol, estado
- Categoria: id, nombre, descripcion
- Imagen: id, titulo, nombre_archivo, descripcion, fecha_registro, categoria_id, usuario_id

Un usuario tiene varias imágenes, una categoría tiene varias imágenes y cada imagen pertenece a un usuario y a una categoría.

## Publicar el frontend en Amazon S3

1. En S3 crear un bucket (nombre único, por ejemplo lumio-galeria-uide).
2. En el bucket, pestaña Permissions, desactivar Block all public access y confirmar.
3. Pestaña Properties, al final, Static website hosting: Enable, Index document: index.html.
4. Pestaña Permissions, Bucket policy, pegar esto cambiando NOMBRE-DEL-BUCKET:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LecturaPublica",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::NOMBRE-DEL-BUCKET/*"
    }
  ]
}
```

5. Pestaña Objects, Upload: subir todo lo que está dentro de frontend (los 7 HTML, style.css y app.js).
6. En Properties, Static website hosting, copiar el Bucket website endpoint.
7. En backend/main.py cambiar la constante URL_S3 por ese endpoint, sin la barra final, y reiniciar uvicorn.
8. Abrir el endpoint en el navegador del computador donde corre el backend.

El endpoint de S3 es http (no https), igual que el backend local. Si Chrome muestra un aviso para permitir el acceso a la red local, hay que aceptarlo.

## Notas

- guardadas.html se mantiene como en el Avance 2 (diseño estático): el Avance 3 no incluye guardar imágenes.
- Las contraseñas se guardan con SHA-256. Para un proyecto real convendría usar bcrypt.

## Bucket de imágenes (segundo bucket de S3)

Las fotos no se guardan en el servidor. El backend las sube a un segundo bucket (`lumio-imagenes-uide`) y la base de datos guarda el link completo en la columna `url` de la tabla Imagen. El frontend muestra la foto directamente desde ese link.

1. Copiar `backend/.env.example` a `backend/.env` y completar `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` de un usuario IAM que solo tenga permiso `s3:PutObject` y `s3:DeleteObject` sobre `lumio-imagenes-uide/*`.
2. El archivo `.env` está en `.gitignore`: las claves no se suben a GitHub.
3. Instalar dependencias con `pip install -r requirements.txt` (incluye `boto3` y `python-dotenv`).
