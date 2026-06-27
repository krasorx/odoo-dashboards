/** @odoo-module */
function injectScript(id, src) {
    if (document.getElementById(id)) return;
    const s = document.createElement('script');
    s.id = id;
    s.src = src;
    document.head.appendChild(s);
}
injectScript('pd-tw-cdn', 'https://cdn.tailwindcss.com');
injectScript('pd-chartjs-cdn', 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js');
