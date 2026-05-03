import { Link } from 'react-router-dom'

import { PageHeader } from '../components/PageHeader'

export function NotFoundPage() {
  return (
    <main className="page page-not-found">
      <PageHeader
        eyebrow="404"
        title="This page was not found"
        subtitle="The route might have changed, or the page was removed."
      />
      <section className="panel">
        <Link to="/" className="button">
          Back to shop
        </Link>
      </section>
    </main>
  )
}