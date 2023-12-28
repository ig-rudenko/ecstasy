<template>
  <button class="btn" @mouseover="showHelpText=true" @mouseleave="showHelpText=false">
    <a v-if="interface.graphsLink" :href="interface.graphsLink" target="_blank">
      <svg :fill="interface.graphsLink?'#63af4f':'#d5d5d5'" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
           class="bi bi-graph-up" viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M0 0h1v15h15v1H0V0Zm14.817 3.113a.5.5 0 0 1 .07.704l-4.5 5.5a.5.5 0 0 1-.74.037L7.06 6.767l-3.656 5.027a.5.5 0 0 1-.808-.588l4-5.5a.5.5 0 0 1 .758-.06l2.609 2.61 4.15-5.073a.5.5 0 0 1 .704-.07Z"></path>
      </svg>
    </a>
    <svg v-else :fill="interface.graphsLink?'#63af4f':'#d5d5d5'" xmlns="http://www.w3.org/2000/svg" width="24"
         height="24"
         class="bi bi-graph-up" viewBox="0 0 16 16">
      <path fill-rule="evenodd"
            d="M0 0h1v15h15v1H0V0Zm14.817 3.113a.5.5 0 0 1 .07.704l-4.5 5.5a.5.5 0 0 1-.74.037L7.06 6.767l-3.656 5.027a.5.5 0 0 1-.808-.588l4-5.5a.5.5 0 0 1 .758-.06l2.609 2.61 4.15-5.073a.5.5 0 0 1 .704-.07Z"></path>
    </svg>

    <span v-show="showHelpText" :class="helpTextClasses">
      {{ helpText }}
    </span>
  </button>
</template>

<script lang="ts">
import {PropType} from "vue";

interface InterfaceGraphs { graphsLink: string }

export default {
  name: "graphsLink",
  props: {
    interface: {
      required: true, type: Object as PropType<InterfaceGraphs>
    }
  },
  data() {
    return {
      showHelpText: false
    }
  },
  computed: {
    helpTextClasses() {
      if (this.interface.graphsLink) {
        return ["badge", "bg-success", "graphs-help-text"]
      } else {
        return ["badge", "bg-secondary", "graphs-help-text"]
      }
    },
    helpText() {
      if (this.interface.graphsLink) {
        return "Графики"
      } else {
        return "Нет графиков"
      }
    }
  }
}
</script>

<style scoped>
.graphs-help-text {
  position: absolute;
  display: inline;
  top: 7px;
  margin-left: 7px;
}
</style>