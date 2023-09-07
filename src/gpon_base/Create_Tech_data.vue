<template>
  <div id="app">

    <div class="w-75 container py-2">
      <h2>Добавление технических данных</h2>
    </div>

    {{ formData }}


    <div class="plate py-4 w-75 container">

      <StepMenu
          class="p-2"
          :current-step="current_step"
          :steps-text="['OLT State', 'Дом', 'Абонентская линия']">
      </StepMenu>

      <!-- FIRST STEP -->
      <div v-if="current_step===1" class="p-4">

        <div class="d-flex align-items-center flex-wrap">
          <div class="me-3">

            <h6 class="px-2">OLT оборудование
              <Asterisk/>
            </h6>

            <div class="shadow">
              <Dropdown v-model="formData.oltState.deviceName" :options="devicesList" filter
                        optionLabel="name" placeholder="Выберите устройство">
                <template #value="slotProps">
                  <div v-if="slotProps.value" class="flex align-items-center">
                    <div>{{ slotProps.value }}</div>
                  </div>
                  <span v-else>
                            {{ slotProps.placeholder }}
                        </span>
                </template>
                <template #option="slotProps">
                  <div class="flex align-items-center">
                    <div>{{ slotProps.option }}</div>
                  </div>
                </template>
              </Dropdown>
            </div>
          </div>

          <div class="me-3">

            <h6 class="px-2">Порт
              <Asterisk/>
            </h6>

            <div class="shadow">
              <Dropdown v-model="formData.oltState.devicePort" :options="devicePortList" filter
                        optionLabel="name" placeholder="Выберите порт">
                <template #value="slotProps">
                  <div v-if="slotProps.value" class="flex align-items-center">
                    <div>{{ slotProps.value }}</div>
                  </div>
                  <span v-else>
                            {{ slotProps.placeholder }}
                        </span>
                </template>
                <template #option="slotProps">
                  <div class="flex align-items-center">
                    <div>{{ slotProps.option }}</div>
                  </div>
                </template>
              </Dropdown>
            </div>
          </div>
        </div>

        <br>

        <div class="w-100">
          <h6 class="px-2">Волокно</h6>
          <InputText v-model.trim="formData.oltState.fiber" class="shadow w-100" type="text"
                     placeholder="Название кабеля/номер волокна в кабеле"/>
        </div>

        <br>

        <div>
          <h6 class="px-2">Описание сплиттера 1го каскада</h6>
          <Textarea class="shadow w-100" v-model="formData.oltState.description" rows="5"/>
        </div>

      </div>

      <!-- SECOND STEP -->
      <div v-else-if="current_step===2" class="p-4">

        <div class="w-100">
          <div v-if="!show_new_address_form && !formData.houseB.new_address_valid">
            <h6 class="px-2">Выберите существующий адрес дома
              <Asterisk/>
            </h6>
            <div class="shadow">
              <Dropdown v-model="formData.houseB.address" :options="addressesList" filter
                        optionLabel="fullAddress" placeholder="Выберите устройство" class="w-100">
                <template #value="slotProps">
                  <div v-if="slotProps.value" class="flex align-items-center">
                    <div>{{ slotProps.value.fullAddress }}</div>
                  </div>
                  <span v-else>
                            {{ slotProps.placeholder }}
                        </span>
                </template>
                <template #option="slotProps">
                  <div class="flex align-items-center">
                    <div>{{ slotProps.option.fullAddress }}</div>
                  </div>
                </template>
              </Dropdown>
            </div>

            <Button @click="show_new_address_form=true" severity="success" size="small">
              Создать новый адрес
            </Button>

          </div>

          <Dialog v-model:visible="show_new_address_form" modal header="Добавление нового дома"
                  :style="{ width: '50vw' }">
            <AddressForm @valid="validNewAddress" :address="formData.houseB.new_address"></AddressForm>
          </Dialog>

          <div v-if="!show_new_address_form && formData.houseB.new_address_valid">
            <h6>
              регион: {{ this.formData.houseB.new_address.region }}, нас. пункт:
              {{ this.formData.houseB.new_address.settlement }},
              {{ this.formData.houseB.new_address.street }} д. {{ this.formData.houseB.new_address.house }}
              <template v-if="this.formData.houseB.new_address.block">
                корпус: {{ this.formData.houseB.new_address.block }}
              </template>

              <br>
              <template v-if="this.formData.houseB.new_address.apartment_building === 'true'">
                Многоквартирный дом. Количество этажей: {{ this.formData.houseB.new_address.floors }} /
                Количество подъездов: {{ this.formData.houseB.new_address.total_entrances }}
              </template>
              <template v-else>
                Частный дом.
              </template>
            </h6>
            <Button @click="show_new_address_form=true" severity="success" size="small">
              Редактировать новый адрес
            </Button>
          </div>


          <div class="w-100 py-3">
            <h6 class="px-2">Задействованные подъезды в доме для данного OLT порта</h6>
            <InputText class="w-100" v-model.trim="formData.houseB.entrances" type="text"
                       placeholder="Укажите подъезды"/>
          </div>

          <div>
            <h6 class="px-2">Описание сплиттера 2го каскада</h6>
            <Textarea class="shadow w-100" v-model="formData.houseB.description" rows="5"/>
          </div>

        </div>
      </div>

      <!-- Кнопки -->
      <div class="d-flex justify-content-between mx-5">

        <Button severity="secondary" rounded>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-1"
               viewBox="0 0 16 16">
            <path
                d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/>
          </svg>
          Отмена
        </Button>


        <div>

          <Button class="me-2" v-if="current_step!==1" severity="secondary" @click="prevStep" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-1"
                 viewBox="0 0 16 16">
              <path
                  d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/>
            </svg>
            Назад
          </Button>

          <Button v-if="current_step<4" @click="nextStep" severity="success" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-1"
                 viewBox="0 0 16 16">
              <path
                  d="m12.14 8.753-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 4.796a1 1 0 0 1 0 1.506z"/>
            </svg>
            {{ current_step < 3 ? 'Далее' : 'Завершить' }}
          </Button>

          <Button v-if="current_step===4" @click="nextStep" severity="success" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-2"
                 viewBox="0 0 16 16">
              <path
                  d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
            </svg>
            Создать
          </Button>

        </div>

      </div>

    </div>

  </div>
