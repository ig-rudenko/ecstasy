<template>
  <div id="app">

    <div class="w-75 container py-2">
      <h2>Добавление абонента</h2>
    </div>

    <div class="plate py-4 w-75 container">

      <StepMenu
          class="p-2"
          :current-step="current_step"
          :is-mobile="isMobile"
          :steps-text="['Тех. данные', 'Абон. данные', 'Подключение']">
      </StepMenu>

      <!-- FIRST STEP -->
      <div v-if="current_step===1" class="p-4">

        <div class="d-flex align-items-center flex-wrap">
          <div class="me-3">
            <h6 class="px-2">OLT оборудование
              <Asterisk/>
            </h6>
            <div class="shadow">
              <Dropdown v-model="formData.techData.deviceName" :options="devicesList" filter
                        :class="formState.firstStep.deviceName.valid?['flex-wrap']:['flex-wrap', 'p-invalid']"
                        @change="deviceHasChanged"
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

          <div v-if="formData.techData.deviceName" class="me-3">
            <h6 class="px-2">Порт
              <Asterisk/>
            </h6>
            <div class="shadow">
              <Dropdown v-model="formData.techData.devicePort" :options="devicePortList" filter
                        :class="formState.firstStep.devicePort.valid?[]:['p-invalid']"
                        @change="portHasChanged"
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

        <div v-if="formData.techData.devicePort" class="w-100">
          <AddressGetCreate @change="addressHasChanged" :is-mobile="isMobile" :allow-create="false"
                            :data="formData.techData"
                            :get-from-device-port="{
                              deviceName: formData.techData.deviceName,
                              devicePort: formData.techData.devicePort
                            }">
          </AddressGetCreate>
        </div>

        <br>

        <div v-if="formData.techData.address">
          <SplittersRizersFind @change="(e) => {formData.techData.end3 = e.value; end3HasChanged()}"
                               :init="formData.techData.end3"
                               :get-from-house-address="formData.techData.address">
          </SplittersRizersFind>
        </div>

        <br>

        <div v-if="formData.techData.end3 && formData.techData.address">
          <SelectSplitterRizerPort :init="formData.techData.end3Port"
                                   @change="(e) => {formData.techData.end3Port = e.value}"
                                   :get-from="formData.techData.end3" :type="formData.techData.end3.type"
                                   :only-unused-ports="true">
          </SelectSplitterRizerPort>
        </div>

      </div>

      <!-- SECOND STEP -->
      <div v-else-if="current_step===2" class="p-4">

        <div class="py-2">
          <Dropdown v-model="formData.subscriberData.type" :options="['person','company','contract']"
                    placeholder="Выберите тип абонента" class="w-full md:w-14rem">
            <template #value="slotProps">
              <div v-if="slotProps.value" class="flex align-items-center"
                   v-html="subscriberVerbose(slotProps.value)"></div>
              <span v-else>{{ slotProps.placeholder }}</span>
            </template>
            <template #option="slotProps">
              <div class="flex align-items-center" v-html="subscriberVerbose(slotProps.option)"></div>
            </template>
          </Dropdown>
        </div>

        <div v-if="formData.subscriberData.type==='person'" class="d-flex flex-wrap py-2">
          <div class="me-2">
            <h6 class="px-2">Фамилия
              <Asterisk/>
            </h6>
            <InputText v-model.trim="formData.subscriberData.person.surname" type="text"
                       :class="formState.secondStep.person.surname.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
          <div class="me-2">
            <h6 class="px-2">Имя
              <Asterisk/>
            </h6>
            <InputText v-model.trim="formData.subscriberData.person.firstName" type="text"
                       :class="formState.secondStep.person.firstName.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
          <div class="me-2">
            <h6 class="px-2">Отчество
              <Asterisk/>
            </h6>
            <InputText v-model.trim="formData.subscriberData.person.lastName" type="text"
                       :class="formState.secondStep.person.lastName.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
        </div>

        <div v-else class="d-flex flex-wrap py-2">
          <div class="me-2">
            <h6 class="px-2">Название компании
              <Asterisk/>
            </h6>
            <InputText v-model.trim="formData.subscriberData.companyName" type="text"
                       :class="formState.secondStep.companyName.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
        </div>

        <div class="d-flex flex-wrap py-2">
          <div class="me-2">
            <h6 class="px-2">Лицевой счет
              <Asterisk/>
            </h6>
            <InputText v-model.number="formData.subscriberData.personalAccount" type="number"
                       :class="formState.secondStep.personalAccount.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
          <div class="me-2">
            <h6 class="px-2">Транзит
              <Asterisk/>
            </h6>
            <InputText v-model.number="formData.subscriberData.transit" type="number"
                       :class="formState.secondStep.transit.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
          <div class="me-2">
            <h6 class="px-2">Контактный номер
              <Asterisk/>
            </h6>
            <div class="flex-auto">
              <InputMask v-model="formData.subscriberData.phone"
                         date="phone" mask="+7 (999) 999-99-99" placeholder="+7 (999) 999-99-99"
                         :class="formState.secondStep.phone.valid?['shadow']:['shadow', 'p-invalid']"/>
            </div>
          </div>
        </div>


        <h6 class="p-2">Выберите услуги</h6>
        <div class="d-flex flex-wrap">
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.subscriberData.services" inputId="service-internet"
                      value="internet"/>
            <label for="service-internet" class="ml-2"> Интернет </label>
          </div>
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.subscriberData.services" inputId="service-tv" value="tv"/>
            <label for="service-tv" class="ml-2"> Телевидение </label>
          </div>
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.subscriberData.services" inputId="service-voip" value="voip"/>
            <label for="service-voip" class="ml-2"> VOIP </label>
          </div>
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.subscriberData.services" inputId="service-static" value="static"/>
            <label for="service-static" class="ml-2"> Статический IP </label>
          </div>
        </div>


      </div>

      <!-- THIRD STEP -->
      <div v-else-if="current_step===3" class="p-4">


      </div>

      <!-- LAST STEP -->
      <div v-else-if="current_step===4" class="p-4">
        <h4 class="text-center">Внимательно проверьте введенный данные</h4>

      </div>

      <!-- Кнопки -->
      <div class="d-flex justify-content-between mx-5">

        <Button severity="secondary" rounded>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-1"
               viewBox="0 0 16 16">
            <path
                d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/>
          </svg>
          {{ isMobile ? '' : 'Отмена' }}
        </Button>


        <div>

          <Button class="me-2" v-if="current_step!==1" severity="secondary" @click="prevStep" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-1"
                 viewBox="0 0 16 16">
              <path
                  d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/>
            </svg>
            {{ isMobile ? '' : 'Назад' }}
          </Button>

          <Button v-if="current_step<4" @click="nextStep" severity="success" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="me-1"
                 viewBox="0 0 16 16">
              <path
                  d="m12.14 8.753-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 4.796a1 1 0 0 1 0 1.506z"/>
            </svg>
            {{ isMobile ? '' : current_step < 3 ? 'Далее' : 'Завершить' }}
          </Button>

          <Button v-if="current_step===4" @click="submitForm" severity="success" rounded>
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
import Checkbox from "primevue/checkbox/Checkbox.vue";
import Dropdown from "primevue/dropdown/Dropdown.vue";
import InputText from "primevue/inputtext/InputText.vue";
import InputMask from "primevue/inputmask/InputMask.vue";
import Textarea from "primevue/textarea/Textarea.vue";
import Button from "primevue/button/Button.vue";
import Dialog from "primevue/dialog/Dialog.vue";
import RadioButton from "primevue/radiobutton/RadioButton.vue";
import AddressForm from "./components/AddressForm.vue";

