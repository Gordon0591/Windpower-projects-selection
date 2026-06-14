Page({
  data: {
    notificationsEnabled: true,
    subscriptions: {
      provinces: [],
      projectTypes: [],
      minCapacity: '',
    },
  },

  onLoad() {
    const subs = wx.getStorageSync('subscriptions');
    if (subs) {
      this.setData({ subscriptions: subs });
    }
  },

  // 通知开关
  onNotificationToggle(e) {
    this.setData({ notificationsEnabled: e.detail.value });
  },

  // 订阅设置变更
  onSubChange(e) {
    const { field, value } = e.currentTarget.dataset;
    const subs = { ...this.data.subscriptions };
    if (field === 'provinces' || field === 'projectTypes') {
      const arr = subs[field] || [];
      const idx = arr.indexOf(value);
      if (idx > -1) arr.splice(idx, 1);
      else arr.push(value);
      subs[field] = arr;
    }
    this.setData({ subscriptions: subs });
    wx.setStorageSync('subscriptions', subs);
  },

  onCapacityInput(e) {
    const subs = { ...this.data.subscriptions, minCapacity: e.detail.value };
    this.setData({ subscriptions: subs });
    wx.setStorageSync('subscriptions', subs);
  },

  // 关于
  onAbout() {
    wx.showModal({
      title: '风电项目信息收集系统',
      content: '版本 0.1.0\n\n定期收集中国风电陆上/海上风电项目的核准、招标、在建和完工信息。\n\n数据来源：北极星风力发电网、国家能源局等公开渠道。',
      showCancel: false,
    });
  },
});
