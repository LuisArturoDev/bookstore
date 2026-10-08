import { useEffect, useRef } from 'react'
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

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('es-ES', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function BookDetails({ book, onClose }) {
  const closeButtonRef = useRef(null)

  useEffect(() => {
    closeButtonRef.current?.focus()
  }, [])

  return (
    <>
        <div className="modal-heading">
          <div>
            <span className="eyebrow"><span className="eyebrow-line" /> DETALLE DEL LIBRO</span>
            <h2 id="book-details-title">{book.title}</h2>
            <p>{book.author}</p>
          </div>
          <button ref={closeButtonRef} className="icon-button modal-close" type="button" aria-label="Cerrar detalles" onClick={onClose}><Icon name="close" /></button>
        </div>

        <div className="book-details-content">
          <BookCover book={book} />
          <dl className="book-details-grid">
            <div><dt>ISBN</dt><dd>{book.isbn || '—'}</dd></div>
            <div><dt>Categoría</dt><dd>{book.category || '—'}</dd></div>
            <div><dt>Costo</dt><dd>{formatMoney(book.cost_usd, 'USD')}</dd></div>
            <div><dt>Precio sugerido</dt><dd>{formatMoney(book.selling_price_local)}</dd></div>
            <div><dt>Existencias</dt><dd>{book.stock_quantity} {book.stock_quantity === 1 ? 'unidad' : 'unidades'}</dd></div>
            <div><dt>País proveedor</dt><dd>{book.supplier_country || '—'}</dd></div>
            <div><dt>Creado</dt><dd>{formatDate(book.created_at)}</dd></div>
            <div><dt>Última actualización</dt><dd>{formatDate(book.updated_at)}</dd></div>
          </dl>
        </div>
        <div className="modal-actions">
          <button className="button button-primary" type="button" onClick={onClose}>Cerrar</button>
        </div>
    </>
  )
}

export default BookDetails
