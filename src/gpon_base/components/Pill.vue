<template>
  <div class="olt-port-badge me-2" :style="{'background-color': backColor}">
    <span :style="{color: color}">{{ text }}</span>
    <div :style="{background: color}" class="olt-port-badge-point"></div>
  </div>
</template>

<script>
export default {
  name: "Pill.vue",
  props: {
    text: {required: true, type: String},
    color: {required: false, type: String, default: "#4A4AFF"},
    backColor: {required: false, type: String, default: "#E6E6F2"},
  }
}
</script>

<style scoped>
.olt-port-badge {
  height: 24px;
  padding: 0 10px 0 3px;
  background-color: #E6E6F2;
  width: max-content;
  font-size: 14px;
  font-weight: 600;
  border-radius: 19px;
}

.olt-port-badge span {
  margin-left: 16px;
}

.olt-port-badge-point {
  width: 6px;
  height: 6px;
  left: 6px;
  top: -12px;
  position: relative;
  border-radius: 9999px;
}
</style>