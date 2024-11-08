<template>
  <span class="px-2 rounded font-mono" :class="getStatusClasses">{{ status }}</span>
</template>

<script>
export default {
  name: "TechCapabilityBadge",
  props: {
    status: {required: true, type: String}
  },
  data() {
    return {
      lineStatuses: [
        {name: "active", classes: ['bg-green-500', 'text-gray-950']},
        {name: "pause", classes: ['bg-yellow-500', 'text-gray-950']},
        {name: "reserved", classes: ['bg-blue-500', 'text-gray-950']},
        {name: "bad", classes: ['bg-red-500', 'text-gray-950']},
      ]
    }
  },
  computed: {
    getStatusClasses() {
      for (let lineStatus of this.lineStatuses) {
        if (lineStatus.name === this.status) return lineStatus.classes
      }
    }
  }

}
</script>

<style scoped>

</style>