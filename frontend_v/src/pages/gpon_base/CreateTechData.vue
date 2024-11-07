<template>
  <Header/>

  <div>
    <div class="header py-5">
      <img class="header-image" src="/img/gpon/tech-data.svg" alt="create-tech-data-image">
      <div class="text-4xl">Добавление технических данных</div>
    </div>

    <div class="plate shadow py-4 px-2 xl:w-2/3 mx-auto">

      <StepMenu
          class="p-2"
          :current-step="current_step"
          :is-mobile="isMobile"
          :steps-text="['OLT State', 'Дом', 'Абонентская линия']">
      </StepMenu>

      <!-- FIRST STEP -->
      <div v-if="current_step===1" class="p-4">

        <div class="flex flex-col sm:grid grid-cols-3 gap-4">
          <div class="me-3 w-full col-span-2">
            <div class="px-2 flex items-center gap-1 pb-2">
              OLT оборудование
              <Asterisk/>
            </div>
            <Select v-model="formData.oltState.deviceName" :options="devicesList" filter
                    :class="formState.firstStep.deviceName.valid?'':'p-invalid'"
                    class="w-full" fluid
                    :option-label="x => x"
                    :virtualScrollerOptions="{ itemSize: 38 }"
                    @change="deviceNameSelected" placeholder="Выберите устройство">
              <template #value="slotProps">
                <div v-if="slotProps.value">{{ slotProps.value }}</div>
                <span v-else>{{ slotProps.placeholder }}</span>
              </template>
              <template #option="slotProps">
                <div>{{ slotProps.option }}</div>
              </template>
            </Select>
          </div>

          <div class="me-3 w-full">
            <div class="px-2 flex items-center gap-1 pb-2">
              Порт
              <Asterisk/>
            </div>
            <Select v-model="formData.oltState.devicePort" :options="devicePortList" filter
                    :class="formState.firstStep.devicePort.valid?[]:['p-invalid']" fluid class="w-full"
                    :option-label="x => x" placeholder="Выберите порт">
              <template #value="slotProps">
                <div v-if="slotProps.value">{{ slotProps.value }}</div>
                <span v-else>{{ slotProps.placeholder }}</span>
              </template>
              <template #option="slotProps">
                <div>{{ slotProps.option }}</div>
              </template>
            </Select>
          </div>
        </div>

        <br>

        <div class="w-100">
          <h6 class="px-2 pb-2">Волокно</h6>
          <InputText v-model.trim="formData.oltState.fiber" fluid
                     placeholder="Название кабеля/номер волокна в кабеле"/>
        </div>

        <br>

        <div>
          <h6 class="px-2 pb-2">Описание сплиттера 1го каскада</h6>
          <Textarea fluid auto-resize v-model="formData.oltState.description" rows="5"/>
        </div>

      </div>

      <!-- SECOND STEP -->
      <div v-else-if="current_step===2" class="p-4">

        <div>

          <AddressGetCreate :is-mobile="isMobile" :data="formData.houseB"/>

          <div v-if="formData.houseB.address && formData.houseB.address.building_type === 'building'"
               class="w-100 py-2">
            <div class="p-2">Задействованные подъезды в доме для данного OLT порта</div>
            <InputText class="w-100" v-model.trim="formData.houseB.entrances" fluid
                       placeholder="Укажите подъезды"/>
          </div>

          <div>
            <div class="p-2">Описание сплиттера 2го каскада</div>
            <Textarea v-model="formData.houseB.description" rows="5" fluid auto-resize/>
          </div>

        </div>
      </div>

      <!-- THIRD STEP -->
      <div v-else-if="current_step===3" class="p-4">

        <div v-if="formData.houseB.buildType()==='house'" class="flex justify-center flex-col gap-2">
          <Message icon="pi pi-info-circle" class="text-center w-fit self-center">
            Возможно для данного частного дома уже имеется сплиттер
          </Message>
          <div class="self-center w-full">
            <SplittersRizersFind :init="formData.end3.existingSplitter"
                                 :type="formData.end3.type"
                                 :getFromOLTState="formData.oltState"
                                 @change="(e) => {formData.end3.existingSplitter = e.value}">
            </SplittersRizersFind>
          </div>
          <Message class="text-center w-fit self-center">Либо укажите новый сплиттер</Message>
        </div>

        <!-- Выбор сплиттера или райзера -->
        <div class="flex">
          <div v-if="formData.houseB.buildType()==='building'" class="py-3 me-4">
            <div class="flex items-center py-1">
              <RadioButton v-model="formData.end3.type" input-id="splitter" value="splitter"/>
              <label for="splitter" class="cursor-pointer"><span class="m-2">Сплиттер</span></label>
            </div>
            <div class="flex items-center">
              <RadioButton v-model="formData.end3.type" input-id="rizer" value="rizer"/>
              <label for="rizer" class="cursor-pointer"><span class="m-2">Райзер</span></label>
            </div>
          </div>

          <!-- Кол-во портов -->
          <div v-if="formData.end3.type==='splitter'">
            <div>
              <div class="px-2 flex items-center gap-1 p-1">
                Количество портов на сплиттере
                <Asterisk/>
              </div>
              <Select v-model="formData.end3.portCount" :options="[4, 8, 12, 16, 24]" class="w-14rem"/>
            </div>
          </div>

          <!-- Кол-во волокон -->
          <div v-if="formData.end3.type==='rizer'">
            <div>
              <div class="px-2 flex items-center gap-1 p-1">
                Количество волокон на райзере
                <Asterisk/>
              </div>
              <Select v-model="formData.end3.portCount" :options="[4, 8, 12, 16, 24]"
                      class="md:w-14rem me-3"/>
              <Button @click="formState.thirdStep.showRizerColors=true" severity="primary" icon="pi pi-palette" outlined
                      label="Посмотреть цвета"/>
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
      <div v-else-if="current_step===4" class="p-4 flex justify-center flex-col">
        <div class="text-3xl text-center p-3">Внимательно проверьте введенные данные</div>

        <div class="text-2xl p-3">OLT State</div>

        <table>
          <tbody class="text-[1.1rem]">
          <tr class="bg-gray-200 dark:bg-gray-700">
            <td class="p-2">Оборудование</td>
            <td class="p-2">{{ formData.oltState.deviceName }}</td>
          </tr>
          <tr v-if="deviceNameErrors">
            <td colspan="2" class="pb-5">
              <Message severity="error">{{ deviceNameErrors }}</Message>
            </td>
          </tr>

          <tr>
            <td class="p-2">OLT порт</td>
            <td class="p-2">{{ formData.oltState.devicePort }}</td>
          </tr>
          <tr v-if="devicePortErrors">
            <td colspan="2" class="pb-5">
              <Message severity="error">{{ devicePortErrors }}</Message>
            </td>
          </tr>

          <tr class="bg-gray-200 dark:bg-gray-700">
            <td class="p-2">Волокно</td>
            <td class="p-2">{{ formData.oltState.fiber }}</td>
          </tr>
          <tr v-if="fiberErrors">
            <td colspan="2" class="pb-5">
              <Message severity="error">{{ fiberErrors }}</Message>
            </td>
          </tr>

          <tr>
            <td class="p-2">Описание сплиттера 1го каскада</td>
            <td class="p-2">{{ formData.oltState.description }}</td>
          </tr>
          <tr v-if="oltDescriptionErrors">
            <td colspan="2" class="pb-5">
              <Message severity="error">{{ oltDescriptionErrors }}</Message>
            </td>
          </tr>

          </tbody>
        </table>

        <div class="text-2xl p-3">Дом</div>
        <table>
          <tbody class="text-[1.1rem]">
          <tr class="bg-gray-200 dark:bg-gray-700">
            <td class="p-2">Адрес</td>
            <td class="p-2">
              <div class="flex flex-wrap gap-2">
                <BuildingIcon :type="formData.houseB.address.building_type" width="24" height="24"/>
                <span>{{ getFullAddress(formData.houseB.address) }}</span>
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
          <tr v-if="addressError">
            <td colspan="2" class="pb-5">
              <Message severity="error">{{ addressError }}</Message>
            </td>
          </tr>

          <tr v-if="formData.houseB.address.building_type==='building'">
            <td class="p-2">Задействованные подъезды в доме для данного OLT порта</td>
            <td class="p-2">{{ formData.houseB.entrances }}</td>
          </tr>
          <tr v-if="entrancesError">
            <td colspan="2" class="pb-5">
              <Message severity="error">asdasd{{ entrancesError }}</Message>
            </td>
          </tr>

          <tr class="bg-gray-200 dark:bg-gray-700">
            <td class="p-2">Описание сплиттера 2го каскада</td>
            <td class="p-2">{{ formData.houseB.description }}</td>
          </tr>
          <tr v-if="houseDescriptionError">
            <td colspan="2" class="pb-5">
              <Message severity="error">{{ houseDescriptionError }}</Message>
            </td>
          </tr>

          </tbody>
        </table>

        <div class="text-2xl py-3">Абонентская линия</div>
        <table>
          <tbody>
          <tr class="bg-gray-200 dark:bg-gray-700">
            <td class="p-2">Тип линии</td>
            <td class="p-2">{{ formData.end3.type }}</td>
          </tr>
          <tr v-if="end3TypeError">
            <td colspan="2" class="pb-5">
              <Message severity="error">{{ end3TypeError }}</Message>
            </td>
          </tr>

          <tr>
            <td>Количество портов</td>
            <td>{{ formData.end3.portCount }}</td>
          </tr>
          <tr v-if="end3PortCountError">
            <td colspan="2" class="pb-5">
              <Message severity="error">{{ end3PortCountError }}</Message>
            </td>
          </tr>

          <tr v-if="formData.end3.existingSplitter" class="odd:bg-gray-200 dark:odd:bg-gray-700">
            <td>Выбран существующий сплиттер</td>
            <td>
              {{ getFullAddress(formData.end3.existingSplitter.address) }}
              Локация: {{ formData.end3.existingSplitter.location }}.
              Кол-во портов: {{ formData.end3.existingSplitter.capacity }}
            </td>
          </tr>
          <tr v-if="end3ExistingSplitterError" class="odd:bg-gray-200 dark:odd:bg-gray-700">
            <td colspan="2" class="pb-5">
              <Message severity="error">{{ end3ExistingSplitterError }}</Message>
            </td>
          </tr>

          <template v-for="(sp, index) in formData.end3.list">
            <tr class="odd:bg-gray-200 dark:odd:bg-gray-700">
              <td>{{ formData.end3.type }} {{ index + 1 }}</td>
              <td>
                Адрес:
                <template v-if="!sp.buildAddress">{{ getFullAddress(sp.address) }}</template>
                <template v-else>в этом же доме</template>
                <br>
                Местоположение: {{ sp.location }}
              </td>
            </tr>
            <tr v-if="end3ListErrors && Object.entries(end3ListErrors[index]).length">
              <td colspan="2" class="pb-5">
                <Message severity="error">{{ end3ListErrors[index] }}</Message>
              </td>
            </tr>
          </template>


          </tbody>
        </table>

      </div>

      <!-- Ошибки в форме -->
      <Message v-if="errors" severity="error" class="text-center m-4">
        <div class="flex gap-2 items-center py-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
            <path
                d="M7.005 3.1a1 1 0 1 1 1.99 0l-.388 6.35a.61.61 0 0 1-1.214 0L7.005 3.1ZM7 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0Z"/>
          </svg>
          <span>Были замечены ошибки. Проверьте правильность введенных данных</span>
        </div>
      </Message>

      <!-- Кнопки -->
      <div v-if="!form_submitted_successfully" class="flex justify-between mx-5">

        <router-link :to="{name: 'gpon-tech-data'}">
          <Button severity="secondary" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                  d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/>
            </svg>
            <span>{{ isMobile ? '' : 'Отмена' }}</span>
          </Button>
        </router-link>

        <div>
          <Button v-if="current_step!==1" severity="secondary" @click="prevStep" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                  d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/>
            </svg>
            <span>{{ isMobile ? '' : 'Назад' }}</span>
          </Button>

          <Button v-if="current_step<4" @click="nextStep" severity="success" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                  d="m12.14 8.753-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 4.796a1 1 0 0 1 0 1.506z"/>
            </svg>
            <span>{{ isMobile ? '' : current_step < 3 ? 'Далее' : 'Завершить' }}</span>
          </Button>

          <Button v-if="current_step===4" @click="submitForm" severity="success" rounded>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <path
                  d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
            </svg>
            <span>Создать</span>
          </Button>

        </div>

      </div>

      <!-- Успешно создано -->
      <div v-else class="p-2 m-4 flex items-center justify-between gap-4">
        <router-link :to="{name: 'gpon-tech-data'}">
          <Button class="w-full" outlined icon="pi pi-arrow-left" label="Вернуться к перечню"/>
        </router-link>
        <Message severity="success">
          <div class="flex flex-wrap gap-4">
            <div class="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
                <path
                    d="M12.5 16a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm1.679-4.493-1.335 2.226a.75.75 0 0 1-1.174.144l-.774-.773a.5.5 0 0 1 .708-.708l.547.548 1.17-1.951a.5.5 0 1 1 .858.514ZM8 1c-1.573 0-3.022.289-4.096.777C2.875 2.245 2 2.993 2 4s.875 1.755 1.904 2.223C4.978 6.711 6.427 7 8 7s3.022-.289 4.096-.777C13.125 5.755 14 5.007 14 4s-.875-1.755-1.904-2.223C11.022 1.289 9.573 1 8 1Z"></path>
                <path
                    d="M2 7v-.839c.457.432 1.004.751 1.49.972C4.722 7.693 6.318 8 8 8s3.278-.307 4.51-.867c.486-.22 1.033-.54 1.49-.972V7c0 .424-.155.802-.411 1.133a4.51 4.51 0 0 0-4.815 1.843A12.31 12.31 0 0 1 8 10c-1.573 0-3.022-.289-4.096-.777C2.875 8.755 2 8.007 2 7Zm6.257 3.998L8 11c-1.682 0-3.278-.307-4.51-.867-.486-.22-1.033-.54-1.49-.972V10c0 1.007.875 1.755 1.904 2.223C4.978 12.711 6.427 13 8 13h.027a4.552 4.552 0 0 1 .23-2.002Zm-.002 3L8 14c-1.682 0-3.278-.307-4.51-.867-.486-.22-1.033-.54-1.49-.972V13c0 1.007.875 1.755 1.904 2.223C4.978 15.711 6.427 16 8 16c.536 0 1.058-.034 1.555-.097a4.507 4.507 0 0 1-1.3-1.905Z"></path>
              </svg>
              <span>Данные добавлены</span>
            </div>
          </div>
        </Message>
      </div>

    </div>

  </div>

  <Footer/>
