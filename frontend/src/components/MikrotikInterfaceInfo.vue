<template>

<!--  POE   -->
<div v-if="data.poeStatus">
  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" :fill="data.poeStatus==='off'?'grey':'orange'"
       class="bi bi-lightning-charge-fill me-2" viewBox="0 0 16 16">
    <path d="M11.251.068a.5.5 0 0 1 .227.58L9.677 6.5H13a.5.5 0 0 1 .364.843l-8 8.5a.5.5 0 0 1-.842-.49L6.323 9.5H3a.5.5 0 0 1-.364-.843l8-8.5a.5.5 0 0 1 .615-.09z"></path>
  </svg>
  <span style="vertical-align: middle;" class="me-2">PoE:</span>

  <select v-model="newPoeStatus" class="form-select" style="width: 150px; display: inline; vertical-align: middle;">
    <option v-for="poe in data.poeChoices" :value="poe">{{ poe }}</option>
  </select>

  <button @click="changePoEStatus" class="btn btn-outline-success">
    <svg v-show="!changingPoEStatusNow" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
      <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/>
    </svg>
    <span v-show="changingPoEStatusNow" class="spinner-border" style="height: 24px;width: 24px;"></span>
  </button>
</div>
<!-- / POE  -->

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import Interface from "../types/interfaces";
import api_request from "../api_request";
import {AxiosResponse} from "axios";

interface Poe {
  poeStatus: string
  poeChoices: string[]
}

export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    data: {required: true, type: Object as PropType<Poe>},
    interface: {required: true, type: Object as PropType<Interface>},
  },
  data() {
    return {
      newPoeStatus: this.data.poeStatus,
      poeChangeSuccess: null as boolean|null,
      changingPoEStatusNow: false
    }
  },
  methods: {
    changePoEStatus() {
      let data = {port: this.interface.name, status: this.newPoeStatus}

      this.changingPoEStatusNow = true
      api_request.post("/device/api/" + this.deviceName + "/set-poe-out", data)
          .then(
              (value: AxiosResponse) => {
                this.poeChangeSuccess = value.status === 200;
                this.changingPoEStatusNow = false
              }
          )
    },
  }
})
</script>