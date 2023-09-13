<template>
  <div v-if="!show_new_address_form">
    <h6 class="px-2">Выберите существующий адрес дома
      <Asterisk/>
    </h6>
    <div class="shadow">
      <Dropdown v-model="data.address" :options="addressesList()" filter showClear
                :class="formState.address.valid?[]:['p-invalid']"
                :optionLabel="getFullAddress" placeholder="Выберите" class="w-100">
        <template #value="slotProps">
          <div v-if="slotProps.value" class="flex align-items-center d-flex">
            <BuildingIcon :type="slotProps.value.building_type" width="24" height="24"></BuildingIcon>
            <div>{{ getFullAddress(slotProps.value) }}</div>
          </div>
          <span v-else>
            {{ slotProps.placeholder }}
        </span>
        </template>
        <template #option="slotProps">
          <div v-if="slotProps.option" class="flex align-items-center d-flex">
            <BuildingIcon :type="slotProps.option.building_type" width="24" height="24"></BuildingIcon>
            <div>{{ getFullAddress(slotProps.option) }}</div>
          </div>
        </template>
      </Dropdown>
    </div>

    <Button @click="show_new_address_form=true" severity="success" size="small">
      Редактировать
    </Button>

  </div>

  <Dialog v-model:visible="show_new_address_form" modal header="Добавление нового адреса"
          :style="{ width: isMobile?'100vw':'50vw' }">
    <AddressForm @valid="validNewAddress" @dismiss="dismissNewAddress"
                 :address="data.address||getNewAddress()"></AddressForm>
  </Dialog>

</template>

<script>
import Button from "primevue/button/Button.vue"
import Dialog from "primevue/dialog/Dialog.vue"
import Dropdown from "primevue/dropdown/Dropdown.vue"

import AddressForm from "./AddressForm.vue"
import Asterisk from "./Asterisk.vue"
import BuildingIcon from "./BuildingIcon.vue"
import formatAddress from "../../helpers/address";

export default {
  name: "AddressGetCreate.vue",
  components: {
    AddressForm,
    Button,
    Dialog,
    Dropdown,
    Asterisk,
    BuildingIcon,
  },

  props: {
    isMobile: {required: true, type: Boolean},
    data: {required: true, type: Object},
  },

  data() {
    return {
      show_new_address_form: false,
      formState: {
        address: {valid: true},
        isValid() {
          return this.address.valid
        }
      }
    }
  },

  methods: {
    getFullAddress(address) {
      return formatAddress(address)
    },

    validNewAddress(newAddress) {
      this.show_new_address_form = false
      this.formState.address.valid = true
      this.data.address = newAddress
    },

    dismissNewAddress() {
      this.show_new_address_form = false
      this.data.address = null
    },

    addressesList() {
      let allAddresses = [
        {
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
        },
        {
          id: 2,
          region: "Севастополь",
          settlement: "Севастополь",
          planStructure: "",
          street: "улица Колобова",
          house: "22",
          block: null,
          building_type: 'building',
          floors: 1,
          total_entrances: 1
        },
        {
          id: 3,
          region: "Севастополь",
          settlement: "Севастополь",
          planStructure: "",
          street: "проспект Генерала Острякова",
          house: "222а",
          block: 2,
          building_type: 'building',
          floors: 1,
          total_entrances: 1
        },
        {
          id: 4,
          region: "Севастополь",
          settlement: "Севастополь",
          planStructure: "Рыбак-7",
          street: "",
          house: "123",
          block: null,
          building_type: 'house',
          floors: 1,
          total_entrances: 1
        },
      ]
      if (this.formState.isValid()) {
        allAddresses = [this.data.address, ...allAddresses]
      }
      return allAddresses
    },

    getNewAddress() {
      return {
        region: "Севастополь",
        settlement: "Севастополь",
        planStructure: "",
        street: "",
        house: "",
        block: null,
        building_type: "building",
        floors: 1,
        total_entrances: 1
      }
    }

  }
}
</script>

<style scoped>

</style>