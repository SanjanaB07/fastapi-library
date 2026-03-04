export default function StatsCard({ title, value }) {
  return (
    <div style={{ border: '1px solid #444', padding: 12, borderRadius: 8, minWidth: 200 }}>
      <div style={{ fontSize: 12, color: '#bbb' }}>{title}</div>
      <div style={{ fontSize: 24 }}>{value ?? 'N/A'}</div>
    </div>
  )
}
