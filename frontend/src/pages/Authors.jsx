import { useEffect, useState } from 'react'
import { api } from '../services/api.js'

export default function Authors() {
  const [authors, setAuthors] = useState([])
  const [name, setName] = useState('')
  const [editing, setEditing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [stats, setStats] = useState(null)

  async function load() {
    try {
      setLoading(true)
      const a = await api.getAuthors()
      setAuthors(a)
      setError('')
    } catch {
      setError('Failed to load authors')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function submit() {
    if (!name.trim()) return
    if (editing) {
      await api.updateAuthor(editing.id, { name })
    } else {
      await api.createAuthor({ name })
    }
    setName('')
    setEditing(null)
    await load()
  }

  async function remove(a) {
    try {
      await api.deleteAuthor(a.id)
      await load()
    } catch {
      setError('Delete failed')
    }
  }

  async function selectAuthor(a) {
    setSelected(a)
    const s = await api.authorEarliestLatest(a.id)
    setStats(s)
  }

  return (
    <div>
      <h2>Authors</h2>
      {loading ? <div>Loading…</div> : error ? <div>{error}</div> : (
        <table style={{ width: '100%' }}>
          <thead><tr><th>Name</th><th>Actions</th></tr></thead>
          <tbody>
            {authors.map(a => (
              <tr key={a.id}>
                <td><button onClick={() => selectAuthor(a)}>{a.name}</button></td>
                <td>
                  <button onClick={() => { setEditing(a); setName(a.name) }}>Edit</button>
                  <button onClick={() => remove(a)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div style={{ marginTop: 12 }}>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Author name" />
        <button onClick={submit}>{editing ? 'Update' : 'Create'}</button>
        {editing && <button onClick={() => { setEditing(null); setName('') }}>Cancel</button>}
      </div>
      {stats && (
        <div style={{ marginTop: 12 }}>
          <div>Earliest: {stats.earliest ? `${stats.earliest.title} (${stats.earliest.year || '-'})` : 'None'}</div>
          <div>Latest: {stats.latest ? `${stats.latest.title} (${stats.latest.year || '-'})` : 'None'}</div>
        </div>
      )}
    </div>
  )
}
