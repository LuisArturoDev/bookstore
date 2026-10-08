import { useEffect, useState } from 'react'
import Icon from './Icon.jsx'

const emptyForm = {
  title: '',
  author: '',
  isbn: '',
  cost_usd: '',
  stock_quantity: '0',
  category: '',
  supplier_country: '',
}

const CHARACTER_LIMITS = {
  title: 150,
  author: 100,
  isbn: 25,
  category: 50,
}

function getIsbnError(value) {
  const isbn = value.replace(/[\s-]/g, '').toUpperCase()

  if (/^\d{13}$/.test(isbn)) {
    const errors = []
    if (!isbn.startsWith('978') && !isbn.startsWith('979')) {
      errors.push('Un ISBN-13 debe comenzar con 978 o 979.')
    }
    const checksum = [...isbn].reduce(
      (sum, digit, index) => sum + Number(digit) * (index % 2 === 0 ? 1 : 3),
      0,
    )
    if (checksum % 10 !== 0) {
      errors.push('El dígito de control del ISBN-13 no es válido.')
    }
    return errors.join(' ')
  }

  if (/^\d{9}[\dX]$/.test(isbn)) {
    const checksum = [...isbn].reduce(
      (sum, digit, index) => sum + (digit === 'X' ? 10 : Number(digit)) * (10 - index),
      0,
    )
    return checksum % 11 === 0 ? '' : 'El dígito de control del ISBN-10 no es válido.'
  }

  return 'Introduce un ISBN-10 de 10 dígitos o un ISBN-13 de 13 dígitos.'
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
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(book?.image || '')
  const [removeImage, setRemoveImage] = useState(false)
  const [isbnError, setIsbnError] = useState('')

  useEffect(() => {
    return () => {
      if (imagePreview.startsWith('blob:')) URL.revokeObjectURL(imagePreview)
    }
  }, [imagePreview])

  const updateField = (event) => {
    const { name, value } = event.target
    if (name === 'isbn') setIsbnError('')
    setForm((current) => ({
      ...current,
      [name]: name === 'supplier_country'
        ? value.toUpperCase().slice(0, 2)
        : value.slice(0, CHARACTER_LIMITS[name] || value.length),
    }))
  }

  const updateImage = (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    setImageFile(file)
    setRemoveImage(false)
    setImagePreview(URL.createObjectURL(file))
  }

  const clearImage = () => {
    if (imageFile) {
      setImageFile(null)
      setImagePreview(book?.image || '')
      return
    }
    setRemoveImage(true)
    setImagePreview('')
  }

  const submit = (event) => {
    event.preventDefault()
    const validationError = getIsbnError(form.isbn)
    if (validationError) {
      setIsbnError(validationError)
      return
    }

    const formData = new FormData()
    formData.append('title', form.title)
    formData.append('author', form.author)
    formData.append('isbn', form.isbn)
    formData.append('cost_usd', Number(form.cost_usd).toFixed(2))
    formData.append('stock_quantity', String(Number(form.stock_quantity)))
    formData.append('category', form.category)
    formData.append('supplier_country', form.supplier_country.trim().toUpperCase())
    if (imageFile) formData.append('image', imageFile)
    if (removeImage) formData.append('remove_image', 'true')
    onSubmit(formData)
  }

  return (
    <form className="book-form" onSubmit={submit}>
      <div className="modal-heading">
        <div><span className="eyebrow"><span className="eyebrow-line" /> INVENTARIO</span><h2 id="book-form-title">{book ? 'Editar libro' : 'Agregar un libro'}</h2><p>{book ? 'Actualiza la información del título.' : 'Completa los datos para añadirlo a tu colección.'}</p></div>
        <button className="icon-button modal-close" type="button" aria-label="Cerrar formulario" onClick={onCancel} disabled={loading}><Icon name="close" /></button>
      </div>

      {error && <div className="form-error" role="alert"><Icon name="alert" size={18} /><span>{error}</span></div>}

      <div className="form-grid">
        <label className="form-field form-field-wide">
          <span>Título <b>*</b></span>
          <input autoFocus name="title" value={form.title} onChange={updateField} required maxLength="150" placeholder="Nombre del libro" />
          <small>Máximo 150 caracteres.</small>
        </label>
        <div className="form-field form-field-wide">
          <span>Portada del libro <small>(opcional)</small></span>
          <div className="image-upload-control">
            <div className={`image-upload-preview${imagePreview ? ' image-upload-preview-image' : ''}`}>
              {imagePreview
                ? <><span>{form.title.trim().split(/\s+/).slice(0, 2).map((word) => word[0]).join('').toUpperCase() || 'L'}</span><img src={imagePreview} alt="" onError={(event) => { event.currentTarget.hidden = true }} /></>
                : <span>{form.title.trim().split(/\s+/).slice(0, 2).map((word) => word[0]).join('').toUpperCase() || 'L'}</span>}
            </div>
            <div className="image-upload-details">
              <label className="button button-outline image-upload-button">
                {imageFile ? 'Cambiar imagen' : imagePreview ? 'Reemplazar imagen' : 'Elegir imagen'}
                <input type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={updateImage} />
              </label>
              <small>{imageFile?.name || (book?.image ? 'Se conserva la portada actual si no eliges otra.' : 'JPG, PNG o WebP · máximo 5 MB')}</small>
              {(imageFile || (book?.image && !removeImage)) && (
                <button className="image-remove-button" type="button" onClick={clearImage}>
                  {imageFile ? 'Quitar selección' : 'Quitar portada'}
                </button>
              )}
            </div>
          </div>
        </div>
        <label className="form-field">
          <span>Autor <b>*</b></span>
          <input name="author" value={form.author} onChange={updateField} required maxLength="100" placeholder="Nombre del autor" />
          <small>Máximo 100 caracteres.</small>
        </label>
        <label className="form-field">
          <span>ISBN <b>*</b></span>
          <input
            name="isbn"
            value={form.isbn}
            onChange={updateField}
            onBlur={(event) => setIsbnError(getIsbnError(event.target.value))}
            required
            maxLength="25"
            placeholder="978-0-306-40615-7"
            aria-invalid={Boolean(isbnError)}
            aria-describedby="isbn-hint"
          />
          <small id="isbn-hint" className={isbnError ? 'field-validation-error' : ''} role={isbnError ? 'alert' : undefined}>
            {isbnError || 'ISBN-10 o ISBN-13, con o sin guiones.'}
          </small>
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
          <input name="category" value={form.category} onChange={updateField} required maxLength="50" placeholder="Ej. Narrativa" />
          <small>Máximo 50 caracteres.</small>
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
