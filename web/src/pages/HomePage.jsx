import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Loader2 } from 'lucide-react'
import { getProjects } from '../api'
import ProjectCard from '../components/ProjectCard'
import FilterBar from '../components/FilterBar'

export default function HomePage() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [filters, setFilters] = useState({})
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async (reset = false) => {
    if (loading) return
    const currentPage = reset ? 1 : page
    if (!reset && !hasMore) return

    setLoading(true)
    try {
      const res = await getProjects({
        page: currentPage,
        page_size: 20,
        ...filters,
      })
      const list = res.data || []
      const pagination = res.pagination || {}

      setProjects(prev => reset ? list : [...prev, ...list])
      setPage(currentPage)
      setTotal(pagination.total || 0)
      setHasMore(currentPage < (pagination.total_pages || 0))
    } finally {
      setLoading(false)
    }
  }, [filters, page, hasMore, loading])

  useEffect(() => {
    setPage(1)
    setHasMore(true)
    load(true)
  }, [filters])

  const handleScroll = useCallback(() => {
    if (loading || !hasMore) return
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement
    if (scrollTop + clientHeight >= scrollHeight - 200) {
      setPage(p => p + 1)
    }
  }, [loading, hasMore])

  useEffect(() => {
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [handleScroll])

  useEffect(() => {
    if (page > 1) load(false)
  }, [page])

  return (
    <div>
      {/* 搜索栏 */}
      <div className="bg-white px-4 py-3">
        <div
          onClick={() => navigate('/search')}
          className="flex items-center gap-2 bg-gray-100 rounded-full px-4 py-2.5 text-gray-400 cursor-pointer"
        >
          <Search size={18} />
          <span className="text-sm">搜索项目名称、业主、供应商...</span>
        </div>
      </div>

      {/* 筛选栏 */}
      <FilterBar filters={filters} onChange={setFilters} />

      {/* 统计 */}
      {total > 0 && (
        <div className="px-4 py-2 text-xs text-gray-400">
          共 {total} 个项目
        </div>
      )}

      {/* 列表 */}
      <div className="px-4 pb-8">
        {projects.map(p => (
          <ProjectCard key={p.id} project={p} />
        ))}

        {loading && (
          <div className="flex justify-center py-6 text-gray-400">
            <Loader2 size={20} className="animate-spin" />
          </div>
        )}

        {!hasMore && projects.length > 0 && (
          <div className="text-center py-6 text-sm text-gray-400">
            — 已加载全部 —
          </div>
        )}

        {!loading && projects.length === 0 && (
          <div className="flex flex-col items-center py-20 text-gray-400">
            <span className="text-4xl mb-3">📭</span>
            <p className="text-lg">暂无匹配的项目</p>
            <p className="text-sm mt-1">尝试调整筛选条件</p>
          </div>
        )}
      </div>
    </div>
  )
}
