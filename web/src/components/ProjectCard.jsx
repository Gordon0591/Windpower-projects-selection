import { Link } from 'react-router-dom'
import { Zap, Factory, Cpu, TowerControl } from 'lucide-react'

function fmtCap(mw) {
  if (!mw) return '--'
  return mw >= 1000 ? (mw / 1000).toFixed(1) + ' GW' : mw + ' MW'
}

export default function ProjectCard({ project }) {
  const statusName = {
    planned: '规划', approved: '核准', bidding: '招标',
    construction: '在建', grid_connected: '并网',
    completed: '完工', shelved: '搁置', cancelled: '取消'
  }[project.status?.code] || project.status?.code

  const typeName = project.project_type?.code === 'offshore' ? '海上' : '陆上'
  const typeColor = project.project_type?.code === 'offshore' ? 'bg-sky-100 text-sky-700' : 'bg-green-100 text-green-700'

  const towerName = project.tower_type?.code === 'steel' ? '钢塔' : project.tower_type?.code === 'hybrid' ? '混塔' : '待确认'

  return (
    <Link
      to={`/project/${project.id}`}
      className="block bg-white rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow mb-4"
    >
      {/* 顶部标签 */}
      <div className="flex items-center gap-2 mb-3">
        <span className={`status-${project.status?.code} px-3 py-1 rounded-lg text-xs font-semibold`}>
          {statusName}
        </span>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${typeColor}`}>
          {typeName}
        </span>
        {project.is_verified && (
          <span className="ml-auto text-green-600 text-xs font-medium">✓ 已核实</span>
        )}
      </div>

      {/* 项目名称 */}
      <h3 className="text-lg font-bold text-gray-900 leading-snug mb-1 line-clamp-2">
        {project.name}
      </h3>

      {/* 业主省份 */}
      <p className="text-sm text-gray-400 mb-4">
        {project.owner} {project.province?.name && `· ${project.province.name}`}
      </p>

      {/* 核心指标 2x2 网格 */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-green-50 rounded-xl p-3">
          <div className="flex items-center gap-1 text-green-700 mb-1">
            <Zap size={14} />
            <span className="text-xs">装机容量</span>
          </div>
          <span className="text-xl font-bold text-green-800">{fmtCap(project.capacity_mw)}</span>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <div className="flex items-center gap-1 text-gray-500 mb-1">
            <Factory size={14} />
            <span className="text-xs">风机台数</span>
          </div>
          <span className="text-lg font-bold text-gray-800">{project.turbine_count || '--'}<span className="text-sm font-normal text-gray-500 ml-0.5">台</span></span>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <div className="flex items-center gap-1 text-gray-500 mb-1">
            <Cpu size={14} />
            <span className="text-xs">单机容量</span>
          </div>
          <span className="text-lg font-bold text-gray-800">{project.unit_capacity_mw || '--'}<span className="text-sm font-normal text-gray-500 ml-0.5">MW</span></span>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <div className="flex items-center gap-1 text-gray-500 mb-1">
            <TowerControl size={14} />
            <span className="text-xs">塔筒构造</span>
          </div>
          <span className="text-lg font-bold text-gray-800">{towerName}</span>
        </div>
      </div>

      {/* 底部信息 */}
      <div className="flex items-center gap-3 text-sm text-gray-500 pt-3 border-t border-gray-100">
        {project.turbine_supplier && <span>{project.turbine_supplier}</span>}
        {project.investment_bn && (
          <span className="text-orange-600 font-semibold">{project.investment_bn}亿元</span>
        )}
        <span className="ml-auto text-xs text-gray-400">
          {project.approval_date && `核准 ${project.approval_date.slice(0, 7)}`}
        </span>
      </div>
    </Link>
  )
}
