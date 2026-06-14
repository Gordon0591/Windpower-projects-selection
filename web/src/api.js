import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 10000,
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    console.error('API Error:', err)
    return Promise.reject(err)
  }
)

export const getProjects = (params) => api.get('/projects', { params })
export const getProject = (id) => api.get(`/projects/${id}`)
export const getOverview = () => api.get('/stats/overview')
export const getByProvince = () => api.get('/stats/by-province')
export const getSuppliers = () => api.get('/stats/supplier-ranking')
export const getTowerRatio = () => api.get('/stats/tower-type-ratio')
export const getDict = (type) => api.get(`/dict/${type}`)

export default api