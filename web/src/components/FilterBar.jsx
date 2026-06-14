import { useState } from 'react'
import { ChevronDown, X } from 'lucide-react'

const QUICK_FILTERS = [
  { key: 'status', value: 'approved', label: '核准' },
  { key: 'status', value: 'bidding', label: '招标' },
  { key: 'status', value: 'construction', label: '在建' },
  { key: 'project_type', value: 'offshore', label: '海上风电' },
  { key: 'project_type', value: 'onshore', label: '陆上风电' },
  { key: 'tower_type', value: 'hybrid', label: '混塔' },
]

export default function FilterBar({ filters, onChange }) {
  const [showPanel, setShowPanel] = useState(false)

  const toggleFilter = (key, value) => {
    const next = { ...filters }
    if (next[key] === value) {
      delete next[key]
    } else {
      next[key] = value
    }
    onChange(next)
  }

  const isActive = (key, value) => filters[key] === value

  return (
    <div className="bg-white border-b border-gray-100">
      {/* 快捷筛选 */}
      <div className="flex items-center gap-2 px-4 py-3 overflow-x-auto scrollbar-hide">
        {QUICK_FILTERS.map((f) => (
          <button
            key={`${f.key}-${f.value}`}
            onClick={() => toggleFilter(f.key, f.value)}
            className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              isActive(f.key, f.value)
                ? 'bg-primary-800 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {f.label}
          </button>
        ))}
        <button
          onClick={() => setShowPanel(!showPanel)}
          className="shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-full text-sm border border-gray-300 text-gray-600"
        >
          更多 <ChevronDown size={14} className={showPanel ? 'rotate-180' : ''} />
        </button>
        {Object.keys(filters).length > 0 && (
          <button
            onClick={() => onChange({})}
            className="shrink-0 flex items-center gap-1 px-3 py-1.5 text-sm text-gray-400 hover:text-gray-600"
          >
            <X size={14} /> 清除
          </button>
        )}
      </div>

      {/* 展开面板 */}
      {showPanel && (
        <div className="px-4 pb-4 border-t border-gray-50">
          <div className="pt-3">
            <p className="text-xs font-semibold text-gray-500 mb-2">项目类型</p>
            <div className="flex gap-2">
              {['onshore', 'offshore'].map((code) => (
                <button
                  key={code}
                  onClick={() => toggleFilter('project_type', code)}
                  className={`px-4 py-2 rounded-lg text-sm ${
                    isActive('project_type', code)
                      ? 'bg-green-50 text-primary-800 border border-primary-600'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {code === 'onshore' ? '陆上风电' : '海上风电'}
                </button>
              ))}
            </div>
          </div>
          <div className="pt-3">
            <p className="text-xs font-semibold text-gray-500 mb-2">塔筒构造</p>
            <div className="flex gap-2">
              {['steel', 'hybrid'].map((code) => (
                <button
                  key={code}
                  onClick={() => toggleFilter('tower_type', code)}
                  className={`px-4 py-2 rounded-lg text-sm ${
                    isActive('tower_type', code)
                      ? 'bg-green-50 text-primary-800 border border-primary-600'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {code === 'steel' ? '钢塔' : '混塔'}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
