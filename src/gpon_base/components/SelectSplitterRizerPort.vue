<template>
  <h6 class="px-2">Выберите {{ verboseType }}
    <Asterisk/>
  </h6>
  <div class="shadow">
    <Dropdown v-model="selectedPort" :options="availablePorts" filter showClear
              @change="(e) => {this.$emit('change', e)}"
              optionLabel="port" placeholder="Выберите" class="w-100">
      <template #value="slotProps">
        <div v-if="slotProps.value" class="flex align-items-center d-flex">
          <div>{{ slotProps.value.port }}</div>
        </div>
        <span v-else>
          {{ slotProps.placeholder }}
      </span>
      </template>
      <template #option="slotProps">
        <div v-if="slotProps.option" class="flex align-items-center d-flex">
          <div>{{ slotProps.option.port }}</div>
        </div>
      </template>
    </Dropdown>
  </div>
</template>

<script>
import Dropdown from "primevue/dropdown/Dropdown.vue";

import Asterisk from "./Asterisk.vue";

export default {
  name: "SelectSplittersRizersPort.vue",
  components: {
    Asterisk,
    Dropdown,
  },
  props: {
    type: {required: true, type: String,},
    getFrom: {required: true, type: Object},
    init: {required: false, default: null},
    onlyUnusedPorts: {required: false, type: Boolean, default: false},
  },
  data() {
    return {
      selectedPort: null
    }
  },
  updated() {
    this.selectedPort = this.init
  },
  computed: {

    verboseType() {
      if (this.type === 'splitter') return "порт сплиттера";
      if (this.type === 'rizer') return "волокно райзера";
    },

    availablePorts() {
      return [
        {
          id: 11,
          port: 1
        },
        {
          id: 12,
          port: 2
        },
        {
          id: 13,
          port: 3
        },
        {
          id: 14,
          port: 4
        },
        {
          id: 15,
          port: 5
        },
        {
          id: 16,
          port: 6
        },
        {
          id: 17,
          port: 7
        },
        {
          id: 18,
          port: 8
        },
      ]
    }
  },
  methods: {}
}
</script>

<style scoped>

</style>