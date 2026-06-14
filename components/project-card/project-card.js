Component({
  properties: {
    project: {
      type: Object,
      value: {},
    },
    showProvince: {
      type: Boolean,
      value: true,
    },
  },

  computed: {},

  methods: {
    onTap() {
      this.triggerEvent('tap', { id: this.data.project.id });
    },
  },

  // 格式化工具方法在 WXML 中通过 wxs 调用
});
