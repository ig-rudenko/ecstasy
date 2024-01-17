<template>
  <div :class="pillClasses" :style="{'background-color': backColor}">
    <span :style="{color: color}">{{ text }}</span>
    <div :style="{background: color}" class="pill-badge-point"></div>
  </div>
</template>

<script>
export default {
  name: "Pill.vue",
  props: {
    text: {required: true, type: String},
    color: {required: false, type: String, default: "#4A4AFF"},
    hover: {required: false, type: String, default: false},
    backColor: {required: false, type: String, default: "#E6E6F2"},
  },
  computed: {
    pillClasses(){
      let classes_list = ['pill-badge', 'me-2']
      if (this.hover) classes_list.push('pill-badge-hover')
      return classes_list
    }
  }
}
</script>

<style scoped>
.pill-badge {
  height: 24px;
  padding: 1px 10px 1px 3px;
  background-color: #E6E6F2;
  width: max-content;
  font-size: 14px;
  font-weight: 600;
  border-radius: 19px;
}

.pill-badge span {
  margin-left: 16px;
}

.pill-badge-hover:hover {
  cursor: pointer;
  box-shadow: 0 .5rem 1rem rgba(0,0,0,.15)!important;
  border: 1px solid #a48eff;
  padding: 0 9px 0 2px;
}

.pill-badge-point {
  width: 6px;
  height: 6px;
  left: 6px;
  top: -12px;
  position: relative;
  border-radius: 9999px;
}
</style>