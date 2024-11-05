<template>
  <div v-if="totalCount">
    <div class="pb-2">Загруженность интерфейсов</div>
    <div class="text-center flex shadow-xl rounded">
      <div class="bg-green-700 rounded" :style="style_up_with_desc">{{ workload.abons_up_with_desc }}</div>
      <div class="bg-green-500 rounded" :style="style_up_no_desc">{{ workload.abons_up_no_desc }}</div>
      <div class="bg-red-300 rounded" :style="style_down_with_desc">{{ workload.abons_down_with_desc }}</div>
      <div class="bg-gray-300 rounded" :style="style_down_no_desc">{{ workload.abons_down_no_desc }}</div>
      <div class="bg-blue-400 rounded" :style="style_systems">{{ systemsInterfacesCount }}</div>
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
        'width': this.workload.abons_up_no_desc / this.totalCount * 100 + '%',
        height: '25px'
      }
    },
    style_down_with_desc() {
      return {
        'width': this.workload.abons_down_with_desc / this.totalCount * 100 + '%',
        height: '25px'
      }
    },
    style_down_no_desc() {
      return {
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