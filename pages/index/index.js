const api = require('../../utils/api');

Page({
  data: {
    projects: [],
    filters: {},
    sortBy: 'updated_at',
    sortOrder: 'desc',

    // 分页
    page: 1,
    pageSize: 20,
    total: 0,
    hasMore: true,
    loading: false,
    refreshing: false,
  },

  onLoad() {
    this.loadProjects();
  },

  onShow() {
    // 每次显示页面时刷新（可能从详情页返回，状态可能已变更）
    if (this.data.projects.length > 0) {
      this.refreshProjects();
    }
  },

  // ── 加载项目列表 ──
  async loadProjects(reset = true) {
    if (this.data.loading) return;

    const page = reset ? 1 : this.data.page + 1;
    if (!reset && !this.data.hasMore) return;

    this.setData({ loading: true });

    try {
      const params = {
        page,
        page_size: this.data.pageSize,
        sort_by: this.data.sortBy,
        sort_order: this.data.sortOrder,
        ...this.data.filters,
      };

      const res = await api.get('/projects', params);
      const newProjects = res.data || [];
      const pagination = res.pagination || {};

      this.setData({
        projects: reset ? newProjects : [...this.data.projects, ...newProjects],
        page,
        total: pagination.total || 0,
        hasMore: page < (pagination.total_pages || 0),
        loading: false,
      });
    } catch (err) {
      this.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  // ── 下拉刷新 ──
  async onPullDownRefresh() {
    await this.loadProjects(true);
    wx.stopPullDownRefresh();
  },

  // ── 触底加载更多 ──
  onReachBottom() {
    this.loadProjects(false);
  },

  // 强制刷新
  async refreshProjects() {
    this.setData({ page: 1, hasMore: true });
    await this.loadProjects(true);
  },

  // ── 筛选变更 ──
  onFilterChange(e) {
    const { filters } = e.detail;
    this.setData({ filters, page: 1, hasMore: true }, () => {
      this.loadProjects(true);
    });
  },

  // ── 点击项目卡片 → 跳转详情 ──
  onProjectTap(e) {
    const { id } = e.detail;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  },

  // ── 搜索入口 ──
  onSearchTap() {
    wx.navigateTo({ url: '/pages/search/search' });
  },
});
