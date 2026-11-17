const API = "http://127.0.0.1:8000";

const usuario = JSON.parse(localStorage.getItem("usuario"));
const ES_ADMIN = usuario && usuario.rol === "Administrador";

if (!usuario && !document.documentElement.hasAttribute("data-publica")) {
    window.location.replace("index.html");
}

if (!ES_ADMIN) {
    document.documentElement.classList.add("sin-admin");
    if (document.documentElement.hasAttribute("data-requiere-admin")) {
        window.location.replace("galeria.html");
    }
}

function iniciales(nombre) {
    const partes = nombre.split(" ");
    let letras = partes[0][0];
    if (partes[1]) {
        letras = letras + partes[1][0];
    }
    return letras.toUpperCase();
}

function crearTarjeta(imagen) {
    const item = document.createElement("li");
    const enlace = document.createElement("a");
    const foto = document.createElement("img");
    const titulo = document.createElement("h3");
    const datos = document.createElement("p");
    enlace.className = "card";
    enlace.href = "detalle.html?id=" + imagen.id;
    foto.className = "card__img";
    foto.src = imagen.url;
    foto.alt = imagen.titulo;
    titulo.className = "card__title";
    titulo.textContent = imagen.titulo;
    datos.className = "card__meta";
    datos.textContent = imagen.categoria_nombre + " · " + imagen.usuario_nombre;
    enlace.appendChild(foto);
    enlace.appendChild(titulo);
    enlace.appendChild(datos);
    item.appendChild(enlace);
    return item;
}

document.addEventListener("DOMContentLoaded", function () {
    const avatar = document.querySelector(".header .avatar");
    if (avatar && usuario) {
        avatar.textContent = iniciales(usuario.nombre);
    }
});
