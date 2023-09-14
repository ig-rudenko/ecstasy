<template>
  <h6 class="px-2">Выберите существующий {{ verboseType }}
    <Asterisk/>
  </h6>
  <div class="shadow">
    <Dropdown v-model="connection" :options="availableList" filter showClear
              @change="(e) => {this.$emit('change', e)}"
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
</template>

<script>
import Dropdown from "primevue/dropdown/Dropdown.vue"

import Asterisk from "./Asterisk.vue"
import formatAddress from "../../helpers/address";

export default {
  name: "SplittersRizersFind.vue",
  components: {
    Asterisk,
    Dropdown,
  },
  props: {
    init: {required: false, default: null},
    type: {required: false, type: String, default: "both"},
    getFromHouseAddress: {required: false, default: null},
  },
  data() {
    return {
      connection: null
    }
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

    availableList() {
      return [
        {
          id: 1,
          location: "На столбе слева",
          capacity: 8,
          type: "splitter",
          address: {
            id: 1,
            region: "Севастополь",
            settlement: "Сахарная головка",
            planStructure: "",
            street: "улица Тракторная",
            house: "2",
            block: null,
            building_type: 'house',
            floors: 1,
            total_entrances: 1
          }
        },
        {
          id: 2,
          location: "На столбе справа",
          capacity: 8,
          type: "splitter",
          address: {
            id: 1,
            region: "Севастополь",
            settlement: "Сахарная головка",
            planStructure: "",
            street: "улица Тракторная",
            house: "22",
            block: null,
            building_type: 'house',
            floors: 1,
            total_entrances: 1
          }
        },
        {
          id: 3,
          location: "На чердаке",
          capacity: 8,
          type: "splitter",
          address: {
            id: 1,
            region: "Севастополь",
            settlement: "Сахарная головка",
            planStructure: "",
            street: "улица Тракторная",
            house: "65",
            block: null,
            building_type: 'house',
            floors: 1,
            total_entrances: 1
          }
        },
        {
          id: 4,
          location: "в колодце",
          capacity: 8,
          type: "splitter",
          address: {
            id: 1,
            region: "Севастополь",
            settlement: "Сахарная головка",
            planStructure: "",
            street: "улица Тракторная",
            house: "11",
            block: null,
            building_type: 'house',
            floors: 1,
            total_entrances: 1
          }
        },
      ]
    }
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