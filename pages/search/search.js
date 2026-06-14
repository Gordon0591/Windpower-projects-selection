const api = require('../../utils/api');

Page({
  data: {
    keyword: '',
    results: [],
    searching: false,
    searched: false,
    history: [],
  },

  onLoad() {
    // 加载搜索历史
    const history = wx.getStorageSync('searchHistory') || [];
    this.setData({ history });
  },

  onInput(e) {
    this.setData({ keyword: e.detail.value });
  },

  async onSearch(e) {
    const keyword = (e.detail.value || this.data.keyword).trim();
    if (!keyword) return;

    this.setData({ searching: true, searched: true });

    // 保存搜索历史
    let history = this.data.history;
    history = [keyword, ...history.filter(h => h !== keyword)].slice(0, 10);
    this.setData({ history });
    wx.setStorageSync('searchHistory', history);

    try {
      const res = await api.get('/projects', { keyword, page_size: 50 });
      this.setData({
        results: res.data || [],
        searching: false,
      });
    } catch (err) {
      this.setData({ searching: false });
      wx.showToast({ title: '搜索失败', icon: 'none' });
    }
  },

  onHistoryTap(e) {
    const keyword = e.currentTarget.dataset.keyword;
    this.setData({ keyword });
    this.onSearch({ detail: { value: keyword } });
  },

  onClearHistory() {
    this.setData({ history: [] });
    wx.removeStorageSync('searchHistory');
  },

  onProjectTap(e) {
    const { id } = e.detail;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  },
});
