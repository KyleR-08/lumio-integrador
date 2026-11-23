import base64,hashlib,hmac,json,os,secrets,time
from datetime import datetime,timedelta,timezone
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlmodel import Session,select
from models import Usuario,EventoAuditoria

load_dotenv()

# CS-02: contraseñas con sal, bloqueo de intentos y mensajes genéricos
LONGITUD_MINIMA=8
INTENTOS_MAXIMOS=5
VENTANA_BLOQUEO=timedelta(minutes=15)

# CS-04: token de sesión firmado (HMAC-SHA256) con vencimiento
CLAVE=(os.getenv("LUMIO_SECRET") or secrets.token_hex(32)).encode()
DURACION_TOKEN=8*60*60

def ahora():
    return datetime.now(timezone.utc)

def hash_contrasena(contrasena:str):
    sal=secrets.token_bytes(16)
    resumen=hashlib.scrypt(contrasena.encode(),salt=sal,n=2**14,r=8,p=1,dklen=32)
    return "scrypt$"+sal.hex()+"$"+resumen.hex()

def verificar_contrasena(contrasena:str,guardado:str):
    if guardado.startswith("scrypt$"):
        _,sal,resumen=guardado.split("$")
        calculado=hashlib.scrypt(contrasena.encode(),salt=bytes.fromhex(sal),n=2**14,r=8,p=1,dklen=32)
        return hmac.compare_digest(calculado.hex(),resumen),False
    # formato anterior (SHA-256 sin sal): se acepta una vez y se vuelve a guardar con sal
    antiguo=hashlib.sha256(contrasena.encode()).hexdigest()
    return hmac.compare_digest(antiguo,guardado),True

HASH_FALSO=hash_contrasena("contrasena-que-no-existe")

def validar_contrasena(contrasena:str):
    if len(contrasena)<LONGITUD_MINIMA:
        raise HTTPException(status_code=400,detail="La contraseña debe tener al menos "+str(LONGITUD_MINIMA)+" caracteres")

def _b64(datos:bytes):
    return base64.urlsafe_b64encode(datos).decode().rstrip("=")

def _firmar(texto:str):
    return _b64(hmac.new(CLAVE,texto.encode(),hashlib.sha256).digest())

def crear_token(usuario_id:int):
    carga=_b64(json.dumps({"uid":usuario_id,"exp":int(time.time())+DURACION_TOKEN}).encode())
    return carga+"."+_firmar(carga)

def leer_token(token:str):
    try:
        carga,firma=token.split(".")
        if not hmac.compare_digest(firma,_firmar(carga)):
            return None
        datos=json.loads(base64.urlsafe_b64decode(carga+"="*(-len(carga)%4)))
        if datos["exp"]<time.time():
            return None
        return int(datos["uid"])
    except Exception:
        return None

def intentos_recientes(correo:str,session:Session):
    desde=ahora()-VENTANA_BLOQUEO
    statement=select(EventoAuditoria).where(EventoAuditoria.accion=="LOGIN",EventoAuditoria.resultado=="FALLO",EventoAuditoria.correo==correo,EventoAuditoria.fecha_hora>=desde)
    return len(session.exec(statement).all())

def login(correo:str,contrasena:str,session:Session,ip:str=""):
    from auditoria import registrar
    if intentos_recientes(correo,session)>=INTENTOS_MAXIMOS:
        registrar(session,"LOGIN_BLOQUEADO","DENEGADO",correo=correo,recurso="POST /api/usuarios/login",ip=ip,detalle="Se superaron "+str(INTENTOS_MAXIMOS)+" intentos fallidos en 15 minutos")
        raise HTTPException(status_code=429,detail="Demasiados intentos fallidos. Intenta de nuevo en 15 minutos")
    usuario=session.exec(select(Usuario).where(Usuario.correo==correo)).first()
    valida=False
    antiguo=False
    if usuario:
        valida,antiguo=verificar_contrasena(contrasena,usuario.contrasena)
    else:
        # se hace el mismo cálculo aunque la cuenta no exista, para que el tiempo de respuesta no delate qué correos están registrados
        verificar_contrasena(contrasena,HASH_FALSO)
    if not usuario or not valida:
        registrar(session,"LOGIN","FALLO",correo=correo,recurso="POST /api/usuarios/login",ip=ip,detalle="Credenciales incorrectas")
        raise HTTPException(status_code=401,detail="Credenciales incorrectas")
    if usuario.estado!="Activo":
        registrar(session,"LOGIN","DENEGADO",correo=correo,usuario_id=usuario.id,recurso="POST /api/usuarios/login",ip=ip,detalle="Usuario inactivo")
        raise HTTPException(status_code=403,detail="El usuario no está activo")
    if antiguo:
        usuario.contrasena=hash_contrasena(contrasena)
        session.add(usuario)
        session.commit()
        registrar(session,"CONTRASENA_ACTUALIZADA_HASH","EXITO",correo=correo,usuario_id=usuario.id,ip=ip,detalle="Hash SHA-256 sin sal reemplazado por scrypt con sal")
    registrar(session,"LOGIN","EXITO",correo=correo,usuario_id=usuario.id,recurso="POST /api/usuarios/login",ip=ip)
    return usuario