</template>

<script>
import StepMenu from "./components/StepMenu.vue";
import Dropdown from "primevue/dropdown/Dropdown.vue"
import InputText from "primevue/inputtext/InputText.vue"
import Textarea from "primevue/textarea/Textarea.vue"
import Button from "primevue/button/Button.vue"
import Dialog from "primevue/dialog/Dialog.vue"

import AddressForm from "./components/AddressForm.vue";
import Asterisk from "./components/Asterisk.vue"

export default {
  name: "Gpon_base.vue",
  components: {
    AddressForm,
    Asterisk,
    Button,
    Dialog,
    Dropdown,
    InputText,
    StepMenu,
    Textarea,
  },
  data() {
    return {
      current_step: 1,
      show_new_address_form: false,
      formData: {
        oltState: {
          deviceName: "",
          devicePort: "",
          fiber: "",
          description: "",
        },
        houseB: {
          address: null,
          entrances: "",
          description: "",
          new_address: {
            region: "Севастополь",
            settlement: "Севастополь",
            planStructure: "",
            street: "",
            house: "",
            block: null,
            apartment_building: 'true',
            floors: 1,
            total_entrances: 1
          },
          new_address_valid: false,
        },
      }
    }
  },
  computed: {
    devicesList() {
      return [
        "MSAN_GStal64_upssssssssssssssssssss",
        "MSAN_GStal64_down",
      ]
    },

    devicePortList() {
      if (this.formData.oltState.deviceName.length === 0) return []
      return [
        "0/1/1",
        "0/1/2",
        "0/1/3",
        "0/1/4",
        "0/1/5",
        "0/1/6",
      ]
    },

    addressesList() {
      return [
        {id: 1, fullAddress: "Севастополь, ул. Колобова 22/10"},
        {id: 2, fullAddress: "Севастополь, ул. Колобова 23/10"},
        {id: 3, fullAddress: "Севастополь, ул. Колобова 24/10"},
        {id: 4, fullAddress: "Севастополь, ул. Колобова 25/10"},
        {id: 5, fullAddress: "Севастополь, ул. Колобова 26/10"},
        {id: 6, fullAddress: "Севастополь, ул. Колобова 27/10"},
      ]
    }
  },
  methods: {
    nextStep() {
      if (this.current_step < 4) this.current_step++
    },
    prevStep() {
      if (this.current_step > 1) this.current_step--
    },
    validNewAddress() {
      this.show_new_address_form = false
      this.formData.houseB.new_address_valid = true
    },
  },
}
</script>

<style scoped>
.plate {
  border-radius: 14px;
  border: 1px solid #A3A3A3;
}

</style>