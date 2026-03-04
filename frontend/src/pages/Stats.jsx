import { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import StatsCard from '../components/StatsCard.jsx'

export default function Stats() {
  const [stats, setStats] = useState(null)
  const [authors, setAuthors] = useState([])
  const [selected, setSelected] = useState('')
  const [authorStats, setAuthorStats] = useState(null)
  const [authorHas, setAuthorHas] = useState(null)
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('')
  const [categoryChecks, setCategoryChecks] = useState(null)

  useEffect(() => {
    async function load() {
      const [s, a, c] = await Promise.all([api.getStats(), api.getAuthors(), api.getCategories()])
      setStats(s)
      setAuthors(a)
      setCategories(c)
    }
    load()
  }, [])

  useEffect(() => {
    async function run() {
      if (!selected) {
        setAuthorStats(null)
        setAuthorHas(null)
        return
      }
      const s = await api.authorEarliestLatest(Number(selected))
      setAuthorStats(s)
      const has = await api.authorHasBooks(Number(selected))
      setAuthorHas(has)
    }
    run()
  }, [selected])

  useEffect(() => {
    async function run() {
      if (!selectedCategory) {
        setCategoryChecks(null)
        return
      }
      const id = Number(selectedCategory)
      const [has, allYear] = await Promise.all([api.categoryHasBooks(id), api.categoryAllHaveYear(id)])
      setCategoryChecks({ has, allYear })
    }
    run()
  }, [selectedCategory])

  if (!stats) return <div>Loading…</div>

  const atLeastOneBook = stats.total_books > 0 ? 'Yes' : 'No'

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(2, minmax(220px, 1fr))' }}>
        <StatsCard title="Total books" value={stats.total_books} />
        <StatsCard title="Average year" value={stats.average_year ?? 'N/A'} />
        <StatsCard title="At least one book?" value={atLeastOneBook} />
        <StatsCard title="Distinct authors" value={(stats.books_per_author || []).length} />
      </div>
      <div>
        <h3>Author earliest/latest</h3>
        <select value={selected} onChange={e => setSelected(e.target.value)}>
          <option value="">Select author</option>
          {authors.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
        {authorStats && (
          <div style={{ marginTop: 8 }}>
            <div>Earliest: {authorStats.earliest ? `${authorStats.earliest.title} (${authorStats.earliest.year || '-'})` : 'None'}</div>
            <div>Latest: {authorStats.latest ? `${authorStats.latest.title} (${authorStats.latest.year || '-'})` : 'None'}</div>
          </div>
        )}
        {authorHas && (
          <div style={{ marginTop: 8 }}>
            <div>Selected author has at least one book? {authorHas.has_books ? 'Yes' : 'No'} (count {authorHas.count})</div>
          </div>
        )}
      </div>
      <div>
        <h3>Category checks</h3>
        <select value={selectedCategory} onChange={e => setSelectedCategory(e.target.value)}>
          <option value="">Select category</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        {categoryChecks && (
          <div style={{ marginTop: 8 }}>
            <div>Category has at least one book? {categoryChecks.has.has_books ? 'Yes' : 'No'} (count {categoryChecks.has.count})</div>
            <div>Do all books in this category have a year? {categoryChecks.allYear.all_have_year ? 'Yes' : 'No'} (missing {categoryChecks.allYear.missing})</div>
          </div>
        )}
      </div>
      <div>
        <h3>Books per author</h3>
        <ul>
          {(stats.books_per_author || []).map(x => <li key={x.name}>{x.name}: {x.count}</li>)}
        </ul>
      </div>
      <div>
        <h3>Books per category</h3>
        <ul>
          {(stats.books_per_category || []).map(x => <li key={x.name}>{x.name}: {x.count}</li>)}
        </ul>
      </div>
    </div>
  )
}
