export function PageHeader({ eyebrow, title, subtitle, actions }) {
  return (
    <section className="page-header">
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <h1>{title}</h1>
      {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
      {actions ? <div className="page-header-actions">{actions}</div> : null}
    </section>
  )
}