/** @odoo-module */
function injectScript(id, src) {
    if (document.getElementById(id)) return;
    const s = document.createElement('script');
    s.id = id;
    s.src = src;
    document.head.appendChild(s);
}
function injectStylesheet(id, href) {
    if (document.getElementById(id)) return;
    const l = document.createElement('link');
    l.id = id;
    l.rel = 'stylesheet';
    l.href = href;
    document.head.appendChild(l);
}
function injectPreconnect(id, href) {
    if (document.getElementById(id)) return;
    const l = document.createElement('link');
    l.id = id;
    l.rel = 'preconnect';
    l.href = href;
    l.crossOrigin = 'anonymous';
    document.head.appendChild(l);
}
injectScript('pd-tw-cdn', 'https://cdn.tailwindcss.com');
injectScript('pd-chartjs-cdn', 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js');
// Type system for the "technical instrument" look: Archivo (grotesque) + IBM Plex Mono (data).
injectPreconnect('pd-gf-pre1', 'https://fonts.googleapis.com');
injectPreconnect('pd-gf-pre2', 'https://fonts.gstatic.com');
injectStylesheet(
    'pd-fonts',
    'https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap',
);
