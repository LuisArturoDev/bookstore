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

function BookTable({ books, loading, error, pendingAction, onEdit, onDelete, onCalculate, onViewDetails, onAddBook }) {
  const openDetailsOnKeyDown = (event, book) => {
    if (event.target !== event.currentTarget) return
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onViewDetails(book)
    }
  }

  if (loading && books.length === 0) {
    return (
      <div className="table-wrap" role="status" aria-label="Cargando libros">
        <table className="book-table-skeleton">
          <thead>
            <tr><th>LIBRO</th><th>ISBN</th><th>CATEGORÍA</th><th>COSTO</th><th>PRECIO SUGERIDO</th><th>STOCK</th><th>ACCIONES</th></tr>
          </thead>
          <tbody>
            {Array.from({ length: 6 }, (_, index) => (
              <tr key={index} aria-hidden="true">
                <td><span className="skeleton skeleton-table-book" /></td>
                <td><span className="skeleton skeleton-line skeleton-table-isbn" /></td>
                <td><span className="skeleton skeleton-chip" /></td>
                <td><span className="skeleton skeleton-line skeleton-table-price" /></td>
                <td><span className="skeleton skeleton-line skeleton-table-price" /></td>
                <td><span className="skeleton skeleton-chip" /></td>
                <td><span className="skeleton skeleton-actions" /></td>
              </tr>
            ))}
          </tbody>
        </table>
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
    <div className={`table-wrap ${loading ? 'table-loading' : ''}`}>
      <table>
        <thead>
          <tr>
            <th>LIBRO</th>
            <th>ISBN</th>
            <th>CATEGORÍA</th>
            <th>COSTO</th>
            <th>PRECIO SUGERIDO</th>
            <th>STOCK</th>
            <th>ACCIONES</th>
          </tr>
        </thead>
        <tbody>
          {books.map((book) => (
              <tr
                key={book.id}
                className="book-row-clickable"
                tabIndex={0}
                aria-label={`Ver detalles de ${book.title}`}
                onClick={(event) => {
                  if (!event.target.closest('button, a, input, select, textarea')) onViewDetails(book)
                }}
                onKeyDown={(event) => openDetailsOnKeyDown(event, book)}
              >
                <td>
                  <div className="book-cell">
                    <BookCover book={book} />
                    <span className="book-name"><strong>{book.title}</strong><small>{book.author}</small></span>
                  </div>
                </td>
                <td className="isbn-cell">{book.isbn}</td>
                <td><span className="category-chip">{book.category}</span></td>
                <td className="money-cell">{formatMoney(book.cost_usd, 'USD')}</td>
                <td className="money-cell selling-price">{formatMoney(book.selling_price_local)}</td>
                <td><span className={`stock-pill ${book.stock_quantity === 0 ? 'stock-empty' : book.stock_quantity <= 10 ? 'stock-low' : 'stock-good'}`}><i />{book.stock_quantity} {book.stock_quantity === 1 ? 'unidad' : 'unidades'}</span></td>
                <td>
                  <BookActions
                    book={book}
                    pendingAction={pendingAction}
                    onEdit={onEdit}
                    onDelete={onDelete}
                    onCalculate={onCalculate}
                  />
                </td>
              </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default BookTable
