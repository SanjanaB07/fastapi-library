import { useEffect, useState } from 'react'
import { api } from '../services/api.js'

export default function Filters({ value, onChange }) {
  const [authors, setAuthors] = useState([])
  const [categories, setCategories] = useState([])

  useEffect(() => {
    async function load() {
      const [a, c] = await Promise.all([api.getAuthors(), api.getCategories()])
      setAuthors(a)
      setCategories(c)
    }
    load()
  }, [])

  function update(k, v) {
    onChange({ ...value, [k]: v })
  }

  return (
    <div style={{ display: 'grid', gap: 8, gridTemplateColumns: 'repeat(5, minmax(160px, 1fr))', marginBottom: 12 }}>
      <select value={value.author_id ?? ''} onChange={(e) => update('author_id', e.target.value ? Number(e.target.value) : undefined)}>
        <option value="">Author</option>
        {authors.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
      </select>
      <select value={value.category_id ?? ''} onChange={(e) => update('category_id', e.target.value ? Number(e.target.value) : undefined)}>
        <option value="">Category</option>
        {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>
      <input type="number" placeholder="Year" value={value.year ?? ''} onChange={(e) => update('year', e.target.value ? Number(e.target.value) : undefined)} />
      <input type="number" placeholder="Year min" value={value.year_min ?? ''} onChange={(e) => update('year_min', e.target.value ? Number(e.target.value) : undefined)} />
      <input type="number" placeholder="Year max" value={value.year_max ?? ''} onChange={(e) => update('year_max', e.target.value ? Number(e.target.value) : undefined)} />
      <input type="number" placeholder="Limit" value={value.limit ?? ''} onChange={(e) => update('limit', e.target.value ? Number(e.target.value) : undefined)} />
      <select value={value.sort ?? ''} onChange={(e) => update('sort', e.target.value || undefined)}>
        <option value="">Sort</option>
        <option value="title_asc">Title A–Z</option>
      </select>
    </div>
  )
}
