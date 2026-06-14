const api = require('../../utils/api');

Page({
  data: {
    project: null,
    statusHistory: [],
    sources: [],
    loading: true,
  },

  onLoad(options) {
    const { id } = options;
    if (id) {
      this.loadDetail(id);
    }
  },

  async loadDetail(id) {
    try {
      const res = await api.get(`/projects/${id}`);
      const project = res.data;

      this.setData({
        project,
        statusHistory: project.status_history || [],
        sources: project.sources || [],
        loading: false,
      });
    } catch (err) {
      this.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  // 复制项目名称
  onCopyName() {
    if (this.data.project) {
      wx.setClipboardData({
        data: this.data.project.name,
        success: () => wx.showToast({ title: '已复制', icon: 'success' }),
      });
    }
  },

  // 打开来源链接
  onOpenSource(e) {
    const { url } = e.currentTarget.dataset;
    if (url) {
      wx.setClipboardData({
        data: url,
        success: () => wx.showToast({ title: '链接已复制，请在浏览器打开', icon: 'none' }),
      });
    }
  },
});
