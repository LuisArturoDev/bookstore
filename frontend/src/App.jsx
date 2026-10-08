import { useCallback, useEffect, useState } from 'react'
import BookForm from './components/BookForm.jsx'
import BookCards from './components/BookCards.jsx'
import BookTable from './components/BookTable.jsx'
import BookDetails from './components/BookDetails.jsx'
import Modal from './components/Modal.jsx'
import PriceResult from './components/PriceResult.jsx'
import Icon from './components/Icon.jsx'
import {
  calculatePrice,
  createBook,
  deleteBook,
  getBooks,
  getLowStockBooks,
  searchBooks,
  updateBook,
} from './services/booksApi.js'
import './App.css'

const PAGE_SIZE = 10
const VIEW_MODE_STORAGE_KEY = 'bookwise.inventory.viewMode'
const THEME_STORAGE_KEY = 'bookwise.theme'

function getSavedTheme() {
  try {
    return window.localStorage.getItem(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

function getSavedViewMode() {
  try {
    const savedViewMode = window.localStorage.getItem(VIEW_MODE_STORAGE_KEY)
    return savedViewMode === 'table' || savedViewMode === 'cards' ? savedViewMode : 'cards'
  } catch {
    return 'cards'
  }
}

function fetchBookPage(selectedFilter, requestedPage) {
  if (selectedFilter.type === 'search') {
    return searchBooks(selectedFilter.title, selectedFilter.category, requestedPage)
  }
  if (selectedFilter.type === 'low-stock') {
    return getLowStockBooks(selectedFilter.threshold, requestedPage)
  }
  return getBooks(requestedPage)
}

function App() {
  const [booksPage, setBooksPage] = useState(null)
  const [filter, setFilter] = useState({ title: '', category: '', threshold: '10' })
  const [activeFilter, setActiveFilter] = useState({ type: 'all', title: '', category: '', threshold: '10' })
  const [page, setPage] = useState(1)
  const [viewMode, setViewMode] = useState(getSavedViewMode)
  const [theme, setTheme] = useState(getSavedTheme)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [formBook, setFormBook] = useState(null)
  const [formOpen, setFormOpen] = useState(false)
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')
  const [deleteBookCandidate, setDeleteBookCandidate] = useState(null)
  const [pendingAction, setPendingAction] = useState('')
  const [notification, setNotification] = useState(null)
  const [priceResult, setPriceResult] = useState(null)
  const [detailsBook, setDetailsBook] = useState(null)
  const closeBookDetails = useCallback(() => setDetailsBook(null), [])

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

  useEffect(() => {
    if (!deleteBookCandidate || pendingAction === `delete-${deleteBookCandidate.id}`) return undefined
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setDeleteBookCandidate(null)
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [deleteBookCandidate, pendingAction])

  const showSuccess = (message) => setNotification({ type: 'success', message })
  const showError = (message) => setNotification({ type: 'error', message })

  const changeViewMode = (nextViewMode) => {
    setViewMode(nextViewMode)
    try {
      window.localStorage.setItem(VIEW_MODE_STORAGE_KEY, nextViewMode)
    } catch {
      showError('No se pudo guardar la preferencia de vista en este navegador.')
    }
  }

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(nextTheme)
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme)
    } catch {
      showError('No se pudo guardar la preferencia de tema en este navegador.')
    }
  }

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

  const handleDelete = (book) => setDeleteBookCandidate(book)

  const confirmDeleteBook = async () => {
    if (!deleteBookCandidate) return
    const book = deleteBookCandidate
    setPendingAction(`delete-${book.id}`)
    try {
      await deleteBook(book.id)
      showSuccess('Libro eliminado del inventario.')
      const remainingOnPage = (booksPage?.results.length || 1) - 1
      const targetPage = remainingOnPage === 0 && page > 1 ? page - 1 : page
      setDeleteBookCandidate(null)
      await loadBooks(targetPage, activeFilter)
    } catch (error) {
      showError(error.message || 'No se pudo eliminar el libro.')
      setDeleteBookCandidate(null)
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

  const applySearchFilter = (event) => {
    event.preventDefault()
    const title = filter.title.trim()
    const category = filter.category.trim()
    if (!title && !category) {
      showError('Escribe un nombre, una categoría o ambos para buscar.')
      return
    }
    setFilter((current) => ({ ...current, title, category }))
    setLoading(true)
    setActiveFilter({ type: 'search', title, category, threshold: filter.threshold })
  }

  const applyLowStockFilter = (event) => {
    event.preventDefault()
    if (!/^\d+$/.test(filter.threshold.trim())) {
      showError('El umbral debe ser un entero igual o mayor que cero.')
      return
    }
    const threshold = filter.threshold.trim()
    setFilter({ title: '', category: '', threshold })
    setActiveFilter({ type: 'low-stock', title: '', category: '', threshold })
    setLoading(true)
  }

  const clearFilters = () => {
    setLoading(true)
    setFilter({ title: '', category: '', threshold: '10' })
    setActiveFilter({ type: 'all', title: '', category: '', threshold: '10' })
  }

  const handlePageChange = (url) => {
    if (!url) return
    const nextPage = Number(new URL(url, window.location.origin).searchParams.get('page') || 1)
    loadBooks(nextPage, activeFilter)
  }

  const count = booksPage?.count || 0
  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE))
  const visiblePageCount = Math.min(5, totalPages)
  const firstVisiblePage = Math.min(
    Math.max(page - Math.floor(visiblePageCount / 2), 1),
    totalPages - visiblePageCount + 1,
  )
  const visiblePages = Array.from(
    { length: visiblePageCount },
    (_, index) => firstVisiblePage + index,
  )
  const rangeStart = count === 0 ? 0 : (page - 1) * PAGE_SIZE + 1
  const rangeEnd = Math.min(page * PAGE_SIZE, count)
  const title = activeFilter.type === 'search'
    ? 'Resultados de búsqueda'
    : activeFilter.type === 'low-stock'
      ? 'Libros con stock bajo'
      : 'Todos los libros'

  return (
    <div className="app-shell" data-theme={theme}>
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="Bookwise, inicio">
          <span className="brand-mark">b</span>
          <span>bookwise<span className="brand-period">.</span></span>
        </a>
        <div className="sidebar-label">GESTIÓN</div>
        <button className="nav-item nav-item-active" type="button">
          <Icon name="inventory" className="nav-icon" />
          Inventario
        </button>
        <div className="sidebar-note">
          <Icon name="sparkle" className="note-icon" />
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
            <button
              className="theme-switch"
              type="button"
              role="switch"
              aria-checked={theme === 'dark'}
              aria-label={theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
              title={theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
              onClick={toggleTheme}
            >
              <Icon name={theme === 'dark' ? 'moon' : 'sun'} size={16} className="theme-switch-icon" />
              <span className="theme-switch-track"><span /></span>
            </button>
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
              <Icon name="plus" className="button-plus" /> Agregar libro
            </button>
          </section>

          <section className="summary-grid" aria-label="Resumen del inventario">
            <article className="summary-card">
              <div className="summary-top"><span className="summary-label">TÍTULOS EN INVENTARIO</span><span className="summary-icon icon-books"><Icon name="books" /></span></div>
              <strong className="summary-value">{loading && !booksPage ? '—' : count}</strong>
              <span className="summary-caption">en esta consulta</span>
            </article>
            <article className="summary-card summary-card-highlight">
              <div className="summary-top"><span className="summary-label">VISTA ACTUAL</span><span className="summary-icon icon-view"><Icon name="view" /></span></div>
              <strong className="summary-value summary-value-small">{activeFilter.type === 'all' ? 'Completa' : activeFilter.type === 'search' ? 'Búsqueda' : 'Stock bajo'}</strong>
              <span className="summary-caption">{loading ? 'Actualizando resultados…' : 'Datos sincronizados con la API'}</span>
            </article>
            <article className="summary-card summary-card-accent">
              <div className="summary-top"><span className="summary-label">PÁGINA</span><span className="summary-icon icon-page"><Icon name="arrow-up-right" /></span></div>
              <strong className="summary-value">{booksPage ? `${page}` : '—'}<small className="page-total"> / {totalPages}</small></strong>
              <span className="summary-caption">10 libros por página</span>
            </article>
          </section>

          <section className="filter-panel" aria-label="Filtros del inventario">
            <div className="filter-panel-heading">
              <div><span className="filter-icon"><Icon name="search" size={19} /></span><div><h2>Encuentra un libro</h2><p>Busca por nombre, categoría o combina ambos filtros.</p></div></div>
              {activeFilter.type !== 'all' && <button className="text-button" type="button" onClick={clearFilters}>Limpiar filtros <Icon name="close" size={15} /></button>}
            </div>
            <div className="filter-controls">
              <form className="filter-form search-form" onSubmit={applySearchFilter}>
                <div className="search-fields">
                  <label htmlFor="title-filter">Nombre del libro
                    <input id="title-filter" value={filter.title} onChange={(event) => setFilter((current) => ({ ...current, title: event.target.value }))} placeholder="Ej. Cien años de soledad" />
                  </label>
                  <label htmlFor="category-filter">Categoría
                    <input id="category-filter" value={filter.category} onChange={(event) => setFilter((current) => ({ ...current, category: event.target.value }))} placeholder="Ej. Literatura" />
                  </label>
                </div>
                <button className="button button-primary search-submit" type="submit">Buscar libros</button>
              </form>
              <div className="filter-divider" />
              <form className="filter-form stock-form" onSubmit={applyLowStockFilter}>
                <label htmlFor="threshold-filter">Stock bajo · umbral</label>
                <div className="input-button-row">
                  <input id="threshold-filter" type="number" min="0" step="1" value={filter.threshold} onChange={(event) => setFilter((current) => ({ ...current, threshold: event.target.value }))} />
                  <button className="button button-outline" type="submit"><Icon name="filter" size={16} /> Ver stock bajo</button>
                </div>
              </form>
            </div>
          </section>

          <section className="inventory-panel">
            <div className="inventory-heading">
              <div><h2>{title}</h2><p>{count === 1 ? '1 libro encontrado' : `${count} libros encontrados`}</p></div>
              <div className="inventory-heading-tools">
                <div className="view-toggle" role="group" aria-label="Modo de visualización">
                  <button
                    className={`view-toggle-button${viewMode === 'cards' ? ' view-toggle-button-active' : ''}`}
                    type="button"
                    aria-label="Vista de tarjetas"
                    aria-pressed={viewMode === 'cards'}
                    onClick={() => changeViewMode('cards')}
                  >
                    <Icon name="grid" size={15} /><span>Tarjetas</span>
                  </button>
                  <button
                    className={`view-toggle-button${viewMode === 'table' ? ' view-toggle-button-active' : ''}`}
                    type="button"
                    aria-label="Vista de tabla"
                    aria-pressed={viewMode === 'table'}
                    onClick={() => changeViewMode('table')}
                  >
                    <Icon name="table" size={15} /><span>Tabla</span>
                  </button>
                </div>
                <div className="table-meta"><span className="live-dot" /> Actualizado en tiempo real</div>
              </div>
            </div>

            {loadError && (
              <div className="inline-error" role="alert">
                <Icon name="alert" className="inline-error-icon" size={20} /><div><strong>No se pudo cargar el inventario</strong><p>{loadError}</p></div>
                <button className="button button-outline" type="button" onClick={() => loadBooks(page, activeFilter)}>Reintentar</button>
              </div>
            )}

            {viewMode === 'cards' ? (
              <BookCards
                books={booksPage?.results || []}
                loading={loading}
                error={loadError}
                pendingAction={pendingAction}
                onEdit={openEditForm}
                onDelete={handleDelete}
                onCalculate={handleCalculatePrice}
                onViewDetails={setDetailsBook}
                onAddBook={openCreateForm}
              />
            ) : (
              <BookTable
                books={booksPage?.results || []}
                loading={loading}
                error={loadError}
                pendingAction={pendingAction}
                onEdit={openEditForm}
                onDelete={handleDelete}
                onCalculate={handleCalculatePrice}
                onViewDetails={setDetailsBook}
                onAddBook={openCreateForm}
              />
            )}

            <div className="table-footer">
              <span>Mostrando <strong>{rangeStart}–{rangeEnd}</strong> de <strong>{count}</strong> libros</span>
              <div className="pagination">
                <button type="button" className="pagination-button" aria-label="Página anterior" disabled={!booksPage?.previous || loading} onClick={() => handlePageChange(booksPage.previous)}><Icon name="arrow-left" size={15} /></button>
                {visiblePages.map((pageNumber) => (
                  <button
                    key={pageNumber}
                    type="button"
                    className={`pagination-page${pageNumber === page ? ' pagination-page-active' : ''}`}
                    aria-label={`Página ${pageNumber}`}
                    aria-current={pageNumber === page ? 'page' : undefined}
                    disabled={loading || pageNumber === page}
                    onClick={() => loadBooks(pageNumber, activeFilter)}
                  >
                    {pageNumber}
                  </button>
                ))}
                <button type="button" className="pagination-button" aria-label="Página siguiente" disabled={!booksPage?.next || loading} onClick={() => handlePageChange(booksPage.next)}><Icon name="arrow-right" size={15} /></button>
              </div>
            </div>
          </section>

          <footer className="page-footer"><span>BOOKWISE INVENTORY</span><span>Hecho para cuidar cada historia.</span></footer>
        </div>
      </main>

      <Modal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        closeDisabled={formLoading}
        labelledBy="book-form-title"
      >
        <BookForm
          book={formBook}
          loading={formLoading}
          error={formError}
          onSubmit={handleFormSubmit}
          onCancel={() => setFormOpen(false)}
        />
      </Modal>

      <Modal
        open={Boolean(priceResult)}
        onClose={() => setPriceResult(null)}
        className="price-modal"
        labelledBy="price-result-title"
      >
        {priceResult && <PriceResult result={priceResult} onClose={() => setPriceResult(null)} />}
      </Modal>

      <Modal
        open={Boolean(detailsBook)}
        onClose={closeBookDetails}
        className="book-details-modal"
        labelledBy="book-details-title"
      >
        {detailsBook && <BookDetails book={detailsBook} onClose={closeBookDetails} />}
      </Modal>

      <Modal
        open={Boolean(deleteBookCandidate)}
        onClose={() => setDeleteBookCandidate(null)}
        className="delete-confirmation-modal"
        role="alertdialog"
        labelledBy="delete-confirmation-title"
        describedBy="delete-confirmation-description"
        closeDisabled={Boolean(pendingAction)}
      >
        {deleteBookCandidate && (
          <>
            <div className="delete-confirmation-content">
              <span className="delete-confirmation-icon"><Icon name="trash" size={21} /></span>
              <div>
                <h2 id="delete-confirmation-title">¿Eliminar este libro?</h2>
                <p id="delete-confirmation-description">
                  Se eliminará <strong>{deleteBookCandidate.title}</strong> del inventario. Esta acción no se puede deshacer.
                </p>
              </div>
            </div>
            <div className="modal-actions">
              <button
                className="button button-outline"
                type="button"
                autoFocus
                disabled={pendingAction === `delete-${deleteBookCandidate.id}`}
                onClick={() => setDeleteBookCandidate(null)}
              >
                Cancelar
              </button>
              <button
                className="button button-danger"
                type="button"
                disabled={pendingAction === `delete-${deleteBookCandidate.id}`}
                onClick={confirmDeleteBook}
              >
                {pendingAction === `delete-${deleteBookCandidate.id}` ? 'Eliminando…' : 'Eliminar libro'}
              </button>
            </div>
          </>
        )}
      </Modal>

      {notification && (
        <div className={`toast toast-${notification.type}`} role={notification.type === 'error' ? 'alert' : 'status'}>
          <span className="toast-mark"><Icon name={notification.type === 'success' ? 'check' : 'alert'} size={15} /></span>
          {notification.message}
          <button type="button" aria-label="Cerrar notificación" onClick={() => setNotification(null)}><Icon name="close" size={16} /></button>
        </div>
      )}
    </div>
  )
}

export default App
