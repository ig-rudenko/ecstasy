<template>
  <div v-if="totalCount">
    <div class="pb-2">Загруженность интерфейсов</div>
    <div class="text-center flex shadow-xl rounded">
      <div v-if="workload.abons_up_with_desc"
           class="text-white text-sm bg-green-700 first:rounded-l-xl last:rounded-r-xl"
           :style="style_up_with_desc">{{ workload.abons_up_with_desc }}
      </div>
      <div v-if="workload.abons_up_no_desc"
           class="text-sm text-gray-950 bg-green-500 first:rounded-l-xl last:rounded-r-xl"
           :style="style_up_no_desc">{{ workload.abons_up_no_desc }}
      </div>
      <div v-if="workload.abons_down_with_desc"
           class="text-sm text-gray-950 bg-red-300 first:rounded-l-xl last:rounded-r-xl"
           :style="style_down_with_desc">{{ workload.abons_down_with_desc }}
      </div>
      <div v-if="workload.abons_down_no_desc"
           class="text-sm text-gray-950 bg-gray-300 first:rounded-l-xl last:rounded-r-xl"
           :style="style_down_no_desc">{{ workload.abons_down_no_desc }}
      </div>
      <div v-if="systemsInterfacesCount" class="text-sm text-gray-950 bg-blue-400 first:rounded-l-xl last:rounded-r-xl"
           :style="style_systems">
        {{ systemsInterfacesCount }}
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
      return {'width': this.workload.abons_up_with_desc / this.totalCount * 100 + '%'}
    },
    style_up_no_desc() {
      return {'width': this.workload.abons_up_no_desc / this.totalCount * 100 + '%'}
    },
    style_down_with_desc() {
      return {'width': this.workload.abons_down_with_desc / this.totalCount * 100 + '%'}
    },
    style_down_no_desc() {
      return {'width': this.workload.abons_down_no_desc / this.totalCount * 100 + '%'}
    },
    style_systems() {
      return {'width': this.systemsInterfacesCount / this.totalCount * 100 + '%'}
    },

    systemsInterfacesCount() {
      const w = this.workload;
      return w.count - (w.abons_up + w.abons_down);
    }
  }
})
</script>