import StepMenu from "./components/StepMenu.vue";
import Asterisk from "./components/Asterisk.vue";
import BuildingIcon from "./components/BuildingIcon.vue";
import RizerFiberColorExample from "./components/RizerFiberColorExample.vue";
import End3AddForm from "./components/End3AddForm.vue";
import AddressGetCreate from "./components/AddressGetCreate.vue";
import SplittersRizersFind from "./components/SplittersRizersFind.vue";
import SelectSplitterRizerPort from "./components/SelectSplitterRizerPort.vue";
import formatAddress from "../helpers/address";

export default {
  name: "Gpon_base.vue",
  components: {
    AddressGetCreate,
    AddressForm,
    Asterisk,
    BuildingIcon,
    Button,
    Checkbox,
    Dialog,
    Dropdown,
    InputMask,
    InputText,
    RadioButton,
    RizerFiberColorExample,
    End3AddForm,
    SplittersRizersFind,
    SelectSplitterRizerPort,
    StepMenu,
    Textarea,
  },
  mounted() {
    window.addEventListener('resize', () => {
      this.windowWidth = window.innerWidth
    })
  },
  data() {
    return {
      windowWidth: window.innerWidth,
      current_step: 1,
      formState: {
        firstStep: {
          deviceName: {valid: true},
          devicePort: {valid: true},
          address: {valid: true},
          end3: {valid: true},
          end3Port: {valid: true},
          isValid() {
            return this.devicePort.valid && this.deviceName.valid && this.address.valid && this.end3.valid && this.end3Port.valid
          }
        },
        secondStep: {
          person: {
            firstName: {valid: true}, surname: {valid: true}, lastName: {valid: true}
          },
          subscriberType: "",
          companyName: {valid: true},
          personalAccount: {valid: true},
          transit: {valid: true},
          phone: {valid: true},
          services: {valid: true},
          isValid() {
            return (
                (
                    this.subscriberType === "person"
                    &&
                    (this.person.firstName.valid && this.person.surname.valid && this.person.lastName.valid)
                    ||
                    (this.subscriberType !== "person" && this.companyName.valid)
                )
                &&
                this.personalAccount.valid && this.transit.valid && this.phone.valid
            )
          }
        },
        thirdStep: {
          isValid() {
            return
          }
        }
      },

      formData: {
        techData: {
          deviceName: "",
          devicePort: "",
          address: null,
          description: "",
          end3: null,
          end3Port: null,
        },
        subscriberData: {
          type: "person", // person, company, state
          person: {
            firstName: "", surname: "", lastName: ""
          },
          companyName: "",
          personalAccount: null,
          transit: null,
          phone: null,
          services: [],
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

    isMobile() {
      return this.windowWidth <= 768
    },

    devicePortList() {
      if (this.formData.techData.deviceName.length === 0) return []
      return [
        "0/1/1",
        "0/1/2",
        "0/1/3",
        "0/1/4",
        "0/1/5",
        "0/1/6",
      ]
    },

  },
  methods: {

    end3HasChanged() {
      this.formData.techData.end3Port = null
    },

    addressHasChanged() {
      this.formData.techData.end3 = null
      this.end3HasChanged()
    },

    portHasChanged() {
      this.formData.techData.address = null
      this.addressHasChanged()
    },

    deviceHasChanged() {
      this.formData.techData.devicePort = null
      this.portHasChanged()
    },


    subscriberVerbose(value) {
      if (value === 'person') {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                  <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"/>
                  <path fill-rule="evenodd" d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1z"/>
                </svg><span>Физ. лицо</span>`
      }
      if (value === 'company') {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                  <path d="M6.5 1A1.5 1.5 0 0 0 5 2.5V3H1.5A1.5 1.5 0 0 0 0 4.5v1.384l7.614 2.03a1.5 1.5 0 0 0 .772 0L16 5.884V4.5A1.5 1.5 0 0 0 14.5 3H11v-.5A1.5 1.5 0 0 0 9.5 1h-3zm0 1h3a.5.5 0 0 1 .5.5V3H6v-.5a.5.5 0 0 1 .5-.5z"/>
                  <path d="M0 12.5A1.5 1.5 0 0 0 1.5 14h13a1.5 1.5 0 0 0 1.5-1.5V6.85L8.129 8.947a.5.5 0 0 1-.258 0L0 6.85v5.65z"/>
                </svg><span>Юр. лицо</span>`
      }
      if (value === 'contract') {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                  <path d="m8 0 6.61 3h.89a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.5.5H15v7a.5.5 0 0 1 .485.38l.5 2a.498.498 0 0 1-.485.62H.5a.498.498 0 0 1-.485-.62l.5-2A.501.501 0 0 1 1 13V6H.5a.5.5 0 0 1-.5-.5v-2A.5.5 0 0 1 .5 3h.89L8 0ZM3.777 3h8.447L8 1 3.777 3ZM2 6v7h1V6H2Zm2 0v7h2.5V6H4Zm3.5 0v7h1V6h-1Zm2 0v7H12V6H9.5ZM13 6v7h1V6h-1Zm2-1V4H1v1h14Zm-.39 9H1.39l-.25 1h13.72l-.25-1Z"/>
                </svg><span>Гос. контракт</span>`
      }
    },

    stepIsValid() {
      if (this.current_step === 1) {
        this.formState.firstStep.deviceName.valid = this.formData.techData.deviceName.length > 0
        this.formState.firstStep.devicePort.valid = this.formData.techData.devicePort.length > 0
        this.formState.firstStep.address.valid = this.formData.techData.address !== null
        this.formState.firstStep.end3.valid = this.formData.techData.end3 !== null
        this.formState.firstStep.end3Port.valid = this.formData.techData.end3Port !== null
        return this.formState.firstStep.isValid()

      } else if (this.current_step === 2) {
        let data = this.formData.subscriberData
        this.formState.secondStep.subscriberType = data.type

        this.formState.secondStep.person.firstName.valid = data.person.firstName.length > 2
        this.formState.secondStep.person.surname.valid = data.person.surname.length > 2
        this.formState.secondStep.person.lastName.valid = data.person.lastName.length > 2

        this.formState.secondStep.companyName.valid = data.companyName.length > 4
        this.formState.secondStep.personalAccount.valid = data.personalAccount != null
        this.formState.secondStep.transit.valid = data.transit != null
        this.formState.secondStep.phone.valid = data.phone != null && data.phone.match(/\d/g).length === 11
        return this.formState.secondStep.isValid()

      } else if (this.current_step === 3) {
        let validCount = 0
        let totalEnd3Count = this.formData.end3.list.length
        let hasExistingSplitterID = Boolean(this.formData.end3.existingSplitter)

        for (let elem of this.formData.end3.list) {
          // Проверяем, что требуемы данные для сплиттер/райзер указаны
          if ((elem.buildAddress || elem.address) && elem.location.length) validCount++;
        }
        // Если выбран существующий сплиттер (только для частного дома) или имеются новые сплиттер/райзер
        // А также кол-во валидных сплиттер/райзер равно их общему кол-ву
        this.formState.thirdStep.end3Valid = (hasExistingSplitterID || validCount) && (validCount === totalEnd3Count)
        return this.formState.thirdStep.isValid()
      }
    },

    nextStep() {
      if (this.current_step < 4 && this.stepIsValid()) this.current_step++
    },
    prevStep() {
      if (this.current_step > 1) this.current_step--
    },

    getFullAddress(address) {
      return formatAddress(address)
    },

    submitForm() {
      // Отправка данных
    }

  },
}
</script>

<style scoped>
.plate {
  border-radius: 14px;
  border: 1px solid #A3A3A3;
}

@media (max-width: 767px) {
  .container, .mx-5 {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .w-75 {
    width: 100% !important;
  }

  .p-4 {
    padding-left: 0 !important;
    padding-right: 0 !important;
  }
}
</style>