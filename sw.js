/* Gerado pelo build.py. Guarda o consultor no aparelho para funcionar sem internet.
   Com internet: busca sempre a versao nova primeiro (e guarda a copia).
   Sem internet, ou com a rede muito lenta: entrega a copia guardada. */
const VERSAO = 'estoque-22dbf-055c0';
const FONTES = 'estoque-fontes';
const PAGINA = new URL('index.html', self.registration.scope).href;
const ESSENCIAIS = ['index.html', 'manifest.webmanifest', 'icone-192.png', 'icone-512.png',
                    'icone-mascara-512.png', 'icone-180.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(ESSENCIAIS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((nomes) => Promise.all(nomes
      .filter((n) => n.startsWith('estoque-') && n !== VERSAO && n !== FONTES)
      .map((n) => caches.delete(n))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (u.hostname === 'fonts.googleapis.com' || u.hostname === 'fonts.gstatic.com') {
    e.respondWith(guardadoPrimeiro(req, FONTES));
    return;
  }
  if (u.origin !== self.location.origin) return;        // outros sites: sempre direto na rede
  if (u.pathname.endsWith('/versao.txt')) return;        // aviso de versao nova: sempre da rede
  if (req.mode === 'navigate') { e.respondWith(paginaRedePrimeiro(req)); return; }
  e.respondWith(guardadoPrimeiro(req, VERSAO));
});

async function paginaRedePrimeiro(req) {
  const cache = await caches.open(VERSAO);
  const daRede = fetch(req).then((resp) => {
    if (resp && resp.ok) cache.put(PAGINA, resp.clone());
    return resp;
  });
  daRede.catch(() => {});
  try {
    // rede muito lenta: depois de 4 segundos mostra a copia guardada (e a rede atualiza a copia quando chegar)
    return await Promise.race([daRede, new Promise((_, nao) => setTimeout(() => nao(new Error('lenta')), 4000))]);
  } catch (erro) {
    const guardada = await cache.match(PAGINA);
    return guardada || daRede;
  }
}

async function guardadoPrimeiro(req, nome) {
  const cache = await caches.open(nome);
  const achou = await cache.match(req);
  if (achou) return achou;
  const resp = await fetch(req);
  if (resp && (resp.ok || resp.type === 'opaque')) cache.put(req, resp.clone());
  return resp;
}
