<template>
  <div>

    <div class="flex justify-between gap-4">
      <div class="p-3">
        <BuildingIcon :type="address.building_type" width="128" height="128"/>
      </div>

      <div class="w-full flex flex-col gap-2">
        <h6 class="px-2 flex items-center gap-1">
          Регион
          <Asterisk/>
        </h6>
        <InputText v-model.trim="address.region" :class="regionClasses" fluid
                   placeholder="Регион"/>

        <h6 class="px-2 flex items-center gap-1">
          Населенный пункт
          <Asterisk/>
        </h6>
        <InputText v-model.trim="address.settlement" :class="settlementClasses" fluid
                   placeholder="Севастополь/Балаклава/Любимовка/Верхнесадовое"/>
      </div>
    </div>

    <div>
      <div class="p-2">СНТ/ТСН</div>
      <InputText v-model.trim="address.planStructure" :class="planStructureClasses" fluid
                 placeholder="Рыбак-7/Сатурн-2"/>
    </div>

    <div>
      <div class="p-2">Улица</div>
      <InputText v-model.trim="address.street" :class="streetClasses" fluid
                 placeholder="Полное название с указанием типа (улица/проспект/проезд/бульвар/шоссе/переулок/тупик)"/>
    </div>

    <div class="py-3">
      <div class="flex items-center py-1">
        <RadioButton v-model="address.building_type" inputId="building" value="building"/>
        <label for="building" class="ml-2"><span class="m-2">Многоквартирный дом</span></label>
      </div>
      <div class="flex items-center">
        <RadioButton v-model="address.building_type" inputId="house" value="house"/>
        <label for="house" class="ml-2"><span class="m-2">Частный дом</span></label>
      </div>
    </div>


    <div class="flex flex-wrap">
      <div class="me-3">
        <h6 class="px-2 flex items-center gap-1">
          Дом
          <Asterisk/>
        </h6>
        <InputText v-model.trim="address.house" :class="houseClasses" class="w-[100px]"/>
      </div>

      <div class="me-3">
        <h6 class="px-2">Корпус</h6>
        <InputNumber :input-style="{width: '75px'}" :min="1" :max="200" v-model.number="address.block"/>
      </div>

      <template v-if="address.building_type === 'building'">

        <template v-if="subscriberAddress">
          <div class="me-3">
            <h6 class="px-2">Номер этажа</h6>
            <InputNumber :input-style="{width: '200px'}" :min="1" v-model.number="address.floor"/>
          </div>
          <div class="me-3">
            <h6 class="px-2">Квартира</h6>
            <InputNumber :input-style="{width: '200px'}" :min="1" v-model.number="address.apartment"/>
          </div>
        </template>

        <template v-else>
          <div class="me-3">
            <h6 class="px-2">Этажность</h6>
            <InputNumber :input-style="{width: '100px'}" :min="1" v-model.number="address.floors"/>
          </div>
          <div class="me-3">
            <h6 class="px-2">Количество подъездов</h6>
            <InputNumber :input-style="{width: '200px'}" :min="1" v-model.number="address.total_entrances"/>
          </div>
        </template>

      </template>

    </div>

    <div style="text-align: right" class="py-3">
      <Button class="me-3" @click="dismiss" severity="secondary" size="small" icon="pi pi-times" label="Не сохранять"/>
      <Button @click="validate" severity="success" icon="pi pi-check" size="small" label="Подтвердить"/>
    </div>

  </div>
</template>

<script>
import Asterisk from "./Asterisk.vue"
import BuildingIcon from "./BuildingIcon.vue";

export default {
  name: "AddressForm",
  components: {Asterisk, BuildingIcon},
  props: {
    initAddress: {required: true, type: Object},
    subscriberAddress: {required: false, default: false},
  },
  data() {
    return {
      address: null,
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
  beforeMount() {
    this.address = this.initAddress
    if (!this.address.building_type) {
      this.address.building_type = "building"
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
        this.$emit("valid", this.address)
      }
    },

    dismiss() {
      this.$emit("dismiss")
    }

  },
}
</script>

<style scoped>

</style>