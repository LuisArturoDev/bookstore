async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new ApiError(response.status, getErrorMessage(payload, response.statusText), payload)
  }

  if (response.status === 204) return null
  return response.json()
}

function getErrorMessage(payload, fallback) {
  if (!payload) return fallback || 'Ocurrió un error al comunicarse con el servidor.'
  if (typeof payload.detail === 'string') return payload.detail
  if (typeof payload === 'object') {
    return Object.entries(payload)
      .map(([field, messages]) => {
        const text = Array.isArray(messages) ? messages.join(' ') : String(messages)
        return `${field === 'non_field_errors' ? 'Datos' : field}: ${text}`
      })
      .join(' ')
  }
  return fallback || 'Ocurrió un error al comunicarse con el servidor.'
}

export class ApiError extends Error {
  constructor(status, message, payload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

export function getBooks(page = 1) {
  return request(`/books?page=${page}`)
}

export function searchBooksByCategory(category, page = 1) {
  const params = new URLSearchParams({ category, page: String(page) })
  return request(`/books/search?${params}`)
}

export function getLowStockBooks(threshold = 10, page = 1) {
  const params = new URLSearchParams({ threshold: String(threshold), page: String(page) })
  return request(`/books/low-stock?${params}`)
}

export function createBook(book) {
  return request('/books', { method: 'POST', body: JSON.stringify(book) })
}

export function updateBook(id, book) {
  return request(`/books/${id}`, { method: 'PUT', body: JSON.stringify(book) })
}

export function deleteBook(id) {
  return request(`/books/${id}`, { method: 'DELETE' })
}

export function calculatePrice(id) {
  return request(`/books/${id}/calculate-price`, { method: 'POST', body: JSON.stringify({}) })
}
