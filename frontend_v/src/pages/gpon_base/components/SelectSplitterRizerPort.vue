<template>
  <h6 class="px-2">Выберите {{ verboseType }}
    <Asterisk/>
  </h6>
  <Select v-model="selectedPort" :options="capability" filter showClear
          @change="e => $emit('change', e)"
          :class="valid?['w-100']:['p-invalid', 'w-100']"
          optionLabel="port" placeholder="Выберите" class="w-100">
    <template #value="slotProps">
      <div v-if="slotProps.value" class="flex align-items-center d-flex">
        <div>{{ slotProps.value.number }}
          <TechCapabilityBadge :status="slotProps.value.status"/>
        </div>
      </div>
      <span v-else>
        {{ slotProps.placeholder }}
    </span>
    </template>
    <template #option="slotProps">
      <div v-if="slotProps.option" class="flex align-items-center d-flex">
        <div>{{ slotProps.option.number }}
          <TechCapabilityBadge :status="slotProps.option.status"/>
        </div>
      </div>
    </template>
  </Select>
</template>

<script>
import TechCapabilityBadge from "./TechCapabilityBadge.vue";

import Asterisk from "./Asterisk.vue";
import api from "@/services/api";

export default {
  name: "SelectSplittersRizersPort.vue",
  components: {
    Asterisk,
    TechCapabilityBadge,
  },
  props: {
    type: {required: true, type: String,},
    getFrom: {required: true, type: Object},
    end3ID: {required: true, type: Number},
    init: {required: false, default: null},
    onlyUnusedPorts: {required: false, type: Boolean, default: false},
    valid: {required: false, type: Boolean, default: true},
  },

  data() {
    return {
      selectedPort: null,
      _capability: [],
      _initEnd3ID: null,
    }
  },

  mounted() {
    this.getPorts()
    this.selectedPort = this.init
    this._initEnd3ID = this.end3ID
  },

  updated() {
    if (this.end3ID !== this._initEnd3ID) {
      this.getPorts()
      this._initEnd3ID = this.end3ID
    }
  },

  computed: {

    capability() {
      const onlyUnusedPorts = this.onlyUnusedPorts

      return this._capability.filter(
          elem => {
            if (onlyUnusedPorts) {
              return elem.status === "empty"
            }
            return true
          }
      )
    },

    verboseType() {
      if (this.type === 'splitter') return "порт сплиттера";
      if (this.type === 'rizer') return "волокно райзера";
    },

  },
  methods: {
    getPorts() {
      api.get("/gpon/api/tech-data/end3/" + this.end3ID)
          .then(
              resp => this._capability = Array.from(resp.data.capability)
          )
          .catch(
              reason => {
                this.error.status = reason.response.status;
                this.error.message = reason.response.data;
              }
          )
    }
  }
}
</script>
