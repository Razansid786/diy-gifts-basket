import { classNames } from '../utils/format'

export function ToastTray({ toasts, onDismiss }) {
  return (
    <aside className="toast-tray" aria-live="polite" aria-atomic="true">
      {toasts.map((toast) => (
        <article
          key={toast.id}
          className={classNames('toast-card', `toast-${toast.type}`)}
          role="status"
        >
          <p>{toast.message}</p>
          <button
            type="button"
            onClick={() => onDismiss(toast.id)}
            aria-label="Dismiss notification"
          >
            Dismiss
          </button>
        </article>
      ))}
    </aside>
  )
}