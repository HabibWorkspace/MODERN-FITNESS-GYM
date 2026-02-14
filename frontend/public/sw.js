const CACHE_NAME = 'fitnix-pro-v1'

// Install event
self.addEventListener('install', (event) => {
  self.skipWaiting()
})

// Activate event
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          return caches.delete(cacheName)
        })
      )
    })
  )
  self.clients.claim()
})

// Fetch event - Network first for everything
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // Skip non-http(s) requests
  if (!url.protocol.startsWith('http')) {
    return
  }

  // Network first strategy
  event.respondWith(
    fetch(request)
      .then((response) => {
        return response
      })
      .catch(() => {
        // Return offline page or cached response if available
        return caches.match(request).catch(() => {
          return new Response('Offline - No cached data available', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
              'Content-Type': 'text/plain'
            })
          })
        })
      })
  )
})