</template>

<script>
import StepMenu from "./components/StepMenu.vue";
import Asterisk from "./components/Asterisk.vue";
import End3AddForm from "./components/End3AddForm.vue";
import AddressForm from "./components/AddressForm.vue";
import BuildingIcon from "./components/BuildingIcon.vue";
import AddressGetCreate from "./components/AddressGetCreate.vue";
import SplittersRizersFind from "./components/SplittersRizersFind.vue"
import RizerFiberColorExample from "./components/RizerFiberColorExample.vue";

import api from "@/services/api";
import {formatAddress} from "@/formats";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "CreateTechData",
  components: {
    Footer,
    Header,
    AddressGetCreate,
    BuildingIcon,
    AddressForm,
    Asterisk,
    RizerFiberColorExample,
    End3AddForm,
    SplittersRizersFind,
    StepMenu,
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
      _deviceNames: [],
      _portsNames: [],
      form_submitted_successfully: false,
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
            return this.address?.building_type
          },
        },
        end3: {
          type: "splitter",
          list: [],
          existingSplitter: null,
          portCount: 8,
        }

      },

      errors: null

    }
  },
  computed: {

    deviceNameErrors() {
      if (this.errors && this.errors.oltState && this.errors.oltState.deviceName) {
        return this.errors.oltState.deviceName.join('')
      }
      return null
    },
    devicePortErrors() {
      if (this.errors && this.errors.oltState && this.errors.oltState.devicePort) {
        return this.errors.oltState.devicePort.join('')
      }
      return null
    },
    fiberErrors() {
      if (this.errors && this.errors.oltState && this.errors.oltState.fiber) {
        return this.errors.oltState.fiber.join('')
      }
      return null
    },
    oltDescriptionErrors() {
      if (this.errors && this.errors.oltState && this.errors.oltState.description) {
        return this.errors.oltState.description.join('')
      }
      return null
    },

    serverError() {
      if (this.errors && this.errors.serverError) {
        return this.errors.serverError
      }
    },
    addressError() {
      let msg = "";
      if (this.errors && this.errors.houseB && this.errors.houseB.address) {
        // Создаем массив с названиями полей и ошибками
        let fields = [
          {name: "non_field_errors", label: ""},
          {name: "region", label: "Ошибка в поле региона"},
          {name: "settlement", label: "Ошибка в поле населенного пункта"},
          {name: "planStructure", label: "Ошибка в поле СНТ ТСН"},
          {name: "street", label: "Ошибка в поле улицы"},
          {name: "house", label: "Ошибка в поле дома"},
          {name: "block", label: "Ошибка в поле корпуса"},
          {name: "building_type", label: "Ошибка в поле типа строения"},
          {name: "floors", label: "Ошибка в поле кол-ва этажей"},
          {name: "total_entrances", label: "Ошибка в поле кол-ва подъездов"}
        ];
        // Проходим по массиву и добавляем сообщения об ошибках
        for (let field of fields) {
          if (this.errors.houseB.address[field.name]) {
            msg = msg + field.label + " " + this.errors.houseB.address[field.name].join("") + ". ";
          }
        }
      }
      return msg;
    },
    entrancesError() {
      if (this.errors && this.errors.houseB && this.errors.houseB.entrances) {
        return this.errors.houseB.entrances.join('')
      }
    },
    houseDescriptionError() {
      if (this.errors && this.errors.houseB && this.errors.houseB.description) {
        return this.errors.houseB.description.join('')
      }
    },

    end3TypeError() {
      if (this.errors && this.errors.end3 && this.errors.end3.type) {
        return this.errors.end3.type.join("")
      }
    },
    end3PortCountError() {
      if (this.errors && this.errors.end3 && this.errors.end3.portCount) {
        return this.errors.end3.portCount.join("")
      }
    },
    end3ExistingSplitterError() {
      if (this.errors && this.errors.end3 && this.errors.end3.existingSplitter) {
        return this.errors.end3.existingSplitter.join("")
      }
    },
    end3ListErrors() {
      if (this.errors && this.errors.end3 && this.errors.end3.list) {
        return this.errors.end3.list
      }
    },


    isMobile() {
      return this.windowWidth <= 768
    },

    devicesList() {
      if (this._deviceNames.length === 0) this.getDeviceNames();
      return this._deviceNames;
    },

    devicePortList() {
      if (this.formData.oltState.deviceName.length === 0) return []
      if (this._portsNames.length === 0) this.getPortsNames();
      return this._portsNames;
    },

  },
  methods: {

    deviceNameSelected() {
      this.formData.oltState.devicePort = ""
      this.getPortsNames()
    },

    getDeviceNames() {
      api.get("/gpon/api/devices-names")
          .then(res => this._deviceNames = Array.from(res.data))
    },
    getPortsNames() {
      api.get("/gpon/api/ports-names/" + this.formData.oltState.deviceName)
          .then(res => this._portsNames = Array.from(res.data))
    },

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
      api.post("/gpon/api/tech-data", this.formData)
          .then(resp => {
                if (resp.status === 201) {
                  this.form_submitted_successfully = true
                  this.errors = null
                }
              }
          ).catch(reason => {
        if (reason.response.status === 400) {
          this.errors = reason.response.data
        } else if (reason.response.status >= 500) {
          this.errors = {serverError: `Ошибка на сервере. Код ошибки: ${reason.response.status}`}
        }
      })
    }

  },
}
</script>

<style scoped>
.plate {
  border-radius: 14px;
}

.header {
  margin: auto;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 75% !important;
  position: relative;
  top: -25px;
}

.header-image {
  height: 300px;
}

@media (max-width: 767px) {
  .container, .mx-5 {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .header {
    flex-wrap: wrap;
  }

  .plate {
    box-shadow: none !important;
  }

  .header-image {
    height: auto;
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