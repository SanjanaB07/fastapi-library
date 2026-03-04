import { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import StatsCard from '../components/StatsCard.jsx'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const s = await api.getStats()
        setStats(s)
      } catch {
        setError('Failed to load')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <div>Loading…</div>
  if (error) return <div>{error}</div>

  const perAuthor = (stats.books_per_author || []).slice(0, 5).map(x => `${x.name} (${x.count})`).join(', ') || 'None'
  const perCategory = (stats.books_per_category || []).slice(0, 5).map(x => `${x.name} (${x.count})`).join(', ') || 'None'

  return (
    <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(2, minmax(220px, 1fr))' }}>
      <StatsCard title="Total books" value={stats.total_books} />
      <StatsCard title="Average publication year" value={stats.average_year ?? 'N/A'} />
      <StatsCard title="Books per author (top 5)" value={perAuthor} />
      <StatsCard title="Books per category (top 5)" value={perCategory} />
    </div>
  )
}
