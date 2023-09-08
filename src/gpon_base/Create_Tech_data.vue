<template>
  <div id="app">

    <div class="w-75 container py-2">
      <h2>Добавление технических данных</h2>
    </div>

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
                        :class="formState.firstStep.deviceName.valid?[]:['p-invalid']"
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
                        :class="formState.firstStep.devicePort.valid?[]:['p-invalid']"
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
          <div v-if="!show_new_address_form && !formState.secondStep.new_address.valid">
            <h6 class="px-2">Выберите существующий адрес дома
              <Asterisk/>
            </h6>
            <div class="shadow">
              <Dropdown v-model="formData.houseB.address" :options="addressesList" filter
                        :class="formState.secondStep.address.valid?[]:['p-invalid']"
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
                  <div class="flex align-items-center d-flex">
                    <BuildingIcon :type="slotProps.option.building_type" width="24" height="24"></BuildingIcon>
                    <div>{{ getFullAddress(slotProps.option) }}</div>
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

          <div v-if="!show_new_address_form && formState.secondStep.new_address.valid">
            <h6>
              {{ getFullAddress(formData.houseB.new_address) }}
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

      <!-- THIRD STEP -->
      <div v-else-if="current_step===3" class="p-4">

        <div class="w-100 d-flex">
          <div v-if="this.formData.houseB.buildType()==='building'" class="py-3 me-4">
            <div class="flex align-items-center py-1">
              <RadioButton v-model="formData.end3.type" inputId="splitter" value="splitter"/>
              <label for="splitter" class="ml-2"><span class="m-2">Сплиттер</span></label>
            </div>
            <div class="flex align-items-center">
              <RadioButton v-model="formData.end3.type" inputId="rizer" value="rizer"/>
              <label for="rizer" class="ml-2"><span class="m-2">Райзер</span></label>
            </div>
          </div>

          <div v-if="formData.end3.type==='splitter'">
            <div>
              <h6>Количество портов на сплиттере
                <Asterisk/>
              </h6>
              <Dropdown v-model="formData.end3.splitter.portCount" :options="[4, 8, 16]" class="w-full md:w-14rem"/>
            </div>
          </div>

          <div v-if="formData.end3.type==='rizer'">
            <div>
              <h6>Количество волокон на райзере
                <Asterisk/>
              </h6>
              <Dropdown v-model="formData.end3.splitter.portCount" :options="[4, 8, 12, 16, 24]"
                        class="w-full md:w-14rem"/>
            </div>


          </div>

        </div>
        <RizerFiberColorExample :count="formData.end3.splitter.portCount"/>


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

    {{ formData }}

  </div>
</template>

<script>
import StepMenu from "./components/StepMenu.vue"
import Dropdown from "primevue/dropdown/Dropdown.vue"
import InputText from "primevue/inputtext/InputText.vue"
import Textarea from "primevue/textarea/Textarea.vue"
import Button from "primevue/button/Button.vue"
import Dialog from "primevue/dialog/Dialog.vue"
import RadioButton from "primevue/radiobutton/RadioButton.vue"

import AddressForm from "./components/AddressForm.vue"
import Asterisk from "./components/Asterisk.vue"
import BuildingIcon from "./components/BuildingIcon.vue"
import RizerFiberColorExample from "./components/RizerFiberColorExample.vue";

export default {
  name: "Gpon_base.vue",
  components: {
    BuildingIcon,
    AddressForm,
    Asterisk,
    Button,
    Dialog,
    Dropdown,
    InputText,
    RadioButton,
    RizerFiberColorExample,
    StepMenu,
    Textarea,
  },
  data() {
    return {
      current_step: 1,
      show_new_address_form: false,
      formState: {
        firstStep: {
          deviceName: {valid: true},
          devicePort: {valid: true},
          isValid() {
            return this.devicePort.valid && this.deviceName.valid
          }
        },
        secondStep: {
          address: {valid: true},
          new_address: {valid: false},
          isValid() {
            return this.address.valid || this.new_address.valid
          }
        },
      },

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
            building_type: "building",
            floors: 1,
            total_entrances: 1
          },
          buildType() {
            if (this.address) {
              return this.address.building_type
            } else {
              return this.new_address.building_type
            }
          },
        },
        end3: {
          type: "splitter",
          splitter: {
            portCount: 8
          }
        }

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
    }
  },
  methods: {

    stepIsValid() {
      if (this.current_step === 1) {
        this.formState.firstStep.deviceName.valid = this.formData.oltState.deviceName.length > 0
        this.formState.firstStep.devicePort.valid = this.formData.oltState.devicePort.length > 0
        return this.formState.firstStep.isValid()

      } else if (this.current_step === 2) {
        this.formState.secondStep.address.valid = Boolean(this.formData.houseB.address)
        return this.formState.secondStep.isValid()
      }
    },

    nextStep() {
      if (this.current_step < 4 && this.stepIsValid()) this.current_step++
    },
    prevStep() {
      if (this.current_step > 1) this.current_step--
    },

    getFullAddress(address) {
      let str = ""
      if (address.region !== "Севастополь") str += ` ${address.region},`;
      if (address.settlement !== "Севастополь") str += ` ${address.settlement},`;
      if (address.planStructure.length) str += `СНТ ${address.planStructure},`;
      if (address.street.length) str += ` ${address.street},`;
      str += ` д. ${address.house}`;
      if (address.block) str += `/${address.block}`;
      return str
    },

    validNewAddress() {
      this.show_new_address_form = false
      this.formState.secondStep.new_address.valid = true
      this.formData.houseB.address = null
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