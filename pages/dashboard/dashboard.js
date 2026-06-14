const api = require('../../utils/api');

Page({
  data: {
    overview: null,
    provinceStats: [],
    supplierRanking: [],
    towerRatio: null,
    loading: true,
  },

  onLoad() {
    this.loadAll();
  },

  onPullDownRefresh() {
    this.loadAll().then(() => wx.stopPullDownRefresh());
  },

  async loadAll() {
    this.setData({ loading: true });
    try {
      const [overview, provinces, suppliers, towerRatio] = await Promise.all([
        api.get('/stats/overview'),
        api.get('/stats/by-province'),
        api.get('/stats/supplier-ranking'),
        api.get('/stats/tower-type-ratio'),
      ]);

      this.setData({
        overview: overview.data,
        provinceStats: (provinces.data || []).slice(0, 10),
        supplierRanking: (suppliers.data || []).slice(0, 10),
        towerRatio: towerRatio.data,
        loading: false,
      });
    } catch (err) {
      this.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  // 格式化数字
  fmtNum(num) {
    if (!num) return '0';
    if (num >= 10000) return (num / 10000).toFixed(1) + '万';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return num.toString();
  },
});
