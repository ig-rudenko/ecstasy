<template>

  <!--  POE   -->
  <div v-if="data.poeStatus" class="flex gap-2 items-center">
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" :fill="data.poeStatus==='off'?'grey':'orange'"
         class="bi bi-lightning-charge-fill me-2" viewBox="0 0 16 16">
      <path
          d="M11.251.068a.5.5 0 0 1 .227.58L9.677 6.5H13a.5.5 0 0 1 .364.843l-8 8.5a.5.5 0 0 1-.842-.49L6.323 9.5H3a.5.5 0 0 1-.364-.843l8-8.5a.5.5 0 0 1 .615-.09z"></path>
    </svg>
    <span style="vertical-align: middle;" class="me-2">PoE:</span>

    <Select v-model="newPoeStatus" :options="data.poeChoices" />

    <Button @click="changePoEStatus" severity="success" icon="pi pi-check" :loading="changingPoEStatusNow" />
  </div>
  <!-- / POE  -->

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import api from "@/services/api";
import {AxiosResponse} from "axios";
import {DeviceInterface} from "@/services/interfaces.ts";
import {errorToast} from "@/services/my.toast.ts";
import errorFmt from "@/errorFmt.ts";

interface Poe {
  poeStatus: string
  poeChoices: string[]
}

export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    data: {required: true, type: Object as PropType<Poe>},
    interface: {required: true, type: Object as PropType<DeviceInterface>},
  },
  data() {
    return {
      newPoeStatus: this.data.poeStatus,
      poeChangeSuccess: null as boolean | null,
      changingPoEStatusNow: false
    }
  },
  methods: {
    async changePoEStatus() {
      let data = {port: this.interface.name, status: this.newPoeStatus}

      this.changingPoEStatusNow = true
      try {
        await api.post("/device/api/" + this.deviceName + "/set-poe-out", data)
        this.poeChangeSuccess = true;
      } catch (error: any) {
        errorToast("Ошибка измененини PoE", errorFmt(error))
      }
      this.changingPoEStatusNow = false
    },
  }
})
</script>