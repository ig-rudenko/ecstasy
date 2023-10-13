<template>
  <div v-if="!show_new_address_form">
    <h6 v-if="isSubscriberAddress" class="px-2">Укажите адрес подключения <Asterisk/></h6>
    <h6 v-else class="px-2">Выберите существующий адрес дома <Asterisk/></h6>

    <div class="p-inputgroup flex-1">
      <Dropdown v-model="data.address" :options="addressesList()" filter showClear
                :class="formState.address.valid?[]:['p-invalid']"
                @change="(e) => {this.$emit('change', e)}"
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

      <Button v-if="allowCreate" @click="show_new_address_form=true" severity="success" size="small">
        Добавить/Редактировать
      </Button>

    </div>

  </div>

  <Dialog v-model:visible="show_new_address_form" modal header="Добавление нового адреса"
          :style="{ width: isMobile?'100vw':'50vw' }">
    <AddressForm @valid="validNewAddress" @dismiss="dismissNewAddress"
                 :subscriber-address="isSubscriberAddress"
                 :init-address="data.address||getNewAddress()"></AddressForm>
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
import api_request from "../../api_request";

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
    allowCreate: {required: false, default: true},
    getFromDevicePort: {required: false, default: null},
    isSubscriberAddress: {required: false, default: false},
  },

  data() {
    return {
      show_new_address_form: false,
      _addresses: [],
      formState: {
        address: {valid: true},
        isValid() {
          return this.address.valid
        }
      },
      _initData: null
    }
  },

  mounted() {
    this.getAddresses()
    this._initData = this.getFromDevicePort
  },

  updated() {
    // Если поменялись входные данные фильтра по названию оборудования и порта, то ищем адреса еще раз
    if (
        this.getFromDevicePort &&
        (this._initData.deviceName !== this.getFromDevicePort.deviceName
            || this._initData.devicePort !== this.getFromDevicePort.devicePort)
    ){
      this.getAddresses()
      this._initData = this.getFromDevicePort
    }
  },

  methods: {
    getFullAddress(address) {
      let address_string = formatAddress(address)
      if (this.isSubscriberAddress && address.building_type === "building") {
        address_string += ` (${address.floor} этаж) кв. ${address.apartment}`
      }
      return address_string
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

    getAddresses() {
      let url = "/gpon/api/addresses/buildings"
      if (this.getFromDevicePort){
        url += `?device=${this.getFromDevicePort.deviceName}&port=${this.getFromDevicePort.devicePort}`
      }
      api_request.get(url).then(resp => this._addresses = resp.data)
    },

    addressesList() {
      let allAddresses = this._addresses
      if (this.formState.isValid() && this.allowCreate) {
        allAddresses = [this.data.address, ...this._addresses]
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