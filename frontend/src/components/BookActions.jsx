import Icon from './Icon.jsx'

function BookActions({ book, pendingAction, onEdit, onDelete, onCalculate }) {
  const isBusy = pendingAction === `delete-${book.id}` || pendingAction === `price-${book.id}`

  return (
    <div className="row-actions">
      <button className="icon-button action-calculate" type="button" title="Calcular precio de venta" aria-label={`Calcular precio para ${book.title}`} disabled={isBusy} onClick={() => onCalculate(book)}>
        {pendingAction === `price-${book.id}` ? <span className="spinner spinner-small" /> : <Icon name="arrow-up-right" />}
      </button>
      <button className="icon-button" type="button" title="Editar libro" aria-label={`Editar ${book.title}`} disabled={isBusy} onClick={() => onEdit(book)}><Icon name="edit" /></button>
      <button className="icon-button action-delete" type="button" title="Eliminar libro" aria-label={`Eliminar libro ${book.title}`} disabled={isBusy} onClick={() => onDelete(book)}>
        {pendingAction === `delete-${book.id}` ? <span className="spinner spinner-small" /> : <Icon name="trash" />}
      </button>
    </div>
  )
}

export default BookActions
