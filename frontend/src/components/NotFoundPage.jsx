import './NotFoundPage.css'
import Icon from './Icon.jsx'

function NotFoundPage({ path }) {
  return (
    <main className="not-found-page">
      <a className="not-found-brand" href="/" aria-label="Bookwise, ir al inventario">
        <span className="not-found-brand-mark">b</span>
        <span>bookwise<span className="not-found-brand-period">.</span></span>
      </a>

      <section className="not-found-card" aria-labelledby="not-found-title">
        <div className="not-found-illustration" aria-hidden="true">
          <span className="not-found-book"><Icon name="books" size={38} /></span>
          <span className="not-found-spark not-found-spark-one"><Icon name="sparkle" size={16} /></span>
          <span className="not-found-spark not-found-spark-two"><Icon name="sparkle" size={12} /></span>
        </div>
        <p className="not-found-code">ERROR 404</p>
        <h1 id="not-found-title">Esta página no existe</h1>
        <p className="not-found-description">
          No encontramos la dirección que buscas. Puede que el enlace esté incompleto o que la página se haya movido.
        </p>
        <a className="not-found-link" href="/">
          <Icon name="arrow-left" size={16} />
          Volver al inventario
        </a>
        <p className="not-found-address">
          Dirección solicitada <code>{path}</code>
        </p>
      </section>

      <footer className="not-found-footer">BOOKWISE INVENTORY <span>·</span> Hecho para cuidar cada historia.</footer>
    </main>
  )
}

export default NotFoundPage
