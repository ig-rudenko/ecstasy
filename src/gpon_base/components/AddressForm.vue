<template>
  <div>

    <div class="d-flex justify-content-between">
      <div class="p-3">

        <BuildingIcon :type="address.building_type" width="128" height="128"/>

      </div>

      <div class="w-75">
        <h6 class="px-2">Регион
          <Asterisk/>
        </h6>
        <InputText v-model.trim="address.region" :class="regionClasses" type="text"
                   placeholder="Регион"/>

        <br><br>

        <h6 class="px-2">Населенный пункт
          <Asterisk/>
        </h6>
        <InputText v-model.trim="address.settlement" :class="settlementClasses" type="text"
                   placeholder="Севастополь/Балаклава/Любимовка/Верхнесадовое"/>
      </div>
    </div>

    <div class="w-100">
      <h6 class="px-2">СНТ/ТСН</h6>
      <InputText v-model.trim="address.planStructure" :class="planStructureClasses" type="text"
                 placeholder="Рыбак-7/Сатурн-2"/>
    </div>

    <br>

    <div class="w-100">
      <h6 class="px-2">Улица
        <Asterisk/>
      </h6>
      <InputText v-model.trim="address.street" :class="streetClasses" type="text"
                 placeholder="Полное название с указанием типа (улица/проспект/проезд/бульвар/шоссе/переулок/тупик)"/>
    </div>

    <div class="py-3">
      <div class="flex align-items-center py-1">
        <RadioButton v-model="address.building_type" inputId="building" value="building"/>
        <label for="building" class="ml-2"><span class="m-2">Многоквартирный дом</span></label>
      </div>
      <div class="flex align-items-center">
        <RadioButton v-model="address.building_type" inputId="house" value="house"/>
        <label for="house" class="ml-2"><span class="m-2">Частный дом</span></label>
      </div>
    </div>


    <div class="d-flex flex-wrap">
      <div class="me-3" style="width: 100px">
        <h6 class="px-2">Дом
          <Asterisk/>
        </h6>
        <InputText v-model.trim="address.house" :class="houseClasses" type="text"/>
      </div>

      <div class="me-3">
        <h6 class="px-2">Корпус</h6>
        <InputNumber :input-style="{width: '75px'}" :min="1" :max="200" v-model.number="address.block"/>
      </div>

      <template v-if="address.building_type === 'building'">
        <div class="me-3">
          <h6 class="px-2">Этажность</h6>
          <InputNumber :input-style="{width: '100px'}" :min="1" :max="200" v-model.number="address.floors"/>
        </div>

        <div class="me-3">
          <h6 class="px-2">Количество подъездов</h6>
          <InputNumber :input-style="{width: '200px'}" :min="1" :max="200" v-model.number="address.total_entrances"/>
        </div>
      </template>

    </div>

    <div style="text-align: right" class="py-3">
      <Button @click="validate" severity="success" size="small">
        Подтвердить
      </Button>
    </div>

  </div>
</template>

<script>
import InputText from "primevue/inputtext/InputText.vue"
import InputNumber from "primevue/inputnumber/InputNumber.vue"
import Button from "primevue/button/Button.vue"
import RadioButton from "primevue/radiobutton/RadioButton.vue"

import Asterisk from "./Asterisk.vue"
import BuildingIcon from "./BuildingIcon.vue";

export default {
  name: "AddressForm.vue",
  components: {
    Asterisk,
    BuildingIcon,
    InputText,
    InputNumber,
    Button,
    RadioButton,
  },
  props: {
    address: {required: true, type: Object}
  },
  data() {
    return {
      region: {valid: true},
      settlement: {valid: true},
      planStructure: {valid: true},
      street: {valid: true},
      house: {valid: true},
      block: {valid: true},
      apartment_building: {valid: true},
      floors: 1,
      total_entrances: 1
    }
  },
  computed: {
    regionClasses() {
      return ["w-100", ...this.getClasses(this.region)]
    },
    settlementClasses() {
      return ["w-100", ...this.getClasses(this.settlement)]
    },
    planStructureClasses() {
      return ["w-100", ...this.getClasses(this.planStructure)]
    },
    streetClasses() {
      return ["w-100", ...this.getClasses(this.street)]
    },
    houseClasses() {
      return ["w-100", ...this.getClasses(this.house)]
    },
  },
  methods: {
    getClasses(field) {
      if (field.valid) {
        return []
      } else {
        return ["p-invalid"]
      }
    },
    validate() {
      this.region.valid = this.address.region.length > 0
      this.settlement.valid = this.address.settlement.length > 0
      this.street.valid = this.address.street.length > 0 || this.address.planStructure.length > 0
      this.planStructure.valid = this.address.street.length > 0 || this.address.planStructure.length > 0
      this.house.valid = this.address.house.length > 0

      if (this.region.valid && this.settlement.valid && this.planStructure.valid && this.street.valid && this.house.valid) {
        this.$emit("valid")
      }
    },
  },
}
</script>

<style scoped>

</style>