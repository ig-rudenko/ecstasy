<template>
  <h6 class="px-2">Выберите существующий {{ verboseType }}
    <Asterisk/>
  </h6>
  <div v-if="!error.status" class="shadow">
    <Dropdown v-if="availableList !== null"
              v-model="connection" :options="availableList" filter showClear
              @change="(e) => {this.$emit('change', e); console.log(e);}"
              :optionLabel="getFullAddress" placeholder="Выберите" class="w-100">
      <template #value="slotProps">
        <div v-if="slotProps.value" class="flex align-items-center d-flex">
          <div>{{ getFullAddress(slotProps.value) }}</div>
        </div>
        <span v-else>
          {{ slotProps.placeholder }}
      </span>
      </template>
      <template #option="slotProps">
        <div v-if="slotProps.option" class="flex align-items-center d-flex">
          <div>{{ getFullAddress(slotProps.option) }}</div>
        </div>
      </template>
    </Dropdown>
  </div>

  <!-- ERROR -->
  <div v-else class="alert alert-danger">
    Ошибка {{error.message}}. Код ошибки {{error.status}}
  </div>
</template>

<script>
import Dropdown from "primevue/dropdown/Dropdown.vue"

import Asterisk from "./Asterisk.vue"
import formatAddress from "../../helpers/address";
import api_request from "../../api_request";

export default {
  name: "SplittersRizersFind.vue",
  components: {
    Asterisk,
    Dropdown,
  },
  props: {
    init: {required: false, default: null},
    type: {required: false, type: String, default: "both"},
    getFromOLTState: {required: false, default: null},
  },
  data() {
    return {
      connection: null,
      availableList: null,
      error: {
        status: null,
        message: null,
      }
    }
  },
  mounted() {
    let url = "/gpon/api/addresses/splitters"
    if (this.getFromOLTState){
      url += `?device=${this.getFromOLTState.deviceName}&port=${this.getFromOLTState.devicePort}`
    }
    api_request.get(url)
        .then(
          resp => this.availableList = Array.from(resp.data)
        )
        .catch(
          reason => {
            this.error.status = reason.response.status;
            this.error.message = reason.response.data;
          }
        )
  },
  updated() {
    this.connection = this.init
  },
  computed: {
    verboseType() {
      if (this.type === 'both') return "сплиттер или райзер";
      if (this.type === 'splitter') return "сплиттер";
      if (this.type === 'rizer') return "райзер";
    },
  },
  methods: {
    getFullAddress(sr) {
      if (!sr.address) return "НЕТ АДРЕСА"
      let address = formatAddress(sr.address)
      address += ` Локация: ${sr.location}. Кол-во портов: ${sr.capacity}`
      return address
    }
  }
}
</script>

<style scoped>

</style>