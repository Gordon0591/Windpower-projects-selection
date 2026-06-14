/**
 * API 请求封装
 * 用法: const api = require('../../utils/api');
 *       api.get('/projects', { province_id: 51 }).then(res => ...)
 */

const app = getApp();

const request = (method, path, params = {}, data = null) => {
  return new Promise((resolve, reject) => {
    const baseUrl = app.globalData.baseUrl;

    // 构建 query string
    const queryParts = [];
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') {
        queryParts.push(`${k}=${encodeURIComponent(v)}`);
      }
    }
    const query = queryParts.length ? '?' + queryParts.join('&') : '';

    wx.request({
      url: baseUrl + path + query,
      method,
      data,
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data);
        } else {
          reject(res.data);
        }
      },
      fail: (err) => {
        wx.showToast({ title: '网络请求失败', icon: 'none' });
        reject(err);
      },
    });
  });
};

module.exports = {
  get: (path, params) => request('GET', path, params),
  post: (path, data) => request('POST', path, {}, data),
  put: (path, data) => request('PUT', path, {}, data),
  patch: (path, data) => request('PATCH', path, {}, data),
};
