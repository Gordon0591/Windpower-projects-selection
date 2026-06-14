App({
  globalData: {
    // 开发环境: http://localhost:8000/v1
    // 生产环境: https://your-domain.com/v1
    baseUrl: 'http://localhost:8000/v1',
    provinces: [],
    statuses: [],
    projectTypes: [],
    towerTypes: [],
  },

  onLaunch() {
    // 加载字典数据到全局缓存
    this.loadDicts();
  },

  async loadDicts() {
    const dicts = [
      { key: 'provinces', url: '/dict/provinces' },
      { key: 'statuses', url: '/dict/statuses' },
      { key: 'projectTypes', url: '/dict/project-types' },
      { key: 'towerTypes', url: '/dict/tower-types' },
    ];

    for (const { key, url } of dicts) {
      wx.request({
        url: this.globalData.baseUrl + url,
        success: (res) => {
          if (res.data.code === 0) {
            this.globalData[key] = res.data.data;
          }
        },
      });
    }
  },
});
