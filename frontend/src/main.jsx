import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import NotFoundPage from './components/NotFoundPage.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {window.location.pathname === '/' || window.location.pathname === '/index.html'
      ? <App />
      : <NotFoundPage path={window.location.pathname} />}
  </StrictMode>,
)

if (window.location.pathname !== '/' && window.location.pathname !== '/index.html') {
  document.title = 'Página no encontrada · Bookwise'
}
