import { useCallback, useEffect, useState } from 'react'

function Modal({
  open,
  onClose,
  children,
  className = '',
  role = 'dialog',
  labelledBy,
  describedBy,
  closeDisabled = false,
}) {
  const [renderedChildren, setRenderedChildren] = useState(null)
  const [shouldRender, setShouldRender] = useState(open)
  const [closing, setClosing] = useState(false)

  const finishClosing = useCallback(() => {
    setShouldRender(false)
    setClosing(false)
    setRenderedChildren(null)
  }, [])

  useEffect(() => {
    if (!open) return
    const frameId = window.requestAnimationFrame(() => {
      setRenderedChildren(children)
      setShouldRender(true)
      setClosing(false)
    })
    return () => window.cancelAnimationFrame(frameId)
  }, [open, children])

  useEffect(() => {
    if (open || !shouldRender) return undefined

    let timeoutId
    const frameId = window.requestAnimationFrame(() => {
      setClosing(true)
      timeoutId = window.setTimeout(() => {
        finishClosing()
      }, 250)
    })

    return () => {
      window.cancelAnimationFrame(frameId)
      window.clearTimeout(timeoutId)
    }
  }, [open, shouldRender, finishClosing])

  useEffect(() => {
    if (!open || closeDisabled) return undefined

    const closeOnEscape = (event) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [open, onClose, closeDisabled])

  if (!shouldRender) return null

  return (
    <div
      className={`modal-backdrop${closing ? ' modal-closing' : ''}`}
      role="presentation"
      onAnimationEnd={(event) => {
        if (
          closing
          && event.target === event.currentTarget
          && event.animationName === 'modal-backdrop-out'
        ) {
          finishClosing()
        }
      }}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !closeDisabled) onClose()
      }}
    >
      <section
        className={`modal-card ${className}`.trim()}
        role={role}
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-describedby={describedBy}
      >
        {open ? children : renderedChildren}
      </section>
    </div>
  )
}

export default Modal
