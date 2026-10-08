function formatMoney(value, currency = 'EUR') {
  if (value === null || value === undefined || value === '') return '—'
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(Number(value))
}

function BookTable({ books, loading, error, pendingAction, onEdit, onDelete, onCalculate, onAddBook }) {
  if (loading && books.length === 0) {
    return <div className="table-state"><span className="spinner" /><strong>Cargando inventario…</strong><span>Consultando tus libros.</span></div>
  }

  if (error && books.length === 0) return null

  if (!loading && books.length === 0) {
    return (
      <div className="table-state empty-state">
        <span className="empty-icon">▤</span>
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
            <th><span className="sr-only">Acciones</span></th>
          </tr>
        </thead>
        <tbody>
          {books.map((book) => {
            const isBusy = pendingAction === `delete-${book.id}` || pendingAction === `price-${book.id}`
            return (
              <tr key={book.id}>
                <td>
                  <div className="book-cell">
                    <span className={`book-cover cover-${book.id % 5}`} aria-hidden="true"><span>{book.title.charAt(0).toUpperCase()}</span></span>
                    <span className="book-name"><strong>{book.title}</strong><small>{book.author}</small></span>
                  </div>
                </td>
                <td className="isbn-cell">{book.isbn}</td>
                <td><span className="category-chip">{book.category}</span></td>
                <td className="money-cell">{formatMoney(book.cost_usd, 'USD')}</td>
                <td className="money-cell selling-price">{formatMoney(book.selling_price_local)}</td>
                <td><span className={`stock-pill ${book.stock_quantity === 0 ? 'stock-empty' : book.stock_quantity <= 10 ? 'stock-low' : 'stock-good'}`}><i />{book.stock_quantity} {book.stock_quantity === 1 ? 'unidad' : 'unidades'}</span></td>
                <td>
                  <div className="row-actions">
                    <button className="icon-button action-calculate" type="button" title="Calcular precio de venta" aria-label={`Calcular precio para ${book.title}`} disabled={isBusy} onClick={() => onCalculate(book)}>
                      {pendingAction === `price-${book.id}` ? <span className="spinner spinner-small" /> : '↗'}
                    </button>
                    <button className="icon-button" type="button" title="Editar libro" aria-label={`Editar ${book.title}`} disabled={isBusy} onClick={() => onEdit(book)}>✎</button>
                    <button className="icon-button action-delete" type="button" title="Eliminar libro" aria-label={`Eliminar ${book.title}`} disabled={isBusy} onClick={() => onDelete(book)}>
                      {pendingAction === `delete-${book.id}` ? <span className="spinner spinner-small" /> : '⌫'}
                    </button>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default BookTable
