<template>
  <div id="app">

    <div class="w-75 container py-2">
      <h2>Добавление технических данных</h2>
    </div>

    <div class="plate py-4 w-75 container">

      <StepMenu
          class="p-2"
          :current-step="current_step"
          :is-mobile="isMobile"
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
                        :class="formState.firstStep.deviceName.valid?['flex-wrap']:['flex-wrap', 'p-invalid']"
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

          <AddressGetCreate :is-mobile="isMobile" :data="formData.houseB">
          </AddressGetCreate>

          <div v-if="formData.houseB.address && formData.houseB.address.building_type === 'building'"
               class="w-100 py-2">
            <h6 class="px-2">Задействованные подъезды в доме для данного OLT порта</h6>
            <InputText class="w-100" v-model.trim="formData.houseB.entrances" type="text"
                       placeholder="Укажите подъезды"/>
          </div>

          <div class="py-2">
            <h6 class="px-2">Описание сплиттера 2го каскада</h6>
            <Textarea class="shadow w-100" v-model="formData.houseB.description" rows="5"/>
          </div>

        </div>
      </div>

      <!-- THIRD STEP -->
      <div v-else-if="current_step===3" class="p-4">


        <div v-if="formData.houseB.buildType()==='house'">
          <h4 class="text-center py-3">Возможно для данного частного дома уже имеется сплиттер</h4>
          <SplittersRizersFind :init="formData.end3.existingSplitter"
                               :type="formData.end3.type"
                               @selected="(sp) => {formData.end3.existingSplitter = sp}">
          </SplittersRizersFind>

          <h4 class="text-center py-3">Либо укажите новый сплиттер</h4>

        </div>

        <!-- Выбор сплиттера или райзера -->
        <div class="w-100 d-flex">
          <div v-if="formData.houseB.buildType()==='building'" class="py-3 me-4">
            <div class="flex align-items-center py-1">
              <RadioButton v-model="formData.end3.type" id="splitter" inputId="splitter" value="splitter"/>
              <label for="splitter" class="ml-2"><span class="m-2">Сплиттер</span></label>
            </div>
            <div class="flex align-items-center">
              <RadioButton v-model="formData.end3.type" id="rizer" inputId="rizer" value="rizer"/>
              <label for="rizer" class="ml-2"><span class="m-2">Райзер</span></label>
            </div>
          </div>

          <!-- Кол-во портов -->
          <div v-if="formData.end3.type==='splitter'">
            <div>
              <h6>Количество портов на сплиттере
                <Asterisk/>
              </h6>
              <Dropdown v-model="formData.end3.portCount" :options="[4, 8, 12, 16, 24]"
                        class="w-full md:w-14rem"/>
            </div>
          </div>

          <!-- Кол-во волокон -->
          <div v-if="formData.end3.type==='rizer'">
            <div>
              <h6>Количество волокон на райзере
                <Asterisk/>
              </h6>
              <Dropdown v-model="formData.end3.portCount" :options="[4, 8, 12, 16, 24]"
                        class="w-full md:w-14rem me-3"/>
              <Button @click="formState.thirdStep.showRizerColors=true" severity="primary" outlined rounded
                      size="small">
                Посмотреть цвета
              </Button>
            </div>

            <!-- Окно для отображения цветов волокон -->
            <Dialog v-model:visible="formState.thirdStep.showRizerColors">
              <RizerFiberColorExample v-if="formData.end3.type==='rizer'" :count="formData.end3.portCount"/>
            </Dialog>

          </div>

        </div>

        <div v-if="formData.houseB.buildType()==='building'">
          <End3AddForm :initial="formData.end3.list" :end3-type="formData.end3.type"></End3AddForm>
        </div>

        <!-- В частном доме может быть только ОДИН сплиттер -->
        <div v-else>
          <End3AddForm :initial="formData.end3.list" :max-limit="1" end3-type="splitter"></End3AddForm>
        </div>

      </div>

      <!-- LAST STEP -->
      <div v-else-if="current_step===4" class="p-4">
        <h4 class="text-center">Внимательно проверьте введенный данные</h4>

        <h5 class="py-3">OLT State</h5>
        <table class="table table-striped">
          <tbody>
          <tr>
            <td>Оборудование</td>
            <td>{{ formData.oltState.deviceName }}</td>
          </tr>
          <tr>
            <td>OLT порт</td>
            <td>{{ formData.oltState.devicePort }}</td>
          </tr>
          <tr>
            <td>Волокно</td>
            <td>{{ formData.oltState.fiber }}</td>
          </tr>
          <tr>
            <td>Описание сплиттера 1го каскада</td>
            <td>{{ formData.oltState.description }}</td>
          </tr>
          </tbody>
        </table>

        <h5 class="py-3">Дом</h5>
        <table class="table table-striped">
          <tbody>
          <tr>
            <td>Адрес</td>
            <td>
              <div>
                <BuildingIcon :type="formData.houseB.address.building_type" width="24" height="24"></BuildingIcon>
                {{ getFullAddress(formData.houseB.address) }}
                <br>
                <template v-if="formData.houseB.address.building_type === 'building'">
                  Многоквартирный дом. Количество этажей: {{ formData.houseB.address.floors }} /
                  Количество подъездов: {{ formData.houseB.address.total_entrances }}
                </template>
                <template v-else>
                  Частный дом.
                </template>
              </div>
            </td>
          </tr>
          <tr v-if="formData.houseB.address.building_type==='building'">
            <td>Задействованные подъезды в доме для данного OLT порта</td>
            <td>{{ formData.houseB.entrances }}</td>
          </tr>
          <tr>
            <td>Описание сплиттера 2го каскада</td>
            <td>{{ formData.houseB.description }}</td>
          </tr>
          </tbody>
        </table>

        <h5 class="py-3">Абонентская линия</h5>
        <table class="table table-striped">
          <tbody>
          <tr>
            <td>Тип линии</td>
            <td>{{ formData.end3.type }}</td>
          </tr>
          <tr>
            <td>Количество портов</td>
            <td>{{ formData.end3.portCount }}</td>
          </tr>
          <tr v-if="formData.end3.existingSplitter">
            <td>Выбран существующий сплиттер</td>
            <td>
              {{ getFullAddress(formData.end3.existingSplitter.address) }}
              Локация: {{ formData.end3.existingSplitter.location }}.
              Кол-во портов: {{ formData.end3.existingSplitter.capacity }}
            </td>
          </tr>
          <tr v-for="(sp, index) in formData.end3.list">
            <td>{{ formData.end3.type }} {{ index + 1 }}</td>
            <td>
              Адрес:
              <template v-if="!sp.buildAddress">{{ getFullAddress(sp.address) }}</template>
              <template v-else>в этом же доме</template>
              <br>
              Местоположение: {{ sp.location }}
            </td>
          </tr>
          </tbody>
        </table>

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
import StepMenu from "./components/StepMenu.vue";
import Dropdown from "primevue/dropdown/Dropdown.vue";
import InputText from "primevue/inputtext/InputText.vue";
import Textarea from "primevue/textarea/Textarea.vue";
import Button from "primevue/button/Button.vue";
import Dialog from "primevue/dialog/Dialog.vue";
import RadioButton from "primevue/radiobutton/RadioButton.vue";

