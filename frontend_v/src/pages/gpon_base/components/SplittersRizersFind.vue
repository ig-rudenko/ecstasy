<template>
  <div class="px-2 flex items-center gap-2 pb-2">Выберите существующий {{ verboseType }}
    <Asterisk/>
  </div>

  <Select v-if="!error.status && availableList !== null"
          v-model="connection" :options="availableList" filter showClear fluid
          :class="valid?['w-full']:['p-invalid', 'w-full']"
          :virtualScrollerOptions="{ itemSize: 38 }"
          @change="e => $emit('change', e)"
          :optionLabel="getFullAddress" placeholder="Выберите" class="w-full">
    <template #value="slotProps">
      <div v-if="slotProps.value" class="flex items-center">
        <div>{{ getFullAddress(slotProps.value) }}</div>
      </div>
      <span v-else>
        {{ slotProps.placeholder }}
    </span>
    </template>
    <template #option="slotProps">
      <div v-if="slotProps.option" class="items-center flex">
        <div>{{ getFullAddress(slotProps.option) }}</div>
      </div>
    </template>
  </Select>

  <!-- ERROR -->
  <Message v-else severity="error">
    Ошибка {{ error.message }}. Код ошибки {{ error.status }}
  </Message>
</template>

<script>
import Asterisk from "./Asterisk.vue"

import api from "@/services/api";
import {formatAddress} from "@/formats";

export default {
  name: "SplittersRizersFind",
  components: {
    Asterisk,
  },
  props: {
    init: {required: false, default: null},
    type: {required: false, type: String, default: "both"},
    fromAddressID: {required: false, default: null},
    valid: {required: false, type: Boolean, default: true},
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
    let url = "/gpon/api/addresses/end3"
    if (this.fromAddressID) {
      url += "?address_id=" + this.fromAddressID
    }
    api.get(url)
        .then(
            resp => this.availableList = Array.from(resp.data)
        )
        .catch(
            reason => {
              this.error.status = reason.response.status;
              this.error.message = reason.response.data;
            }
        )
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