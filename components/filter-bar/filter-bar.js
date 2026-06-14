const app = getApp();

Component({
  properties: {
    currentFilters: {
      type: Object,
      value: {},
    },
  },

  data: {
    // 从全局字典加载
    get provinces() { return app.globalData.provinces || []; },
    get statuses() { return app.globalData.statuses || []; },
    get projectTypes() { return app.globalData.projectTypes || []; },
    get towerTypes() { return app.globalData.towerTypes || []; },

    // 展开状态
    showPanel: false,
    // 临时筛选值（面板内使用）
    tempFilters: {},

    // 快捷筛选项
    quickFilters: [
      { key: 'status', value: 'approved', label: '核准' },
      { key: 'status', value: 'bidding', label: '招标' },
      { key: 'status', value: 'construction', label: '在建' },
      { key: 'project_type', value: 'offshore', label: '海上风电' },
      { key: 'project_type', value: 'onshore', label: '陆上风电' },
      { key: 'tower_type', value: 'hybrid', label: '混塔' },
    ],

    // 面板筛选选项
    typeOptions: [
      { code: 'onshore', name: '陆上风电' },
      { code: 'offshore', name: '海上风电' },
    ],
    towerOptions: [
      { code: 'steel', name: '钢塔' },
      { code: 'hybrid', name: '混塔' },
    ],
  },

  lifetimes: {
    attached() {
      this.setData({ tempFilters: { ...this.properties.currentFilters } });
    },
  },

  observers: {
    'currentFilters'(val) {
      this.setData({ tempFilters: { ...val } });
    },
  },

  methods: {
    // 快捷筛选切换
    onQuickTap(e) {
      const { key, value } = e.currentTarget.dataset;
      const filters = { ...this.data.tempFilters };

      if (filters[key] === value) {
        delete filters[key];
      } else {
        filters[key] = value;
      }

      this.setData({ tempFilters: filters });
      this.triggerEvent('change', { filters });
    },

    // 展开/收起面板
    togglePanel() {
      this.setData({ showPanel: !this.data.showPanel });
    },

    // 面板内选择
    onTypeTap(e) {
      const code = e.currentTarget.dataset.code;
      const filters = { ...this.data.tempFilters };
      filters.project_type = filters.project_type === code ? undefined : code;
      this.setData({ tempFilters: filters });
      this.triggerEvent('change', { filters });
    },

    onTowerTap(e) {
      const code = e.currentTarget.dataset.code;
      const filters = { ...this.data.tempFilters };
      filters.tower_type = filters.tower_type === code ? undefined : code;
      this.setData({ tempFilters: filters });
      this.triggerEvent('change', { filters });
    },

    // 重置
    onReset() {
      this.setData({ tempFilters: {}, showPanel: false });
      this.triggerEvent('change', { filters: {} });
    },

    // 确认
    onConfirm() {
      this.setData({ showPanel: false });
      this.triggerEvent('change', { filters: this.data.tempFilters });
    },

    // 判断是否激活
    isActive(key, value) {
      const f = this.data.tempFilters || {};
      return f[key] === value;
    },
  },
});
