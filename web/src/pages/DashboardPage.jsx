import { useState, useEffect } from 'react'
import { getOverview, getByProvince, getSuppliers } from '../api'

function fmtGW(mw) {
  if (!mw) return '0'
  return mw >= 1000 ? (mw / 1000).toFixed(1) + ' GW' : mw.toFixed(0) + ' MW'
}

export default function DashboardPage() {
  const [overview, setOverview] = useState(null)
  const [provinces, setProvinces] = useState([])
  const [suppliers, setSuppliers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([getOverview(), getByProvince(), getSuppliers()])
      .then(([ov, pr, su]) => {
        setOverview(ov.data)
        setProvinces((pr.data || []).slice(0, 10))
        setSuppliers((su.data || []).slice(0, 10))
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-20 text-gray-400">
        <div className="animate-spin h-6 w-6 border-2 border-primary-600 border-t-transparent rounded-full" />
      </div>
    )
  }

  const ov = overview || {}
  const byType = ov.by_type || {}
  const byStatus = ov.by_status || {}
  const byTower = ov.by_tower_type || {}

  return (
    <div className="px-4 py-4 pb-10 space-y-4">
      {/* 总览卡片 */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <p className="text-2xl font-bold text-primary-800">{ov.total_projects || 0}</p>
          <p className="text-xs text-gray-400 mt-1">项目总数</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <p className="text-2xl font-bold text-blue-600">{fmtGW(ov.total_capacity_mw)}</p>
          <p className="text-xs text-gray-400 mt-1">总装机容量</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <p className="text-2xl font-bold text-sky-600">{ov.total_turbines || 0}</p>
          <p className="text-xs text-gray-400 mt-1">风机总台数</p>
        </div>
      </div>

      {/* 状态分布 */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-bold text-gray-900 pb-3 border-b border-gray-100 mb-3">📊 项目状态分布</h3>
        <div className="space-y-2">
          {['approved', 'bidding', 'construction', 'grid_connected', 'completed'].map((code) => {
            const name = { approved: '核准', bidding: '招标', construction: '在建', grid_connected: '并网', completed: '完工' }[code]
            const data = byStatus[code] || { count: 0, capacity_mw: 0 }
            const totalCap = ov.total_capacity_mw || 1
            const pct = totalCap > 0 ? (data.capacity_mw / totalCap * 100).toFixed(0) : 0
            return (
              <div key={code} className="flex items-center gap-3">
                <span className="w-12 text-sm text-gray-600 shrink-0">{name}</span>
                <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full status-${code}`} style={{ width: `${pct}%`, opacity: 0.7 }} />
                </div>
                <span className="w-20 text-right text-sm text-gray-500 shrink-0">{fmtGW(data.capacity_mw)}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* 塔筒构造 */}
      {byTower && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-bold text-gray-900 pb-3 border-b border-gray-100 mb-3">🗼 塔筒构造比例</h3>
          <div className="flex gap-4">
            {['steel', 'hybrid', 'unknown'].map((code) => {
              const name = { steel: '钢塔', hybrid: '混塔', unknown: '待确认' }[code]
              const data = byTower[code] || { count: 0 }
              const total = ov.total_projects || 1
              const pct = total > 0 ? (data.count / total * 100).toFixed(1) : 0
              return (
                <div key={code} className="flex-1 text-center">
                  <p className="text-xl font-bold text-gray-800">{pct}%</p>
                  <p className="text-xs text-gray-400 mt-1">{name}</p>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 省份排名 */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-bold text-gray-900 pb-3 border-b border-gray-100 mb-3">🗺️ 省份装机 Top 10</h3>
        <div className="space-y-2">
          {provinces.map((p, i) => (
            <div key={p.province_id} className="flex items-center gap-3">
              <span className="w-6 text-sm font-bold text-gray-400 shrink-0">{i + 1}</span>
              <span className="flex-1 text-sm text-gray-700">{p.province_name}</span>
              <span className="text-sm font-bold text-primary-700 shrink-0">{fmtGW(p.total_capacity_mw)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 供应商排名 */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-bold text-gray-900 pb-3 border-b border-gray-100 mb-3">🏭 供应商排名</h3>
        <div className="space-y-3">
          {suppliers.map((s, i) => (
            <div key={s.supplier} className="flex items-center gap-3">
              <span className="w-6 text-sm font-bold text-gray-400 shrink-0">{i + 1}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{s.supplier}</p>
                <p className="text-xs text-gray-400">{s.project_count}个项目 · {s.total_turbines}台风机</p>
              </div>
              <span className="text-sm font-bold text-primary-700 shrink-0">{fmtGW(s.total_capacity_mw)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
