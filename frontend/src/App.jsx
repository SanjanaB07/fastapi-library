import { Routes, Route, NavLink } from 'react-router-dom'
import './App.css'
import Dashboard from './pages/Dashboard.jsx'
import Books from './pages/Books.jsx'
import Authors from './pages/Authors.jsx'
import Categories from './pages/Categories.jsx'
import Stats from './pages/Stats.jsx'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Library Admin</h1>
        <nav className="nav">
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/books">Books</NavLink>
          <NavLink to="/authors">Authors</NavLink>
          <NavLink to="/categories">Categories</NavLink>
          <NavLink to="/stats">Stats</NavLink>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/books" element={<Books />} />
          <Route path="/authors" element={<Authors />} />
          <Route path="/categories" element={<Categories />} />
          <Route path="/stats" element={<Stats />} />
        </Routes>
      </main>
    </div>
  )
}

export default App