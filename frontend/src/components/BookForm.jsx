import { useState } from 'react'

const emptyForm = {
  title: '',
  author: '',
  isbn: '',
  cost_usd: '',
  stock_quantity: '0',
  category: '',
  supplier_country: '',
}

function BookForm({ book, loading, error, onSubmit, onCancel }) {
  const [form, setForm] = useState(book ? {
    title: book.title,
    author: book.author,
    isbn: book.isbn,
    cost_usd: book.cost_usd,
    stock_quantity: String(book.stock_quantity),
    category: book.category,
    supplier_country: book.supplier_country,
  } : emptyForm)

  const updateField = (event) => {
    const { name, value } = event.target
    setForm((current) => ({
      ...current,
      [name]: name === 'supplier_country' ? value.toUpperCase().slice(0, 2) : value,
    }))
  }

  const submit = (event) => {
    event.preventDefault()
    onSubmit({
      ...form,
      cost_usd: Number(form.cost_usd).toFixed(2),
      stock_quantity: Number(form.stock_quantity),
      supplier_country: form.supplier_country.trim().toUpperCase(),
    })
  }

  return (
    <form className="book-form" onSubmit={submit}>
      <div className="modal-heading">
        <div><span className="eyebrow"><span className="eyebrow-line" /> INVENTARIO</span><h2 id="book-form-title">{book ? 'Editar libro' : 'Agregar un libro'}</h2><p>{book ? 'Actualiza la información del título.' : 'Completa los datos para añadirlo a tu colección.'}</p></div>
        <button className="icon-button modal-close" type="button" aria-label="Cerrar formulario" onClick={onCancel} disabled={loading}>×</button>
      </div>

      {error && <div className="form-error" role="alert"><span>!</span>{error}</div>}

      <div className="form-grid">
        <label className="form-field form-field-wide">
          <span>Título <b>*</b></span>
          <input autoFocus name="title" value={form.title} onChange={updateField} required maxLength="255" placeholder="Nombre del libro" />
        </label>
        <label className="form-field">
          <span>Autor <b>*</b></span>
          <input name="author" value={form.author} onChange={updateField} required maxLength="255" placeholder="Nombre del autor" />
        </label>
        <label className="form-field">
          <span>ISBN <b>*</b></span>
          <input name="isbn" value={form.isbn} onChange={updateField} required maxLength="25" placeholder="978-0-306-40615-7" />
          <small>ISBN-10 o ISBN-13, con o sin guiones.</small>
        </label>
        <label className="form-field">
          <span>Costo (USD) <b>*</b></span>
          <div className="field-prefix"><span>$</span><input name="cost_usd" type="number" min="0.01" step="0.01" value={form.cost_usd} onChange={updateField} required placeholder="0.00" /></div>
        </label>
        <label className="form-field">
          <span>Existencias <b>*</b></span>
          <input name="stock_quantity" type="number" min="0" step="1" value={form.stock_quantity} onChange={updateField} required />
        </label>
        <label className="form-field">
          <span>Categoría <b>*</b></span>
          <input name="category" value={form.category} onChange={updateField} required maxLength="100" placeholder="Ej. Narrativa" />
        </label>
        <label className="form-field">
          <span>País proveedor <b>*</b></span>
          <input name="supplier_country" value={form.supplier_country} onChange={updateField} required minLength="2" maxLength="2" pattern="[A-Z]{2}" title="Usa el código ISO de dos letras, por ejemplo ES." placeholder="ES" />
          <small>Código de país ISO de dos letras.</small>
        </label>
      </div>

      <div className="modal-actions">
        <button className="button button-quiet" type="button" onClick={onCancel} disabled={loading}>Cancelar</button>
        <button className="button button-primary" type="submit" disabled={loading}>
          {loading ? <><span className="spinner spinner-light" /> Guardando…</> : book ? 'Guardar cambios' : 'Agregar libro'}
        </button>
      </div>
    </form>
  )
}

export default BookForm
