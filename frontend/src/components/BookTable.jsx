export default function BookTable({ books, onEdit, onDelete }) {
  if (!books.length) return <div>No books</div>
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr>
          <th style={{ textAlign: 'left' }}>Title</th>
          <th>ISBN</th>
          <th>Year</th>
          <th>Authors</th>
          <th>Category</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {books.map(b => (
          <tr key={b.id}>
            <td>{b.title}</td>
            <td>{b.isbn || '-'}</td>
            <td>{b.publication_year || '-'}</td>
            <td>{(b.authors || []).map(a => a.name).join(', ') || '-'}</td>
            <td>{b.category?.name || '-'}</td>
            <td>
              <button onClick={() => onEdit(b)}>Edit</button>
              <button onClick={() => onDelete(b)}>Delete</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
