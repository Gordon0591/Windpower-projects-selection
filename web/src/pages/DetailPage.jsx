import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, MapPin, Calendar, Copy, ExternalLink } from 'lucide-react'
import { getProject } from '../api'

function fmtCap(mw) {
  if (!mw) return '--'
  return mw >= 1000 ? (mw / 1000).toFixed(1) + ' GW' : mw + ' MW'
}

export default function DetailPage() {
  const { id } = useParams()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getProject(id)
      .then((res) => setProject(res.data))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex justify-center py-20 text-gray-400">
        <div className="animate-spin h-6 w-6 border-2 border-primary-600 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-20 text-gray-400">
        <p>项目不存在</p>
        <Link to="/" className="text-primary-600 mt-2 inline-block">返回首页</Link>
      </div>
    )
  }

  const towerName = project.tower_type?.code === 'steel' ? '钢塔' : project.tower_type?.code === 'hybrid' ? '混塔' : '待确认'

  return (
    <div className="pb-10">
      {/* 返回按钮 */}
      <div className="bg-white px-4 py-3 border-b border-gray-100">
        <Link to="/" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800">
          <ArrowLeft size={18} />
          <span>返回列表</span>
        </Link>
      </div>

      {/* 头部 */}
      <div className="bg-white px-5 py-6">
        <div className="flex items-center gap-2 mb-3">
          <span className={`status-${project.status?.code} px-3 py-1 rounded-lg text-xs font-semibold`}>
            {project.status?.name}
          </span>
          {project.project_type?.code === 'offshore' ? (
            <span className="px-3 py-1 rounded-full text-xs bg-sky-100 text-sky-700 font-medium">海上风电</span>
          ) : (
            <span className="px-3 py-1 rounded-full text-xs bg-green-100 text-green-700 font-medium">陆上风电</span>
          )}
        </div>
        <h1 className="text-xl font-bold text-gray-900 leading-snug mb-2">{project.name}</h1>
        {project.province && (
          <p className="flex items-center gap-1 text-sm text-gray-400">
            <MapPin size={14} />
            {project.province.name} · {project.province.region}
          </p>
        )}
      </div>

      {/* 核心指标 */}
      <div className="bg-white px-5 py-5 mt-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-green-50 rounded-xl p-4">
            <p className="text-xs text-green-600 mb-1">装机容量</p>
            <p className="text-2xl font-bold text-green-800">{fmtCap(project.capacity_mw)}</p>
          </div>
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="text-xs text-gray-500 mb-1">风机台数</p>
            <p className="text-xl font-bold text-gray-800">{project.turbine_count || '--'}<span className="text-sm font-normal text-gray-500 ml-1">台</span></p>
          </div>
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="text-xs text-gray-500 mb-1">单机容量</p>
            <p className="text-xl font-bold text-gray-800">{project.unit_capacity_mw || '--'}<span className="text-sm font-normal text-gray-500 ml-1">MW</span></p>
          </div>
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="text-xs text-gray-500 mb-1">塔筒构造</p>
            <p className="text-xl font-bold text-gray-800">{towerName}</p>
          </div>
        </div>
      </div>

      {/* 项目信息 */}
      <div className="bg-white px-5 py-5 mt-3">
        <h2 className="text-base font-bold text-gray-900 pb-3 border-b border-gray-100 mb-3">📋 项目信息</h2>
        <div className="space-y-0">
          {project.owner && (
            <div className="flex py-3 border-b border-gray-50">
              <span className="w-28 text-sm text-gray-400 shrink-0">业主/开发商</span>
              <span className="text-sm text-gray-800 font-medium">{project.owner}</span>
            </div>
          )}
          {project.turbine_supplier && (
            <div className="flex py-3 border-b border-gray-50">
              <span className="w-28 text-sm text-gray-400 shrink-0">风机供应商</span>
              <span className="text-sm text-gray-800 font-medium">{project.turbine_supplier}</span>
            </div>
          )}
          {project.investment_bn && (
            <div className="flex py-3 border-b border-gray-50">
              <span className="w-28 text-sm text-gray-400 shrink-0">投资金额</span>
              <span className="text-sm text-orange-600 font-bold">{project.investment_bn} 亿元</span>
            </div>
          )}
          {project.description && (
            <div className="flex py-3">
              <span className="w-28 text-sm text-gray-400 shrink-0">项目描述</span>
              <span className="text-sm text-gray-600 leading-relaxed">{project.description}</span>
            </div>
          )}
        </div>
      </div>

      {/* 关键节点 */}
      {(project.approval_date || project.bid_date || project.construction_start_date || project.planned_cod_date || project.completion_date) && (
        <div className="bg-white px-5 py-5 mt-3">
          <h2 className="text-base font-bold text-gray-900 pb-3 border-b border-gray-100 mb-3">📅 关键节点</h2>
          <div className="space-y-4">
            {project.approval_date && (
              <div className="flex items-start gap-3">
                <div className="w-3 h-3 rounded-full bg-gray-300 mt-1.5 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-gray-800">核准批复</p>
                  <p className="text-xs text-gray-400 mt-0.5">{project.approval_date}</p>
                </div>
              </div>
            )}
            {project.construction_start_date && (
              <div className="flex items-start gap-3">
                <div className="w-3 h-3 rounded-full bg-gray-300 mt-1.5 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-gray-800">主体开工</p>
                  <p className="text-xs text-gray-400 mt-0.5">{project.construction_start_date}</p>
                </div>
              </div>
            )}
            {project.planned_cod_date && (
              <div className="flex items-start gap-3">
                <div className="w-3 h-3 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-gray-800">计划并网</p>
                  <p className="text-xs text-blue-500 mt-0.5">{project.planned_cod_date}</p>
                </div>
              </div>
            )}
            {project.completion_date && (
              <div className="flex items-start gap-3">
                <div className="w-3 h-3 rounded-full bg-green-500 mt-1.5 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-gray-800">完工/全容量并网</p>
                  <p className="text-xs text-green-600 mt-0.5">{project.completion_date}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 信息来源 */}
      {project.sources?.length > 0 && (
        <div className="bg-orange-50 px-5 py-5 mt-3">
          <h2 className="text-base font-bold text-gray-900 pb-3 border-b border-orange-100 mb-2">📡 信息来源</h2>
          <p className="text-xs text-gray-400 mb-3">以下为本项目信息的数据采集来源，点击可复制链接</p>
          <div className="space-y-2">
            {project.sources.map((s, i) => (
              <div
                key={i}
                className="bg-white rounded-lg p-3 border border-orange-200 flex items-start justify-between gap-3 cursor-pointer hover:shadow-sm transition-shadow"
                onClick={() => {
                  navigator.clipboard?.writeText(s.source_url || '')
                  alert('链接已复制')
                }}
              >
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-gray-800">{s.source_name}</p>
                  {s.source_url && <p className="text-xs text-blue-500 mt-1 truncate">{s.source_url}</p>}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {s.captured_at && <span className="text-xs text-gray-400">{s.captured_at.slice(0, 10)}</span>}
                  <Copy size={14} className="text-gray-400" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
