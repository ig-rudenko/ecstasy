<template>
  <div v-if="totalCount" class="py-4">
    <p>Загруженность интерфейсов</p>
    <div class="progress shadow" style="height: 25px;">
      <div class="progress-bar bg-success" role="progressbar" :style="style_up_with_desc">
        {{ workload.abons_up_with_desc }}
      </div>
      <div class="progress-bar" role="progressbar" :style="style_up_no_desc">{{ workload.abons_up_no_desc }}</div>
      <div class="progress-bar text-dark" role="progressbar" :style="style_down_with_desc">
        {{ workload.abons_down_with_desc }}
      </div>
      <div class="progress-bar text-dark" role="progressbar" :style="style_down_no_desc">
        {{ workload.abons_down_no_desc }}
      </div>
      <div class="progress-bar bg-info" role="progressbar" :style="style_systems">{{ systemsInterfacesCount }}
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import {InterfacesCount} from "@/services/interfaces";

export default defineComponent({
  props: {
    workload: {required: true, type: Object as PropType<InterfacesCount>}
  },
  computed: {
    totalCount() {
      return this.workload.count;
    },

    style_up_with_desc() {
      return {'width': this.workload.abons_up_with_desc / this.totalCount * 100 + '%', height: '25px'}
    },
    style_up_no_desc() {
      return {
        'background-color': 'rgb(116, 191, 156)',
        'width': this.workload.abons_up_no_desc / this.totalCount * 100 + '%',
        height: '25px'
      }
    },
    style_down_with_desc() {
      return {
        'background-color': 'rgb(255, 189, 189)',
        'width': this.workload.abons_down_with_desc / this.totalCount * 100 + '%',
        height: '25px'
      }
    },
    style_down_no_desc() {
      return {
        'background-color': 'rgb(207, 207, 207)',
        'width': this.workload.abons_down_no_desc / this.totalCount * 100 + '%',
        height: '25px'
      }
    },
    style_systems() {
      return {'width': this.systemsInterfacesCount / this.totalCount * 100 + '%', height: '25px'}
    },

    systemsInterfacesCount() {
      const w = this.workload;
      return w.count - (w.abons_up + w.abons_down);
    }
  }
})
</script>