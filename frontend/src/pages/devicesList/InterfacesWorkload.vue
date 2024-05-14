<template>
  <div v-if="dev.interfacesCount && dev.interfacesCount.count">

    <div style="width: 25rem;">
      <div class="progress">

        <!-- Абонентские порты UP С ОПИСАНИЕМ -->
        <div v-if="dev.interfacesCount.abonsUpWithDesc" v-tooltip="'Абонентские порты (UP) с описанием'"
             class="progress-bar bg-success" role="progressbar"
             :style="{width: abonsUpWithDescPercent + '%'}" :aria-valuemax="totalCount">
          {{ dev.interfacesCount.abonsUpWithDesc }}
        </div>

        <!-- Абонентские порты UP Без описания -->
        <div class="progress-bar" role="progressbar" style="background-color: #74bf9c"
             v-if="dev.interfacesCount.abonsUpNoDesc" v-tooltip="'Абонентские порты (UP) без описания'"
             :style="{width: abonsUpNoDescPercent + '%'}" :aria-valuemax="totalCount">
          {{ dev.interfacesCount.abonsUpNoDesc }}
        </div>

        <!-- Абонентские порты DOWN С ОПИСАНИЕМ -->
        <div class="progress-bar text-dark" role="progressbar" style="background-color: #ffbdbd"
             v-if="dev.interfacesCount.abonsDownWithDesc" v-tooltip="'Абонентские порты (DOWN) с описанием'"
             :style="{width: abonsDownWithDescPercent + '%'}" :aria-valuemax="totalCount">
          {{ dev.interfacesCount.abonsDownWithDesc }}
        </div>

        <!-- Незадействованные порты -->
        <div class="progress-bar text-dark" role="progressbar" style="background-color: #cfcfcf"
             v-if="dev.interfacesCount.abonsDownNoDesc" v-tooltip="'Незадействованные порты'"
             :style="{width: abonsDownNoDescPercent + '%'}" :aria-valuemax="totalCount">
          {{ dev.interfacesCount.abonsDownNoDesc }}
        </div>

        <!-- СЛУЖЕБНЫЕ порты -->
        <div v-if="systemInterfacesCount" v-tooltip="'Служебные порты'"
             class="progress-bar bg-info" role="progressbar"
             :style="{width: systemInterfacesPercents + '%'}" :aria-valuemax="totalCount">
          {{ systemInterfacesCount }}
        </div>

      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent} from 'vue'
import {Device} from "./devices";

export default defineComponent({
  name: "InterfacesWorkload",
  props: {
    dev: {required: true, type: Device}
  },

  computed: {

    totalCount(): number {
      return this.dev.interfacesCount?.count || 0;
    },

    /* Абонентские порты UP С ОПИСАНИЕМ в процентах */
    abonsUpWithDescPercent(): number {
      if (this.dev.interfacesCount) {
        return this.dev.interfacesCount.abonsUpWithDesc / this.totalCount * 100
      }
      return 0
    },
    /* Абонентские порты UP БЕЗ описания в процентах */
    abonsUpNoDescPercent(): number {
      if (this.dev.interfacesCount) {
        return this.dev.interfacesCount.abonsUpNoDesc / this.totalCount * 100
      }
      return 0
    },
    /* Абонентские порты DOWN С описанием в процентах */
    abonsDownWithDescPercent(): number {
      if (this.dev.interfacesCount) {
        return this.dev.interfacesCount.abonsDownWithDesc / this.totalCount * 100
      }
      return 0
    },
    /* Абонентские порты DOWN без описания в процентах */
    abonsDownNoDescPercent(): number {
      if (this.dev.interfacesCount) {
        return this.dev.interfacesCount.abonsDownNoDesc / this.totalCount * 100
      }
      return 0
    },
    /* Служебные порты в процентах */
    systemInterfacesPercents(): number {
      if (this.dev.interfacesCount) {
        return this.systemInterfacesCount / this.totalCount * 100
      }
      return 0
    },

    systemInterfacesCount(): number {
      if (this.dev.interfacesCount) {
        const i = this.dev.interfacesCount;
        return i.count - (i.abonsUp + i.abonsDown)
      }
      return 0
    }
  }
})
</script>

<style scoped>

</style>