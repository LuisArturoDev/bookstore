import BookActions from './BookActions.jsx'
import BookCover from './BookCover.jsx'
import Icon from './Icon.jsx'

function formatMoney(value, currency = 'EUR') {
  if (value === null || value === undefined || value === '') return '—'
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(Number(value))
}

function BookCards({ books, loading, error, pendingAction, onEdit, onDelete, onCalculate, onViewDetails, onAddBook }) {
  const openDetailsOnKeyDown = (event, book) => {
    if (event.target !== event.currentTarget) return
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onViewDetails(book)
    }
  }

  if (loading && books.length === 0) {
    return (
      <div className="book-card-grid book-card-grid-skeleton" role="status" aria-label="Cargando libros">
        {Array.from({ length: 6 }, (_, index) => (
          <article className="book-card book-card-skeleton" key={index} aria-hidden="true">
            <div className="book-card-top">
              <span className="skeleton skeleton-cover" />
              <span className="book-card-skeleton-title">
                <span className="skeleton skeleton-line skeleton-title-line" />
                <span className="skeleton skeleton-line skeleton-author-line" />
              </span>
            </div>
            <span className="skeleton skeleton-chip" />
            <div className="book-card-skeleton-details">
              <span className="skeleton skeleton-line" />
              <span className="skeleton skeleton-line skeleton-short-line" />
              <span className="skeleton skeleton-line" />
              <span className="skeleton skeleton-line skeleton-short-line" />
            </div>
            <div className="book-card-skeleton-footer">
              <span className="skeleton skeleton-chip" />
              <span className="skeleton skeleton-actions" />
            </div>
          </article>
        ))}
      </div>
    )
  }

  if (error && books.length === 0) return null

  if (!loading && books.length === 0) {
    return (
      <div className="table-state empty-state">
        <span className="empty-icon"><Icon name="books" size={21} /></span>
        <strong>No hay libros en esta vista</strong>
        <span>Prueba con otro filtro o agrega un título al inventario.</span>
        <button className="button button-outline" type="button" onClick={onAddBook}>Agregar primer libro</button>
      </div>
    )
  }

  return (
    <div className={`book-card-grid${loading ? ' book-card-grid-loading' : ''}`}>
      {books.map((book) => (
        <article
          className="book-card book-card-clickable"
          key={book.id}
          tabIndex={0}
          aria-label={`Ver detalles de ${book.title}`}
          onClick={(event) => {
            if (!event.target.closest('button, a, input, select, textarea')) onViewDetails(book)
          }}
          onKeyDown={(event) => openDetailsOnKeyDown(event, book)}
        >
          <div className="book-card-top">
            <BookCover book={book} />
            <span className="book-card-title">
              <strong>{book.title}</strong>
              <small>{book.author}</small>
            </span>
          </div>
          <div className="book-card-tags">
            <span className="category-chip">{book.category}</span>
            <span className="book-card-isbn">{book.isbn}</span>
          </div>
          <dl className="book-card-details">
            <div><dt>Costo</dt><dd>{formatMoney(book.cost_usd, 'USD')}</dd></div>
            <div><dt>Precio sugerido</dt><dd className="selling-price">{formatMoney(book.selling_price_local)}</dd></div>
          </dl>
          <div className="book-card-footer">
            <span className={`stock-pill ${book.stock_quantity === 0 ? 'stock-empty' : book.stock_quantity <= 10 ? 'stock-low' : 'stock-good'}`}>
              <i />{book.stock_quantity} {book.stock_quantity === 1 ? 'unidad' : 'unidades'}
            </span>
            <BookActions
              book={book}
              pendingAction={pendingAction}
              onEdit={onEdit}
              onDelete={onDelete}
              onCalculate={onCalculate}
            />
          </div>
        </article>
      ))}
    </div>
  )
}

export default BookCards
