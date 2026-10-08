import { useCallback, useEffect, useState } from 'react'
import BookForm from './components/BookForm.jsx'
import BookTable from './components/BookTable.jsx'
import PriceResult from './components/PriceResult.jsx'
import {
  calculatePrice,
  createBook,
  deleteBook,
  getBooks,
  getLowStockBooks,
  searchBooksByCategory,
  updateBook,
} from './services/booksApi.js'
import './App.css'

const PAGE_SIZE = 10

function fetchBookPage(selectedFilter, requestedPage) {
  if (selectedFilter.type === 'category') {
    return searchBooksByCategory(selectedFilter.category, requestedPage)
  }
  if (selectedFilter.type === 'low-stock') {
    return getLowStockBooks(selectedFilter.threshold, requestedPage)
  }
  return getBooks(requestedPage)
}

function App() {
  const [booksPage, setBooksPage] = useState(null)
  const [filter, setFilter] = useState({ type: 'all', category: '', threshold: '10' })
  const [activeFilter, setActiveFilter] = useState({ type: 'all', category: '', threshold: '10' })
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [formBook, setFormBook] = useState(null)
  const [formOpen, setFormOpen] = useState(false)
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')
  const [pendingAction, setPendingAction] = useState('')
  const [notification, setNotification] = useState(null)
  const [priceResult, setPriceResult] = useState(null)

  const loadBooks = useCallback(async (requestedPage = 1, selectedFilter = activeFilter) => {
    setLoading(true)
    setLoadError('')

    try {
      const result = await fetchBookPage(selectedFilter, requestedPage)
      setBooksPage(result)
      setPage(requestedPage)
    } catch (error) {
      setLoadError(error.message || 'No se pudo cargar el inventario.')
      setBooksPage(null)
    } finally {
      setLoading(false)
    }
  }, [activeFilter])

  useEffect(() => {
    let cancelled = false
    fetchBookPage(activeFilter, 1)
      .then((result) => {
        if (cancelled) return
        setBooksPage(result)
        setPage(1)
        setLoadError('')
      })
      .catch((error) => {
        if (cancelled) return
        setLoadError(error.message || 'No se pudo cargar el inventario.')
        setBooksPage(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [activeFilter])

  useEffect(() => {
    if (!notification) return undefined
    const timeoutId = window.setTimeout(() => setNotification(null), 4200)
    return () => window.clearTimeout(timeoutId)
  }, [notification])

  const showSuccess = (message) => setNotification({ type: 'success', message })
  const showError = (message) => setNotification({ type: 'error', message })

  const openCreateForm = () => {
    setFormBook(null)
    setFormError('')
    setFormOpen(true)
  }

  const openEditForm = (book) => {
    setFormBook(book)
    setFormError('')
    setFormOpen(true)
  }

  const handleFormSubmit = async (data) => {
    setFormLoading(true)
    setFormError('')
    try {
      if (formBook) {
        await updateBook(formBook.id, data)
        showSuccess('Libro actualizado correctamente.')
      } else {
        await createBook(data)
        showSuccess('Libro agregado al inventario.')
      }
      setFormOpen(false)
      await loadBooks(1, activeFilter)
    } catch (error) {
      setFormError(error.message || 'No se pudo guardar el libro.')
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async (book) => {
    const confirmed = window.confirm(`¿Eliminar "${book.title}" del inventario? Esta acción no se puede deshacer.`)
    if (!confirmed) return

    setPendingAction(`delete-${book.id}`)
    try {
      await deleteBook(book.id)
      showSuccess('Libro eliminado del inventario.')
      const remainingOnPage = (booksPage?.results.length || 1) - 1
      const targetPage = remainingOnPage === 0 && page > 1 ? page - 1 : page
      await loadBooks(targetPage, activeFilter)
    } catch (error) {
      showError(error.message || 'No se pudo eliminar el libro.')
    } finally {
      setPendingAction('')
    }
  }

  const handleCalculatePrice = async (book) => {
    setPendingAction(`price-${book.id}`)
    try {
      const result = await calculatePrice(book.id)
      setPriceResult(result)
      showSuccess('Precio sugerido calculado correctamente.')
      await loadBooks(page, activeFilter)
    } catch (error) {
      showError(error.message || 'No se pudo calcular el precio sugerido.')
    } finally {
      setPendingAction('')
    }
  }

  const applyCategoryFilter = (event) => {
    event.preventDefault()
    const category = filter.category.trim()
    if (!category) {
      showError('Escribe una categoría para buscar.')
      return
    }
    setFilter((current) => ({ ...current, category }))
    setLoading(true)
    setActiveFilter({ type: 'category', category, threshold: '10' })
  }

  const applyLowStockFilter = (event) => {
    event.preventDefault()
    if (!/^\d+$/.test(filter.threshold.trim())) {
      showError('El umbral debe ser un entero igual o mayor que cero.')
      return
    }
    const threshold = filter.threshold.trim()
    setFilter((current) => ({ ...current, threshold }))
    setLoading(true)
    setActiveFilter({ type: 'low-stock', category: '', threshold })
  }

  const clearFilters = () => {
    setLoading(true)
    setFilter({ type: 'all', category: '', threshold: '10' })
    setActiveFilter({ type: 'all', category: '', threshold: '10' })
  }

  const handlePageChange = (url) => {
    if (!url) return
    const nextPage = Number(new URL(url, window.location.origin).searchParams.get('page') || 1)
    loadBooks(nextPage, activeFilter)
  }

  const count = booksPage?.count || 0
  const rangeStart = count === 0 ? 0 : (page - 1) * PAGE_SIZE + 1
  const rangeEnd = Math.min(page * PAGE_SIZE, count)
  const title = activeFilter.type === 'category'
    ? `Resultados para “${activeFilter.category}”`
    : activeFilter.type === 'low-stock'
      ? 'Libros con stock bajo'
      : 'Todos los libros'

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="Bookwise, inicio">
          <span className="brand-mark">b</span>
          <span>bookwise<span className="brand-period">.</span></span>
        </a>
        <div className="sidebar-label">GESTIÓN</div>
        <button className="nav-item nav-item-active" type="button">
          <span className="nav-icon">▦</span>
          Inventario
        </button>
        <div className="sidebar-note">
          <span className="note-icon">✦</span>
          <p>Un buen inventario es el comienzo de una gran historia.</p>
        </div>
        <div className="sidebar-footer">
          <span className="avatar">BI</span>
          <span><strong>Bookwise</strong><small>Panel de administración</small></span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><b>/</b><strong>Inventario</strong></div>
          <div className="topbar-right">
            <span className={`system-status${loading ? ' system-status-loading' : loadError ? ' system-status-error' : ''}`} role="status">
              <i />
              {loading ? 'Conectando con API…' : loadError ? 'Error al consultar API' : 'API conectada'}
            </span>
            <span className="avatar avatar-small">BI</span>
          </div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div>
              <div className="eyebrow"><span className="eyebrow-line" /> CONTROL DE LIBRERÍA</div>
              <h1>Inventario</h1>
              <p>Administra tus títulos, mantén el stock al día y encuentra cada libro.</p>
            </div>
            <button className="button button-primary" type="button" onClick={openCreateForm}>
              <span className="button-plus">+</span> Agregar libro
            </button>
          </section>

          <section className="summary-grid" aria-label="Resumen del inventario">
            <article className="summary-card">
              <div className="summary-top"><span className="summary-label">TÍTULOS EN INVENTARIO</span><span className="summary-icon icon-books">▤</span></div>
              <strong className="summary-value">{loading && !booksPage ? '—' : count}</strong>
              <span className="summary-caption">en esta consulta</span>
            </article>
            <article className="summary-card summary-card-highlight">
              <div className="summary-top"><span className="summary-label">VISTA ACTUAL</span><span className="summary-icon icon-view">◉</span></div>
              <strong className="summary-value summary-value-small">{activeFilter.type === 'all' ? 'Completa' : activeFilter.type === 'category' ? 'Categoría' : 'Stock bajo'}</strong>
              <span className="summary-caption">{loading ? 'Actualizando resultados…' : 'Datos sincronizados con la API'}</span>
            </article>
            <article className="summary-card summary-card-accent">
              <div className="summary-top"><span className="summary-label">PÁGINA</span><span className="summary-icon icon-page">↗</span></div>
              <strong className="summary-value">{booksPage ? `${page}` : '—'}<small className="page-total"> / {Math.max(1, Math.ceil(count / PAGE_SIZE))}</small></strong>
              <span className="summary-caption">10 libros por página</span>
            </article>
          </section>

          <section className="filter-panel" aria-label="Filtros del inventario">
            <div className="filter-panel-heading">
              <div><span className="filter-icon">⌕</span><div><h2>Encuentra un libro</h2><p>Filtra por categoría o revisa las existencias bajas.</p></div></div>
              {activeFilter.type !== 'all' && <button className="text-button" type="button" onClick={clearFilters}>Limpiar filtros <span>×</span></button>}
            </div>
            <div className="filter-controls">
              <form className="filter-form category-form" onSubmit={applyCategoryFilter}>
                <label htmlFor="category-filter">Categoría</label>
                <div className="input-button-row">
                  <input id="category-filter" value={filter.category} onChange={(event) => setFilter((current) => ({ ...current, category: event.target.value }))} placeholder="Ej. Literatura clásica" />
                  <button className="button button-outline" type="submit">Buscar</button>
                </div>
              </form>
              <div className="filter-divider" />
              <form className="filter-form stock-form" onSubmit={applyLowStockFilter}>
                <label htmlFor="threshold-filter">Stock bajo · umbral</label>
                <div className="input-button-row">
                  <input id="threshold-filter" type="number" min="0" step="1" value={filter.threshold} onChange={(event) => setFilter((current) => ({ ...current, threshold: event.target.value }))} />
                  <button className="button button-outline" type="submit"><span className="filter-button-icon">⌁</span> Ver stock bajo</button>
                </div>
              </form>
            </div>
          </section>

          <section className="inventory-panel">
            <div className="inventory-heading">
              <div><h2>{title}</h2><p>{count === 1 ? '1 libro encontrado' : `${count} libros encontrados`}</p></div>
              <div className="table-meta"><span className="live-dot" /> Actualizado en tiempo real</div>
            </div>

            {loadError && (
              <div className="inline-error" role="alert">
                <span>!</span><div><strong>No se pudo cargar el inventario</strong><p>{loadError}</p></div>
                <button className="button button-outline" type="button" onClick={() => loadBooks(page, activeFilter)}>Reintentar</button>
              </div>
            )}

            <BookTable
              books={booksPage?.results || []}
              loading={loading}
              error={loadError}
              pendingAction={pendingAction}
              onEdit={openEditForm}
              onDelete={handleDelete}
              onCalculate={handleCalculatePrice}
              onAddBook={openCreateForm}
            />

            <div className="table-footer">
              <span>Mostrando <strong>{rangeStart}–{rangeEnd}</strong> de <strong>{count}</strong> libros</span>
              <div className="pagination">
                <button type="button" className="pagination-button" aria-label="Página anterior" disabled={!booksPage?.previous || loading} onClick={() => handlePageChange(booksPage.previous)}>←</button>
                <span className="page-indicator">{page}</span>
                <button type="button" className="pagination-button" aria-label="Página siguiente" disabled={!booksPage?.next || loading} onClick={() => handlePageChange(booksPage.next)}>→</button>
              </div>
            </div>
          </section>

          <footer className="page-footer"><span>BOOKWISE INVENTORY</span><span>Hecho para cuidar cada historia.</span></footer>
        </div>
      </main>

      {formOpen && (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget && !formLoading) setFormOpen(false)
        }}>
          <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="book-form-title">
            <BookForm
              book={formBook}
              loading={formLoading}
              error={formError}
              onSubmit={handleFormSubmit}
              onCancel={() => setFormOpen(false)}
            />
          </section>
        </div>
      )}

      {priceResult && (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget) setPriceResult(null)
        }}>
          <section className="modal-card price-modal" role="dialog" aria-modal="true" aria-labelledby="price-result-title">
            <PriceResult result={priceResult} onClose={() => setPriceResult(null)} />
          </section>
        </div>
      )}

      {notification && (
        <div className={`toast toast-${notification.type}`} role={notification.type === 'error' ? 'alert' : 'status'}>
          <span className="toast-mark">{notification.type === 'success' ? '✓' : '!'}</span>
          {notification.message}
          <button type="button" aria-label="Cerrar notificación" onClick={() => setNotification(null)}>×</button>
        </div>
      )}
    </div>
  )
}

export default App
