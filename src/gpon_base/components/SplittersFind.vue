<template>
  <h6 class="px-2">Выберите существующий сплиттер
    <Asterisk/>
  </h6>
  <div class="shadow">
    <Dropdown v-model="splitter" :options="availableSplitters" filter showClear
              :optionLabel="getSplitterFullAddress" placeholder="Выберите" class="w-100">
      <template #value="slotProps">
        <div v-if="slotProps.value" class="flex align-items-center d-flex">
          <div>{{ getSplitterFullAddress(slotProps.value) }}</div>
        </div>
        <span v-else>
          {{ slotProps.placeholder }}
      </span>
      </template>
      <template #option="slotProps">
        <div v-if="slotProps.option" class="flex align-items-center d-flex">
          <div>{{ getSplitterFullAddress(slotProps.option) }}</div>
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
  name: "SplittersFind.vue",
  components: {
    Asterisk,
    Dropdown,
  },
  props: {
    initSplitter: {required: false, default: null}
  },
  data() {
    return {
      _splitter: null
    }
  },
  mounted() {
    this._splitter = this.initSplitter
  },
  computed: {
    splitter: {
      set(value) {
        this._splitter = value
        this.$emit("selected", this._splitter)
      },
      get() {
        return this._splitter
      }
    },

    availableSplitters() {
      return [
        {
          id: 1,
          location: "На столбе слева",
          capacity: 8,
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
    getSplitterFullAddress(sp) {
      if (!sp.address) return "НЕТ АДРЕСА"
      let address = formatAddress(sp.address)
      address += ` Локация: ${sp.location}. Кол-во портов: ${sp.capacity}`
      return address
    }
  }
}
</script>

<style scoped>

</style>