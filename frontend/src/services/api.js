import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const username = import.meta.env.VITE_API_USER || 'admin'
const password = import.meta.env.VITE_API_PASS || 'admin123'

const client = axios.create({ baseURL })

client.interceptors.request.use((config) => {
  const token = btoa(`${username}:${password}`)
  config.headers.Authorization = `Basic ${token}`
  return config
})

export const api = {
  async getStats() {
    const { data } = await client.get('/stats/summary')
    return data
  },
  async authorEarliestLatest(id) {
    const { data } = await client.get(`/stats/author/${id}/earliest_latest`)
    return data
  },
  async authorHasBooks(id) {
    const { data } = await client.get(`/stats/author/${id}/has_books`)
    return data
  },
  async getBooks(params = {}) {
    const { data } = await client.get('/books', { params })
    return data
  },
  async createBook(body) {
    const { data } = await client.post('/books', body)
    return data
  },
  async updateBook(id, body) {
    const { data } = await client.put(`/books/${id}`, body)
    return data
  },
  async deleteBook(id) {
    const { data } = await client.delete(`/books/${id}`)
    return data
  },
  async getAuthors() {
    const { data } = await client.get('/authors')
    return data
  },
  async createAuthor(body) {
    const { data } = await client.post('/authors', body)
    return data
  },
  async updateAuthor(id, body) {
    const { data } = await client.put(`/authors/${id}`, body)
    return data
  },
  async deleteAuthor(id) {
    const { data } = await client.delete(`/authors/${id}`)
    return data
  },
  async getCategories() {
    const { data } = await client.get('/categories')
    return data
  },
  async createCategory(body) {
    const { data } = await client.post('/categories', body)
    return data
  },
  async categoryHasBooks(id) {
    const { data } = await client.get(`/stats/category/${id}/has_books`)
    return data
  },
  async categoryAllHaveYear(id) {
    const { data } = await client.get(`/stats/category/${id}/all_have_year`)
    return data
  },
}

export default client
