const ES_ADMIN = 1;

if (!ES_ADMIN) {
    document.documentElement.classList.add('sin-admin');
    if (document.documentElement.hasAttribute('data-requiere-admin')) {
        window.location.replace('galeria.html');
    }
}
