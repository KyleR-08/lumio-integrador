# Pruebas automáticas de los controles de la Fase 3. Usan una base de datos temporal (no tocan lumio.db) y no llaman a S3.
# Uso (desde la carpeta LumioAvance3, con el entorno virtual activo): python pruebas/prueba_fase3.py
import os,sys,tempfile,time,json,hashlib,base64
base=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","backend")
tmp=tempfile.mkdtemp()
os.environ["LUMIO_DB"]=os.path.join(tmp,"prueba.db")
os.environ["LUMIO_SECRET"]="clave-de-prueba"
os.environ.setdefault("AWS_DEFAULT_REGION","us-east-1")
sys.path.insert(0,base)
os.chdir(tmp)
from fastapi.testclient import TestClient
from sqlmodel import Session,select
import main
from db import engine
from models import Usuario,Imagen,EventoAuditoria
import auth

res=[]
def t(nombre,ok,detalle=""):
    res.append(bool(ok))
    print(("OK   " if ok else "FALLA")+" | "+nombre+(" | "+detalle if detalle else ""))

with TestClient(main.app) as c:
    def login(correo,clave):
        r=c.post("/api/usuarios/login",json={"correo":correo,"contrasena":clave})
        return r
    r=c.get("/api/imagenes/"); t("T1 GET /imagenes sin token -> 401",r.status_code==401,str(r.status_code))
    r=c.get("/api/usuarios/"); t("T1b GET /usuarios sin token -> 401",r.status_code==401,str(r.status_code))
    r=login("admin@lumio.app","admin123")
    t("T2 login admin -> 200 con token",r.status_code==200 and "token" in r.json(),str(r.status_code))
    with Session(engine) as s:
        h=s.exec(select(Usuario).where(Usuario.correo=="admin@lumio.app")).first().contrasena
    t("T2b hash del admin es scrypt con sal de 16 bytes",h.startswith("scrypt$") and len(h.split("$")[1])==32,h[:20]+"...")
    with Session(engine) as s:
        s.add(Usuario(nombre="Antiguo",correo="antiguo@lumio.app",contrasena=hashlib.sha256(b"clave-vieja1").hexdigest(),rol="Usuario",estado="Activo")); s.commit()
    r=login("antiguo@lumio.app","clave-vieja1")
    with Session(engine) as s:
        h2=s.exec(select(Usuario).where(Usuario.correo=="antiguo@lumio.app")).first().contrasena
    t("T3 usuario con SHA-256 entra y su hash se migra a scrypt",r.status_code==200 and h2.startswith("scrypt$"),h2[:12])
    codigos=[login("admin@lumio.app","mala"+str(i)).status_code for i in range(5)]
    r6=login("admin@lumio.app","admin123")
    t("T4 5 fallos -> 401 y el 6.o intento (aun con clave correcta) -> 429",codigos==[401]*5 and r6.status_code==429,str(codigos)+" luego "+str(r6.status_code))
    a=login("noexiste@lumio.app","x").json()["detail"]; b=login("antiguo@lumio.app","incorrecta").json()["detail"]
    t("T4b mismo mensaje para correo inexistente y clave incorrecta",a==b,a)
    with Session(engine) as s:
        for e in s.exec(select(EventoAuditoria).where(EventoAuditoria.accion=="LOGIN",EventoAuditoria.resultado=="FALLO",EventoAuditoria.correo=="admin@lumio.app")).all(): s.delete(e)
        s.commit()
    r=c.post("/api/usuarios/registro",json={"nombre":"Ana Prueba","correo":"ana@lumio.app","contrasena":"corta"}); t("T5 registro con clave de 5 caracteres -> 400",r.status_code==400,r.json()["detail"])
    r=c.post("/api/usuarios/registro",json={"nombre":"Ana Prueba","correo":"ana@lumio.app","contrasena":"claveSegura1"}); t("T5b registro valido -> 201 con rol Usuario",r.status_code==201 and r.json()["rol"]=="Usuario",str(r.status_code))
    r=c.post("/api/usuarios/registro",json={"nombre":"Ana 2","correo":"ana@lumio.app","contrasena":"claveSegura1"}); t("T5c correo repetido -> mensaje generico",r.status_code==400 and "registrado" not in r.json()["detail"],r.json()["detail"])
    r=login("ana@lumio.app","claveSegura1"); ana={"Authorization":"Bearer "+r.json()["token"]}; ana_id=r.json()["id"]; tok=r.json()["token"]
    adm={"Authorization":"Bearer "+login("admin@lumio.app","admin123").json()["token"]}
    r=c.get("/api/usuarios/",headers=ana); t("T6 usuario normal GET /usuarios -> 403",r.status_code==403,str(r.status_code))
    r=c.get("/api/usuarios/",headers=adm); t("T6b administrador GET /usuarios -> 200",r.status_code==200,str(len(r.json()))+" usuarios")
    r=c.patch("/api/usuarios/"+str(ana_id),json={"rol":"Administrador"},headers=ana)
    with Session(engine) as s: rol=s.get(Usuario,ana_id).rol
    t("T7 escalada: usuario se pone rol Administrador -> 403 y el rol no cambia",r.status_code==403 and rol=="Usuario",str(r.status_code)+" rol="+rol)
    r=c.post("/api/usuarios/",json={"nombre":"X","correo":"x@lumio.app","contrasena":"claveSegura1","rol":"Administrador"},headers=ana); t("T7b usuario crea administrador por POST /usuarios -> 403",r.status_code==403,str(r.status_code))
    r=c.patch("/api/usuarios/1",json={"nombre":"Hack"},headers=ana); t("T7c usuario modifica a otro usuario -> 403",r.status_code==403,str(r.status_code))
    r=c.patch("/api/usuarios/"+str(ana_id),json={"nombre":"Ana Editada"},headers=ana); t("T7d usuario modifica su propio nombre -> 200",r.status_code==200,str(r.status_code))
    r=c.patch("/api/usuarios/"+str(ana_id),json={"rol":"Editor"},headers=adm); t("T7e administrador cambia rol -> 200",r.status_code==200 and r.json()["rol"]=="Editor",str(r.status_code))
    carga,firma=tok.split(".")
    falso=auth._b64(json.dumps({"uid":1,"exp":int(time.time())+999}).encode())+"."+firma
    r=c.get("/api/imagenes/",headers={"Authorization":"Bearer "+falso}); t("T8 token con carga alterada (uid=1) -> 401",r.status_code==401,str(r.status_code))
    venc=auth._b64(json.dumps({"uid":1,"exp":int(time.time())-10}).encode()); venc=venc+"."+auth._firmar(venc)
    r=c.get("/api/imagenes/",headers={"Authorization":"Bearer "+venc}); t("T8b token vencido -> 401",r.status_code==401,str(r.status_code))
    r=c.post("/api/categorias/",json={"nombre":"Nueva","descripcion":"x"},headers=ana); t("T9 usuario crea categoria -> 403",r.status_code==403,str(r.status_code))
    r=c.get("/api/categorias/",headers=ana); t("T9b usuario lista categorias -> 200",r.status_code==200,str(r.status_code))
    r=c.post("/api/categorias/",json={"nombre":"Nueva","descripcion":"x"},headers=adm); t("T9c administrador crea categoria -> 201",r.status_code==201,str(r.status_code))
    datos={"titulo":"x","descripcion":"","categoria_id":"1"}
    r=c.post("/api/imagenes/",files={"archivo":("shell.png",b"<?php system($_GET['c']); ?>","image/png")},data=datos,headers=ana)
    t("T10 archivo PHP renombrado .png con Content-Type image/png -> 400",r.status_code==400,r.json().get("detail",""))
    r=c.post("/api/imagenes/",files={"archivo":("doc.pdf",b"%PDF-1.4","application/pdf")},data=datos,headers=ana)
    t("T10b PDF -> 400 por tipo",r.status_code==400,r.json().get("detail",""))
    r=c.post("/api/imagenes/",files={"archivo":("a.jpg",b"\x89PNG\r\n\x1a\n"+b"0"*20,"image/jpeg")},data=datos,headers=ana)
    t("T10c PNG real declarado como JPEG -> 400",r.status_code==400,r.json().get("detail",""))
    r=c.post("/api/imagenes/",files={"archivo":("a.png",b"x","image/png")},data=datos)
    t("T10d subir imagen sin token -> 401",r.status_code==401,str(r.status_code))
    with Session(engine) as s:
        s.add(Imagen(titulo="Del admin",nombre_archivo="arte/prueba.png",url="https://x/y.png",descripcion="",categoria_id=1,usuario_id=1)); s.commit()
        iid=s.exec(select(Imagen)).first().id
    r=c.delete("/api/imagenes/"+str(iid),headers=ana); t("T11 usuario borra imagen ajena -> 403",r.status_code==403,str(r.status_code))
    r=c.patch("/api/imagenes/"+str(iid),json={"titulo":"x"},headers=ana); t("T11b usuario edita imagen ajena -> 403",r.status_code==403,str(r.status_code))
    r=c.get("/api/auditoria/",headers=ana); t("T12 usuario consulta auditoria -> 403",r.status_code==403,str(r.status_code))
    r=c.get("/api/auditoria/?limite=500",headers=adm); ev=r.json()
    acc={}
    for e in ev: acc[e["accion"]+"/"+e["resultado"]]=acc.get(e["accion"]+"/"+e["resultado"],0)+1
    print("      eventos:",json.dumps(dict(sorted(acc.items())),ensure_ascii=False))
    t("T12b auditoria (admin) -> 200 con LOGIN, LOGIN_BLOQUEADO, ACCESO_DENEGADO, ARCHIVO_RECHAZADO, CAMBIO_ROL, CATEGORIA_CREADA",r.status_code==200 and all(any(e["accion"]==x for e in ev) for x in ["LOGIN","LOGIN_BLOQUEADO","ACCESO_DENEGADO","ARCHIVO_RECHAZADO","CAMBIO_ROL","CATEGORIA_CREADA"]))
    texto=json.dumps(ev)
    t("T12c el registro no contiene contrasenas ni el token",all(x not in texto for x in ["claveSegura1","clave-vieja1","admin123","mala0",tok]))
print("\nRESULTADO: %d/%d comprobaciones correctas"%(sum(res),len(res)))
