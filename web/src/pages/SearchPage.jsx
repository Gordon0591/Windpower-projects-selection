import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ArrowLeft, Clock, X, Loader2 } from 'lucide-react'
import { getProjects } from '../api'
import ProjectCard from '../components/ProjectCard'

export default function SearchPage() {
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem('searchHistory') || '[]') }
    catch { return [] }
  })
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const doSearch = async (kw) => {
    if (!kw.trim()) return
    setKeyword(kw)
    setSearched(true)
    setLoading(true)

    // 保存历史
    const newHistory = [kw, ...history.filter(h => h !== kw)].slice(0, 10)
    setHistory(newHistory)
    localStorage.setItem('searchHistory', JSON.stringify(newHistory))

    try {
      const res = await getProjects({ keyword: kw, page_size: 50 })
      setResults(res.data || [])
    } finally {
      setLoading(false)
    }
  }

  const clearHistory = () => {
    setHistory([])
    localStorage.removeItem('searchHistory')
  }

  return (
    <div className="min-h-screen bg-white">
      {/* 搜索栏 */}
      <div className="sticky top-0 z-10 bg-white border-b border-gray-100 px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="text-gray-500">
            <ArrowLeft size={22} />
          </button>
          <div className="flex-1 flex items-center bg-gray-100 rounded-full px-4 py-2.5">
            <Search size={18} className="text-gray-400 mr-2" />
            <input
              ref={inputRef}
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && doSearch(keyword)}
              placeholder="搜索项目名称、业主、供应商..."
              className="flex-1 bg-transparent outline-none text-sm"
            />
            {keyword && (
              <button onClick={() => setKeyword('')} className="text-gray-400">
                <X size={16} />
              </button>
            )}
          </div>
          <button
            onClick={() => doSearch(keyword)}
            className="text-primary-700 font-medium text-sm"
          >
            搜索
          </button>
        </div>
      </div>

      {/* 搜索结果 */}
      {searched && (
        <div className="px-4 py-4">
          {results.length > 0 ? (
            <>
              <p className="text-xs text-gray-400 mb-3">
                找到 {results.length} 个结果
              </p>
              {results.map((p) => (
                <ProjectCard key={p.id} project={p} />
              ))}
            </>
          ) : loading ? (
            <div className="flex justify-center py-20 text-gray-400">
              <Loader2 size={20} className="animate-spin" />
            </div>
          ) : (
            <div className="flex flex-col items-center py-20 text-gray-400">
              <Search size={40} className="mb-3" />
              <p className="text-lg">未找到匹配的项目</p>
              <p className="text-sm mt-1">尝试其他关键词</p>
            </div>
          )}
        </div>
      )}

      {/* 搜索历史 */}
      {!searched && history.length > 0 && (
        <div className="px-4 py-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-700">搜索历史</span>
            <button
              onClick={clearHistory}
              className="text-xs text-gray-400"
            >
              清空
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {history.map((h) => (
              <button
                key={h}
                onClick={() => doSearch(h)}
                className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600"
              >
                <Clock size={12} />
                {h}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
