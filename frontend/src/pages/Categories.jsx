import { useEffect, useState } from 'react'
import { api } from '../services/api.js'

export default function Categories() {
  const [categories, setCategories] = useState([])
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    try {
      setLoading(true)
      const c = await api.getCategories()
      setCategories(c)
      setError('')
    } catch {
      setError('Failed to load categories')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function submit() {
    if (!name.trim()) return
    try {
      await api.createCategory({ name })
      setName('')
      await load()
    } catch {
      setError('Create failed')
    }
  }

  return (
    <div>
      <h2>Categories</h2>
      {loading ? <div>Loading…</div> : error ? <div>{error}</div> : (
        <ul>
          {categories.map(c => <li key={c.id}>{c.name}</li>)}
        </ul>
      )}
      <div style={{ marginTop: 12 }}>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Category name" />
        <button onClick={submit}>Create</button>
      </div>
    </div>
  )
}