import AddressForm from "./components/AddressForm.vue";
import Asterisk from "./components/Asterisk.vue";
import BuildingIcon from "./components/BuildingIcon.vue";
import RizerFiberColorExample from "./components/RizerFiberColorExample.vue";
import End3AddForm from "./components/End3AddForm.vue";
import AddressGetCreate from "./components/AddressGetCreate.vue";
import SplittersRizersFind from "./components/SplittersRizersFind.vue"
import formatAddress from "../helpers/address";

export default {
  name: "Gpon_base.vue",
  components: {
    AddressGetCreate,
    BuildingIcon,
    AddressForm,
    Asterisk,
    Button,
    Dialog,
    Dropdown,
    InputText,
    RadioButton,
    RizerFiberColorExample,
    End3AddForm,
    SplittersRizersFind,
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
          isValid() {
            return this.devicePort.valid && this.deviceName.valid
          }
        },
        secondStep: {
          address: {valid: true},
          isValid() {
            return this.address.valid
          }
        },
        thirdStep: {
          showRizerColors: false,
          end3Valid: false,
          isValid() {
            return this.end3Valid
          }
        }
      },

      formData: {
        oltState: {
          deviceName: "",
          devicePort: "",
          fiber: "",
          description: "",
        },
        houseB: {
          entrances: "",
          description: "",
          address: null,
          buildType() {
            return this.address.building_type
          },
        },
        end3: {
          type: "splitter",
          list: [],
          existingSplitter: null,
          portCount: 8,
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