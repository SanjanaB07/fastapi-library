import { useEffect, useState } from 'react'
import { api } from '../services/api.js'

export default function BookForm({ initial, onSubmit, onCancel }) {
  const [title, setTitle] = useState(initial?.title || '')
  const [isbn, setIsbn] = useState(initial?.isbn || '')
  const [publication_year, setPublicationYear] = useState(initial?.publication_year || '')
  const [category_id, setCategoryId] = useState(initial?.category_id || '')
  const [author_ids, setAuthorIds] = useState(initial?.authors?.map(a => a.id) || [])
  const [authors, setAuthors] = useState([])
  const [categories, setCategories] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      const [a, c] = await Promise.all([api.getAuthors(), api.getCategories()])
      setAuthors(a)
      setCategories(c)
    }
    load()
  }, [])

  function submit(e) {
    e.preventDefault()
    setError('')
    if (!title.trim() || !isbn.trim()) {
      setError('Title and ISBN are required')
      return
    }
    const body = {
      title,
      isbn,
      publication_year: publication_year ? Number(publication_year) : undefined,
      category_id: category_id ? Number(category_id) : undefined,
      author_ids,
    }
    onSubmit(body)
  }

  function toggleAuthor(id) {
    setAuthorIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  return (
    <form onSubmit={submit} style={{ display: 'grid', gap: 8 }}>
      {error && <div style={{ color: 'orange' }}>{error}</div>}
      <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title" />
      <input value={isbn} onChange={e => setIsbn(e.target.value)} placeholder="ISBN" />
      <input type="number" value={publication_year} onChange={e => setPublicationYear(e.target.value)} placeholder="Publication Year" />
      <select value={category_id} onChange={e => setCategoryId(e.target.value)}>
        <option value="">Select Category</option>
        {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>
      <div>
        {authors.map(a => (
          <label key={a.id} style={{ marginRight: 8 }}>
            <input type="checkbox" checked={author_ids.includes(a.id)} onChange={() => toggleAuthor(a.id)} />
            {a.name}
          </label>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button type="submit">Save</button>
        {onCancel && <button type="button" onClick={onCancel}>Cancel</button>}
      </div>
    </form>
  )
}
