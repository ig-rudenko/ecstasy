<template>
<span :class="getStatusClasses">{{status}}</span>
</template>

<script>
export default {
  name: "TechCapabilityBadge.vue",
  props: {
    status: {required: true, type: String}
  },
  data (){
    return {
      lineStatuses: [
        {name: "empty", classes: ["badge", "bg-secondary"]},
        {name: "active", classes: ["badge", "bg-success"]},
        {name: "pause", classes: ["badge", "bg-warning"]},
        {name: "reserved", classes: ["badge", "bg-primary"]},
        {name: "bad", classes: ["badge", "bg-danger"]},
      ]
    }
  },
  computed: {
    getStatusClasses(){
      for (let lineStatus of this.lineStatuses) {
        if (lineStatus.name === this.status) return lineStatus.classes
      }
    }
  }

}
</script>

<style scoped>

</style>