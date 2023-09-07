<template>
  <div>

    <div class="d-flex justify-content-between">
      <div class="p-3">

        <svg v-if="address.apartment_building === 'true'"
             xmlns="http://www.w3.org/2000/svg" width="128" height="128" fill="currentColor" class="me-2"
             viewBox="0 0 16 16">
          <path
              d="M15 .5a.5.5 0 0 0-.724-.447l-8 4A.5.5 0 0 0 6 4.5v3.14L.342 9.526A.5.5 0 0 0 0 10v5.5a.5.5 0 0 0 .5.5h9a.5.5 0 0 0 .5-.5V14h1v1.5a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5V.5ZM2 11h1v1H2v-1Zm2 0h1v1H4v-1Zm-1 2v1H2v-1h1Zm1 0h1v1H4v-1Zm9-10v1h-1V3h1ZM8 5h1v1H8V5Zm1 2v1H8V7h1ZM8 9h1v1H8V9Zm2 0h1v1h-1V9Zm-1 2v1H8v-1h1Zm1 0h1v1h-1v-1Zm3-2v1h-1V9h1Zm-1 2h1v1h-1v-1Zm-2-4h1v1h-1V7Zm3 0v1h-1V7h1Zm-2-2v1h-1V5h1Zm1 0h1v1h-1V5Z"/>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="128" height="128" fill="currentColor" class="me-2"
             viewBox="0 0 16 16">
          <path
              d="M8.707 1.5a1 1 0 0 0-1.414 0L.646 8.146a.5.5 0 0 0 .708.708L8 2.207l6.646 6.647a.5.5 0 0 0 .708-.708L13 5.793V2.5a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5v1.293L8.707 1.5Z"/>
          <path d="m8 3.293 6 6V13.5a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 2 13.5V9.293l6-6Z"/>
        </svg>

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
      <InputText v-model.trim="address.planStructure" class="w-100" type="text"
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
        <RadioButton v-model="address.apartment_building" inputId="apartment_building" name="pizza" value="true"/>
        <label for="apartment_building" class="ml-2"><span class="m-2">Многоквартирный дом</span></label>
      </div>
      <div class="flex align-items-center">
        <RadioButton v-model="address.apartment_building" inputId="private_house" name="pizza" value="false"/>
        <label for="private_house" class="ml-2"><span class="m-2">Частный дом</span></label>
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

      <template v-if="address.apartment_building === 'true'">
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

export default {
  name: "AddressForm.vue",
  components: {
    Asterisk,
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
      this.street.valid = this.address.street.length > 0
      this.house.valid = this.address.house.length > 0

      if (this.region.valid && this.settlement.valid && this.street.valid && this.house.valid) {
        this.$emit("valid")
      }
    },
  },
}
</script>

<style scoped>

</style>