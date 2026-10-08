function formatMoney(value, currency) {
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(Number(value))
}

function PriceResult({ result, onClose }) {
  return (
    <div className="price-result">
      <div className="modal-heading">
        <div><span className="eyebrow"><span className="eyebrow-line" /> CÁLCULO COMPLETADO</span><h2 id="price-result-title">Precio sugerido</h2><p>El precio se guardó en el inventario.</p></div>
        <button className="icon-button modal-close" type="button" aria-label="Cerrar resultado" onClick={onClose}>×</button>
      </div>
      <div className="price-highlight">
        <span>PRECIO DE VENTA</span>
        <strong>{formatMoney(result.selling_price_local, result.currency)}</strong>
        <small>Margen aplicado: {result.margin_percentage}%</small>
      </div>
      <dl className="calculation-details">
        <div><dt>Costo del libro</dt><dd>{formatMoney(result.cost_usd, 'USD')}</dd></div>
        <div><dt>Tasa de cambio</dt><dd>1 USD = {Number(result.exchange_rate).toLocaleString('es-ES', { maximumFractionDigits: 6 })} {result.currency}</dd></div>
        <div><dt>Costo convertido</dt><dd>{formatMoney(result.cost_local, result.currency)}</dd></div>
        <div><dt>Fuente de tasa</dt><dd>{result.used_fallback ? <span className="fallback-badge">Tasa de respaldo</span> : 'Tasa actual de API'}</dd></div>
      </dl>
      <div className="price-result-footer">
        <span>Calculado {new Date(result.calculation_timestamp).toLocaleString('es-ES')}</span>
        <button className="button button-primary" type="button" onClick={onClose}>Listo</button>
      </div>
    </div>
  )
}

export default PriceResult
