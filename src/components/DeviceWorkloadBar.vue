<template>
  <div v-if="workload.count" class="py-4">
    <p>Загруженность интерфейсов</p>
    <div class="progress shadow" style="height: 25px;">
      <div class="progress-bar bg-success" role="progressbar" :style="style_up_with_desc">{{this.workload.abons_up_with_desc}}</div>
      <div class="progress-bar" role="progressbar" :style="style_up_no_desc">{{this.workload.abons_up_no_desc}}</div>
      <div class="progress-bar text-dark" role="progressbar" :style="style_down_with_desc">{{this.workload.abons_down_with_desc}}</div>
      <div class="progress-bar text-dark" role="progressbar" :style="style_down_no_desc">{{this.workload.abons_down_no_desc}}</div>
    </div>
  </div>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
    workload: {
      required: true
    }
  },
  computed: {
    style_up_with_desc() {
      return {'width': this.workload.abons_up_with_desc / this.workload.abons * 100 + '%', height: '25px'}
    },
    style_up_no_desc() {
      return {'background-color': 'rgb(116, 191, 156)', 'width': this.workload.abons_up_no_desc / this.workload.abons * 100 + '%', height: '25px'}
    },
    style_down_with_desc() {
      return {'background-color': 'rgb(255, 189, 189)', 'width': this.workload.abons_down_with_desc / this.workload.abons * 100 + '%', height: '25px'}
    },
    style_down_no_desc() {
      return {'background-color': 'rgb(207, 207, 207)', 'width': this.workload.abons_down_no_desc / this.workload.abons * 100 + '%', height: '25px'}
    }
  }
})
</script>