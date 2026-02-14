// Offline action queue management using IndexedDB

let db = null

export async function initOfflineQueue() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('FitNixProDB', 1)
    
    request.onerror = () => reject(request.error)
    request.onsuccess = () => {
      db = request.result
      resolve(db)
    }
    
    request.onupgradeneeded = (event) => {
      const database = event.target.result
      if (!database.objectStoreNames.contains('offlineActions')) {
        database.createObjectStore('offlineActions', { keyPath: 'id', autoIncrement: true })
      }
    }
  })
}

export async function queueOfflineAction(action) {
  if (!db) {
    await initOfflineQueue()
  }

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['offlineActions'], 'readwrite')
    const store = transaction.objectStore('offlineActions')
    const request = store.add({
      ...action,
      timestamp: new Date().toISOString(),
    })
    
    request.onerror = () => reject(request.error)
    request.onsuccess = () => resolve(request.result)
  })
}

export async function getOfflineActions() {
  if (!db) {
    await initOfflineQueue()
  }

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['offlineActions'], 'readonly')
    const store = transaction.objectStore('offlineActions')
    const request = store.getAll()
    
    request.onerror = () => reject(request.error)
    request.onsuccess = () => resolve(request.result)
  })
}

export async function removeOfflineAction(id) {
  if (!db) {
    await initOfflineQueue()
  }

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['offlineActions'], 'readwrite')
    const store = transaction.objectStore('offlineActions')
    const request = store.delete(id)
    
    request.onerror = () => reject(request.error)
    request.onsuccess = () => resolve()
  })
}

export async function clearOfflineActions() {
  if (!db) {
    await initOfflineQueue()
  }

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['offlineActions'], 'readwrite')
    const store = transaction.objectStore('offlineActions')
    const request = store.clear()
    
    request.onerror = () => reject(request.error)
    request.onsuccess = () => resolve()
  })
}

export async function syncOfflineActions(apiClient) {
  const actions = await getOfflineActions()
  const results = []

  for (const action of actions) {
    try {
      let response
      
      if (action.method === 'GET') {
        response = await apiClient.get(action.url)
      } else if (action.method === 'POST') {
        response = await apiClient.post(action.url, action.body)
      } else if (action.method === 'PUT') {
        response = await apiClient.put(action.url, action.body)
      } else if (action.method === 'DELETE') {
        response = await apiClient.delete(action.url)
      }

      // Remove from queue on success
      await removeOfflineAction(action.id)
      results.push({ id: action.id, success: true, response })
    } catch (error) {
      results.push({ id: action.id, success: false, error: error.message })
    }
  }

  return results
}

// Request background sync when online
export function requestBackgroundSync() {
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    navigator.serviceWorker.ready.then((registration) => {
      registration.sync.register('sync-offline-actions')
    })
  }
}
