/**
 * 通用工具函数
 */

/**
 * 格式化容量
 */
const formatCapacity = (mw) => {
  if (!mw && mw !== 0) return '';
  if (mw >= 1000) return (mw / 1000).toFixed(1) + ' GW';
  return mw.toFixed(0) + ' MW';
};

/**
 * 格式化金额
 */
const formatMoney = (bn) => {
  if (!bn && bn !== 0) return '';
  return bn.toFixed(0) + '亿元';
};

/**
 * 格式化日期
 */
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return dateStr.slice(0, 10);
};

/**
 * 状态码 → 中文名
 */
const statusName = (code) => {
  const map = {
    planned: '规划', approved: '核准', bidding: '招标',
    construction: '在建', grid_connected: '并网',
    completed: '完工', shelved: '搁置', cancelled: '取消',
  };
  return map[code] || code || '';
};

module.exports = {
  formatCapacity,
  formatMoney,
  formatDate,
  statusName,
};
