/**
 * MedIA Health OS — Progressive Web App (PWA) Service Worker
 * Estratégia de cache: Network-First com Fallback Offline para consultas territoriais.
 */

const CACHE_NAME = "media-health-os-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/app",
  "/static/index.html",
  "/static/landing.html",
  "/static/app.js",
  "/static/js/command_bar.js",
  "https://cdn.tailwindcss.com",
  "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[Service Worker] Pré-carregando App Shell no cache offline...");
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => console.warn("Cache inicial parcial:", err));
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const requestUrl = new URL(event.request.url);

  // APIs dinâmicas: Network first com resposta padrão se offline
  if (requestUrl.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(
          JSON.stringify({ offline: true, mensagem: "Modo Offline ativo. Dados sincronizados localmente." }),
          { headers: { "Content-Type": "application/json" } }
        );
      })
    );
    return;
  }

  // Assets estáticos: Cache-first com revalidação
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) return cachedResponse;
      return fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === "basic") {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
        }
        return networkResponse;
      });
    })
  );
});
