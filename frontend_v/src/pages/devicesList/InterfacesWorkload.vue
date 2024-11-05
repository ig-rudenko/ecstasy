<template>
  <div v-if="dev.interfaces_count && dev.interfaces_count.count">

    <div style="width: 25rem;">
      <div class="flex rounded-xl text-center">

        <!-- Абонентские порты UP С ОПИСАНИЕМ -->
        <div v-if="dev.interfaces_count.abons_up_with_desc" v-tooltip="'Абонентские порты (UP) с описанием'"
             class="bg-green-700"
             :style="{width: abonsUpWithDescPercent + '%'}" :aria-valuemax="totalCount">
          <div class="z-10 relative">{{ dev.interfaces_count.abons_up_with_desc }}</div>
        </div>

        <!-- Абонентские порты UP Без описания -->
        <div class="bg-green-500 text-gray-900"
             v-if="dev.interfaces_count.abons_up_no_desc" v-tooltip="'Абонентские порты (UP) без описания'"
             :style="{width: abonsUpNoDescPercent + '%'}" :aria-valuemax="totalCount">
          <div class="z-10 relative">{{ dev.interfaces_count.abons_up_no_desc }}</div>
        </div>

        <!-- Абонентские порты DOWN С ОПИСАНИЕМ -->
        <div class="bg-red-300 text-gray-900"
             v-if="dev.interfaces_count.abons_down_with_desc" v-tooltip="'Абонентские порты (DOWN) с описанием'"
             :style="{width: abonsDownWithDescPercent + '%'}" :aria-valuemax="totalCount">
          <div class="z-10 relative">{{ dev.interfaces_count.abons_down_with_desc }}</div>
        </div>

        <!-- Незадействованные порты -->
        <div class="bg-gray-300 text-gray-900"
             v-if="dev.interfaces_count.abons_down_no_desc" v-tooltip="'Незадействованные порты'"
             :style="{width: abonsDownNoDescPercent + '%'}" :aria-valuemax="totalCount">
          <div class="z-10 relative">{{ dev.interfaces_count.abons_down_no_desc }}</div>
        </div>

        <!-- СЛУЖЕБНЫЕ порты -->
        <div v-if="systeminterfaces_count" v-tooltip="'Служебные порты'"
             class="progress-bar bg-blue-400"
             :style="{width: systemInterfacesPercents + '%'}" :aria-valuemax="totalCount">
          <div class="z-10 relative">{{ systeminterfaces_count }}</div>
        </div>

      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';

import {Device} from "@/services/devices";

export default defineComponent({
  name: "InterfacesWorkload",
  props: {
    dev: {required: true, type: Object as PropType<Device>}
  },

  computed: {

    totalCount(): number {
      return this.dev.interfaces_count?.count || 0;
    },

    /* Абонентские порты UP С ОПИСАНИЕМ в процентах */
    abonsUpWithDescPercent(): number {
      if (this.dev.interfaces_count) {
        return this.dev.interfaces_count.abons_up_with_desc / this.totalCount * 100
      }
      return 0
    },
    /* Абонентские порты UP БЕЗ описания в процентах */
    abonsUpNoDescPercent(): number {
      if (this.dev.interfaces_count) {
        return this.dev.interfaces_count.abons_up_no_desc / this.totalCount * 100
      }
      return 0
    },
    /* Абонентские порты DOWN С описанием в процентах */
    abonsDownWithDescPercent(): number {
      if (this.dev.interfaces_count) {
        return this.dev.interfaces_count.abons_down_with_desc / this.totalCount * 100
      }
      return 0
    },
    /* Абонентские порты DOWN без описания в процентах */
    abonsDownNoDescPercent(): number {
      if (this.dev.interfaces_count) {
        return this.dev.interfaces_count.abons_down_no_desc / this.totalCount * 100
      }
      return 0
    },
    /* Служебные порты в процентах */
    systemInterfacesPercents(): number {
      if (this.dev.interfaces_count) {
        return this.systeminterfaces_count / this.totalCount * 100
      }
      return 0
    },

    systeminterfaces_count(): number {
      if (this.dev.interfaces_count) {
        const i = this.dev.interfaces_count;
        return i.count - (i.abons_up + i.abons_down)
      }
      return 0
    }
  }
})
</script>

<style scoped>

</style>