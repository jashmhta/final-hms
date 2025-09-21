const CACHE_NAME = 'hms-enterprise-v1'
const URLS_TO_CACHE = [
  '/',
  '/static/js/bundle.js',
  '/static/js/1.chunk.js',
  '/static/js/main.chunk.js',
  '/static/css/main.chunk.css',
  '/manifest.json',
  '/favicon.ico',
  '/pwa-192x192.png',
  '/pwa-512x512.png'
]

const API_CACHE_NAME = 'hms-api-v1'
const IMAGE_CACHE_NAME = 'hms-images-v1'

// Install event - cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(URLS_TO_CACHE))
      .then(() => self.skipWaiting())
  )
})

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME &&
              cacheName !== API_CACHE_NAME &&
              cacheName !== IMAGE_CACHE_NAME) {
            return caches.delete(cacheName)
          }
        })
      )
    }).then(() => self.clients.claim())
  )
})

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url)

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Clone the response to cache it
          const responseToCache = response.clone()

          // Cache successful API responses
          if (response.status === 200) {
            caches.open(API_CACHE_NAME).then(cache => {
              cache.put(event.request, responseToCache)
            })
          }

          return response
        })
        .catch(() => {
          // Return cached API response when offline
          return caches.match(event.request)
        })
    )
    return
  }

  // Handle image requests
  if (event.request.url.match(/\.(jpg|jpeg|png|gif|svg|webp)$/)) {
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          // If found in cache, return it
          if (response) {
            return response
          }

          // Otherwise fetch from network and cache
          return fetch(event.request).then(response => {
            const responseToCache = response.clone()
            caches.open(IMAGE_CACHE_NAME).then(cache => {
              cache.put(event.request, responseToCache)
            })
            return response
          })
        })
    )
    return
  }

  // Handle other requests
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version if available
        if (response) {
          return response
        }

        // Otherwise fetch from network
        return fetch(event.request).then(response => {
          // Don't cache non-successful responses
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response
          }

          // Cache the response
          const responseToCache = response.clone()
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache)
          })

          return response
        })
      })
  )
})

// Handle background sync for offline API calls
self.addEventListener('sync', event => {
  if (event.tag === 'sync-patient-data') {
    event.waitUntil(
      // Sync offline patient data
      syncOfflineData()
    )
  }
})

// Handle push notifications
self.addEventListener('push', event => {
  const options = {
    body: event.data.text(),
    icon: '/pwa-192x192.png',
    badge: '/pwa-192x192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Explore',
        icon: '/pwa-192x192.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/pwa-192x192.png'
      }
    ]
  }

  event.waitUntil(
    self.registration.showNotification('HMS Enterprise', options)
  )
})

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  const notification = event.notification
  const action = event.action

  if (action === 'close') {
    notification.close()
  } else {
    event.waitUntil(
      clients.openWindow('/')
    )
    notification.close()
  }
})

// Sync offline data
async function syncOfflineData() {
  try {
    // Get offline data from IndexedDB
    const offlineData = await getOfflineData()

    // Sync with server
    for (const data of offlineData) {
      try {
        await fetch(data.url, {
          method: data.method,
          headers: data.headers,
          body: JSON.stringify(data.body)
        })

        // Remove synced data
        await removeOfflineData(data.id)
      } catch (error) {
        console.error('Failed to sync data:', error)
      }
    }
  } catch (error) {
    console.error('Sync failed:', error)
  }
}

// Mock IndexedDB operations (replace with actual implementation)
async function getOfflineData() {
  return []
}

async function removeOfflineData(id) {
  // Implementation for removing synced offline data
}

// Cache cleanup for old data
self.addEventListener('message', event => {
  if (event.data === 'cleanup-cache') {
    event.waitUntil(
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName.startsWith('hms-')) {
              return caches.open(cacheName).then(cache => {
                return cache.keys().then(keys => {
                  // Keep only recent items (last 7 days)
                  const weekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000)
                  const oldKeys = keys.filter(key => {
                    return Date.parse(key.headers.get('date') || '') < weekAgo
                  })

                  return Promise.all(oldKeys.map(key => cache.delete(key)))
                })
              })
            }
          })
        )
      })
    )
  }
})