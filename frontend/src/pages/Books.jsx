import { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import Filters from '../components/Filters.jsx'
import BookTable from '../components/BookTable.jsx'
import BookForm from '../components/BookForm.jsx'

export default function Books() {
  const [filters, setFilters] = useState({})
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(null)
  const [message, setMessage] = useState('')

  async function load() {
    try {
      setLoading(true)
      const data = await api.getBooks(filters)
      setBooks(data)
      setError('')
    } catch {
      setError('Failed to load books')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [JSON.stringify(filters)])

  async function create(body) {
    const b = await api.createBook(body)
    setMessage('Book created')
    setEditing(null)
    await load()
  }

  async function update(body) {
    const b = await api.updateBook(editing.id, body)
    setMessage('Book updated')
    setEditing(null)
    await load()
  }

  async function remove(b) {
    if (!confirm('Delete this book?')) return
    try {
      await api.deleteBook(b.id)
      setMessage('Book deleted')
      await load()
    } catch {
      setError('Delete failed')
    }
  }

  return (
    <div>
      <h2>Books</h2>
      <Filters value={filters} onChange={setFilters} />
      {loading ? <div>Loading…</div> : error ? <div>{error}</div> : <BookTable books={books} onEdit={setEditing} onDelete={remove} />}
      <div style={{ marginTop: 16 }}>
        <h3>{editing ? 'Edit Book' : 'Create Book'}</h3>
        <BookForm initial={editing} onSubmit={editing ? update : create} onCancel={() => setEditing(null)} />
      </div>
      {message && <div style={{ color: 'green', marginTop: 8 }}>{message}</div>}
    </div>
  )
}
