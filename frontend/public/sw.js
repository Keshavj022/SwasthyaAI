/*
 * SwasthyaAI Service Worker (hand-written, dependency-free).
 *
 * Strategy:
 *  - Precache the app shell + offline fallback page on install.
 *  - Navigations (HTML): network-first, fall back to cached page, then /offline.
 *  - API (/api/...): network-first with a short timeout, fall back to cache.
 *  - Static assets (js/css/img/fonts): stale-while-revalidate.
 *
 * SAFETY: API responses served from cache are returned with an
 * `X-Swasthya-From-Cache: true` header so the app can flag stale/cached
 * medical data to the user instead of presenting it as live.
 */

const VERSION = 'v1';
const PRECACHE = `swasthya-precache-${VERSION}`;
const STATIC_CACHE = `swasthya-static-${VERSION}`;
const API_CACHE = `swasthya-api-${VERSION}`;
const PAGE_CACHE = `swasthya-page-${VERSION}`;

const OFFLINE_URL = '/offline';

// App shell — kept intentionally small; pages are cached at runtime.
const PRECACHE_URLS = [
  OFFLINE_URL,
  '/manifest.json',
  '/icons/icon.svg',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

const API_NETWORK_TIMEOUT_MS = 5000;
const PAGE_NETWORK_TIMEOUT_MS = 4000;

const CURRENT_CACHES = [PRECACHE, STATIC_CACHE, API_CACHE, PAGE_CACHE];

// --- install: precache the shell -------------------------------------------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(PRECACHE)
      .then((cache) =>
        // addAll fails the whole install if any request 404s; add individually
        // so a single missing asset doesn't break SW registration.
        Promise.all(
          PRECACHE_URLS.map((url) =>
            cache.add(new Request(url, { cache: 'reload' })).catch(() => undefined)
          )
        )
      )
      .then(() => self.skipWaiting())
  );
});

// --- activate: drop old caches ---------------------------------------------
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith('swasthya-') && !CURRENT_CACHES.includes(key))
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

// Allow the page to ask the SW to activate immediately.
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});

// --- helpers ----------------------------------------------------------------
function isApiRequest(url) {
  return url.pathname.startsWith('/api/');
}

function isStaticAsset(url) {
  return /\.(?:js|css|png|jpg|jpeg|svg|gif|webp|ico|woff2?|ttf|eot|json)$/i.test(url.pathname);
}

function timeout(ms) {
  return new Promise((_, reject) => setTimeout(() => reject(new Error('network-timeout')), ms));
}

// Tag a cached Response so the UI can show a "cached" indicator.
async function flagFromCache(response) {
  if (!response) return response;
  try {
    const headers = new Headers(response.headers);
    headers.set('X-Swasthya-From-Cache', 'true');
    const body = await response.clone().blob();
    return new Response(body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  } catch {
    return response;
  }
}

// Network-first with timeout; writes successful responses to `cacheName`.
async function networkFirst(request, cacheName, timeoutMs) {
  const cache = await caches.open(cacheName);
  try {
    const network = await Promise.race([fetch(request), timeout(timeoutMs)]);
    if (network && network.ok && request.method === 'GET') {
      cache.put(request, network.clone()).catch(() => undefined);
    }
    return network;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return flagFromCache(cached);
    throw err;
  }
}

// Stale-while-revalidate for static assets.
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request)
    .then((network) => {
      if (network && network.ok && request.method === 'GET') {
        cache.put(request, network.clone()).catch(() => undefined);
      }
      return network;
    })
    .catch(() => undefined);
  return cached || fetchPromise || fetch(request);
}

// --- fetch routing ----------------------------------------------------------
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Only handle GET; let the browser deal with POST/PUT/etc.
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Ignore non-http(s) schemes (chrome-extension:, data:, etc.).
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;

  // Navigations (HTML documents) -> network-first, fall back to /offline.
  if (request.mode === 'navigate') {
    event.respondWith(
      networkFirst(request, PAGE_CACHE, PAGE_NETWORK_TIMEOUT_MS).catch(async () => {
        const cache = await caches.open(PRECACHE);
        const offline = await cache.match(OFFLINE_URL);
        return (
          offline ||
          new Response('<h1>You are offline</h1>', {
            status: 503,
            headers: { 'Content-Type': 'text/html; charset=utf-8' },
          })
        );
      })
    );
    return;
  }

  // Same-origin API proxy calls (if any are routed through the Next origin).
  if (url.origin === self.location.origin && isApiRequest(url)) {
    event.respondWith(
      networkFirst(request, API_CACHE, API_NETWORK_TIMEOUT_MS).catch(
        () =>
          new Response(
            JSON.stringify({ success: false, error: 'offline', fromCache: false }),
            { status: 503, headers: { 'Content-Type': 'application/json' } }
          )
      )
    );
    return;
  }

  // Cross-origin backend API (NEXT_PUBLIC_API_URL) -> network-first w/ cache.
  if (url.origin !== self.location.origin && isApiRequest(url)) {
    event.respondWith(
      networkFirst(request, API_CACHE, API_NETWORK_TIMEOUT_MS).catch(
        () =>
          new Response(
            JSON.stringify({ success: false, error: 'offline', fromCache: false }),
            { status: 503, headers: { 'Content-Type': 'application/json' } }
          )
      )
    );
    return;
  }

  // Same-origin static assets -> stale-while-revalidate.
  if (url.origin === self.location.origin && isStaticAsset(url)) {
    event.respondWith(staleWhileRevalidate(request, STATIC_CACHE));
    return;
  }

  // Everything else: try network, fall back to any cached copy.
  event.respondWith(
    fetch(request).catch(async () => {
      const cached = await caches.match(request);
      if (cached) return cached;
      throw new Error('offline');
    })
  );
});
