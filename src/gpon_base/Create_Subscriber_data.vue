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

        <!-- ВЫБИРАЕМ -->
        <div class="d-flex align-items-center flex-wrap">
          <div class="me-3">
            <h6 class="px-2">OLT оборудование
              <Asterisk/>
            </h6>
            <div class="shadow">
              <Dropdown v-model="formData.techData.deviceName" :options="devicesList" filter
                        :class="formState.firstStep.deviceName.valid?['flex-wrap']:['flex-wrap', 'p-invalid']"
                        :option-label="x => x"
                        @change="deviceHasChanged" placeholder="Выберите устройство">
                <template #value="slotProps">
                  <div v-if="slotProps.value">{{ slotProps.value }}</div>
                  <span v-else>{{ slotProps.placeholder }}</span>
                </template>
                <template #option="slotProps">{{ slotProps.option }}</template>
              </Dropdown>
            </div>
          </div>

          <!-- ПОИСК ПОРТОВ У ВЫБРАННОГО ОБОРУДОВАНИЯ -->
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
          <!-- ПОИСК ВСЕХ ДОМОВ ДЛЯ ВЫБРАННОГО OLT ПОРТА -->
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
          <!-- ПОИСК СПЛИТТЕРОВ/РАЙЗЕРОВ В ВЫБРАННОМ ДОМЕ -->
          <SplittersRizersFind @change="(e) => {formData.techData.end3 = e.value; end3HasChanged()}"
                               :init="formData.techData.end3"
                               :fromAddressID="formData.techData.address.id">
          </SplittersRizersFind>
        </div>

        <br>

        <div v-if="formData.techData.end3 && formData.techData.address">
          <!-- ПОИСК СВОБОДНОГО ПОДКЛЮЧЕНИЯ У ВЫБРАННОГО СПЛИТТЕРА/РАЙЗЕРА -->
          <SelectSplitterRizerPort :init="formData.techData.end3Port"
                                   :end3ID="formData.techData.end3.id"
                                   @change="(e) => {formData.techData.end3Port = e.value}"
                                   :get-from="formData.techData.end3" :type="formData.techData.end3.type"
                                   :only-unused-ports="true">
          </SelectSplitterRizerPort>
        </div>

      </div>

      <!-- SECOND STEP -->
      <div v-else-if="current_step===2" class="p-4">

        <div class="py-2">
          <Dropdown v-model="formData.customer.type" :options="['person','company','contract']"
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

        <div v-if="formData.customer.type==='person'" class="d-flex flex-wrap py-2">
          <div class="me-2">
            <h6 class="px-2">Фамилия<Asterisk/></h6>
            <InputText v-model.trim="formData.customer.surname" type="text"
                       :class="formState.secondStep.person.surname.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
          <div class="me-2">
            <h6 class="px-2">Имя<Asterisk/></h6>
            <InputText v-model.trim="formData.customer.firstName" type="text"
                       :class="formState.secondStep.person.firstName.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
          <div class="me-2">
            <h6 class="px-2">Отчество<Asterisk/></h6>
            <InputText v-model.trim="formData.customer.lastName" type="text"
                       :class="formState.secondStep.person.lastName.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
        </div>

        <div v-else class="d-flex flex-wrap py-2">
          <div class="me-2">
            <h6 class="px-2">Название кампании<Asterisk/></h6>
            <InputText v-model.trim="formData.customer.companyName" type="text"
                       :class="formState.secondStep.companyName.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
        </div>

        <div class="d-flex flex-wrap py-2">
          <div class="me-2">
            <h6 class="px-2">Лицевой счет<Asterisk/></h6>
            <InputText v-model.number="formData.customer.contract" type="number"
                       :class="formState.secondStep.contract.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
          <div class="me-2">
            <h6 class="px-2">Транзит</h6>
            <InputText v-model.number="formData.transit" type="number"/>
          </div>
          <div class="me-2">
            <h6 class="px-2">Контактный номер</h6>
            <div class="flex-auto">
              <InputMask v-model="formData.customer.phone" date="phone" mask="+7 (999) 999-99-99" placeholder="+7 (999) 999-99-99"/>
            </div>
          </div>
        </div>


        <h6 class="p-2">Выберите услуги</h6>
        <div class="d-flex flex-wrap">
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.services" inputId="service-internet"
                      value="internet"/>
            <label for="service-internet" class="ml-2"> Интернет </label>
          </div>
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.services" inputId="service-tv" value="tv"/>
            <label for="service-tv" class="ml-2"> Телевидение </label>
          </div>
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.services" inputId="service-voip" value="voip"/>
            <label for="service-voip" class="ml-2"> VOIP </label>
          </div>
          <div class="me-2 d-flex align-items-center">
            <Checkbox class="me-2" v-model="formData.services" inputId="service-static" value="static"/>
            <label for="service-static" class="ml-2"> Статический IP </label>
          </div>
        </div>

      </div>

      <!-- THIRD STEP -->
      <div v-else-if="current_step===3" class="p-4">

        <div class="d-flex flex-wrap py-2">
          <div class="me-2">
            <h6 class="px-2">ONT ID<Asterisk/></h6>
            <InputText v-model.number="formData.ont_id" type="number"
                       :class="formState.thirdStep.ont_id.valid?['shadow']:['shadow', 'p-invalid']"/>
          </div>
          <div class="me-2">
            <h6 class="px-2">Серийный номер ONT</h6>
            <InputText v-model.trim="formData.ont_serial" type="text"/>
          </div>
          <div class="me-2">
            <h6 class="px-2">MAC адрес ONT</h6>
            <InputText v-model.trim="formData.ont_mac" type="text"/>
          </div>
        </div>

        <div class="d-flex flex-wrap py-2">
          <div class="me-2">
            <h6 class="px-2">Номер наряда</h6>
            <InputText v-model.number="formData.order" type="number" />
          </div>
          <div class="me-2">
            <h6 class="px-2">Дата подключения</h6>
            <Calendar id="calendar-24h" v-model="formData.connected_at" showTime show-icon hourFormat="24"/>
          </div>
        </div>

      </div>

      <!-- LAST STEP -->
      <div v-else-if="current_step===4" class="p-4">
        <h4 class="text-center">Внимательно проверьте введенный данные</h4>

        <h5 class="py-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
            <path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"/>
          </svg>
          Технические данные
        </h5>

        <table class="table table-striped">
          <tbody>
          <tr>
            <td>Оборудование</td>
            <td>{{ formData.techData.deviceName }}</td>
          </tr>

          <tr>
            <td>OLT порт</td>
            <td>{{ formData.techData.devicePort }}</td>
          </tr>

          <tr>
            <td>Дом</td>
            <td>
                <BuildingIcon :type="formData.techData.address.building_type" width="24" height="24"></BuildingIcon>
                {{ getFullAddress(formData.techData.address) }}
                <br>
                <template v-if="formData.techData.address.building_type === 'building'">
                  Многоквартирный дом. Количество этажей: {{ formData.techData.address.floors }} /
                  Количество подъездов: {{ formData.techData.address.total_entrances }}
                </template>
                <template v-else>
                  Частный дом.
                </template>
            </td>
          </tr>

          <tr>
            <td>Существующий {{formData.techData.end3.type}}</td>
            <td>
              {{ getFullAddress(formData.techData.end3.address) }} <br>
              Локация: {{ formData.techData.end3.location }}. <br>
              Кол-во портов: {{ formData.techData.end3.capacity }}
            </td>
          </tr>

          <tr>
            <td>{{formData.techData.end3.type==='splitter'?"Порт сплиттера":"Волокно райзера"}}</td>
            <td>{{formData.techData.end3Port.number}} <TechCapabilityBadge :status="formData.techData.end3Port.status" /></td>
          </tr>
          </tbody>
        </table>

        <h5 class="py-3" v-html="subscriberVerbose(formData.customer.type)"></h5>
        <table class="table table-striped">
          <tbody>

            <tr v-if="formData.customer.type==='person'">
              <td class="col-md-3">ФИО</td>
              <td>{{ formData.customer.firstName }} {{ formData.customer.surname }} {{ formData.customer.lastName }}</td>
            </tr>
            <tr v-else>
              <td class="col-md-3">Название кампании</td>
              <td>{{ formData.customer.companyName }}</td>
            </tr>

            <tr>
              <td class="col-md-3">Лицевой счет</td>
              <td>{{ formData.customer.contract }}</td>
            </tr>
            <tr>
              <td class="col-md-3">Транзит</td>
              <td>{{ formData.transit }}</td>
            </tr>
            <tr>
              <td class="col-md-3">Контактный номер</td>
              <td>{{ formData.customer.phone }}</td>
            </tr>
            <tr>
              <td class="col-md-3">Услуги</td>
              <td>{{ formData.services.join(", ") }}</td>
            </tr>

          </tbody>
        </table>

        <h5 class="py-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
            <path d="M5.525 3.025a3.5 3.5 0 0 1 4.95 0 .5.5 0 1 0 .707-.707 4.5 4.5 0 0 0-6.364 0 .5.5 0 0 0 .707.707Z"/>
            <path d="M6.94 4.44a1.5 1.5 0 0 1 2.12 0 .5.5 0 0 0 .708-.708 2.5 2.5 0 0 0-3.536 0 .5.5 0 0 0 .707.707Z"/>
            <path d="M2.974 2.342a.5.5 0 1 0-.948.316L3.806 8H1.5A1.5 1.5 0 0 0 0 9.5v2A1.5 1.5 0 0 0 1.5 13H2a.5.5 0 0 0 .5.5h2A.5.5 0 0 0 5 13h6a.5.5 0 0 0 .5.5h2a.5.5 0 0 0 .5-.5h.5a1.5 1.5 0 0 0 1.5-1.5v-2A1.5 1.5 0 0 0 14.5 8h-2.306l1.78-5.342a.5.5 0 1 0-.948-.316L11.14 8H4.86L2.974 2.342ZM2.5 11a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1Zm4.5-.5a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Zm2.5.5a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1Zm1.5-.5a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Zm2 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Z"/>
            <path d="M8.5 5.5a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0Z"/>
          </svg>
          Подключение
        </h5>
        <table class="table table-striped">
          <tbody>

            <tr>
              <td class="col-md-3">ONT ID</td>
              <td>{{formData.ont_id}}</td>
            </tr>
            <tr>
              <td class="col-md-3">Серийный номер ONT</td>
              <td>{{ formData.ont_serial }}</td>
            </tr>
            <tr>
              <td class="col-md-3">MAC адрес ONT</td>
              <td>{{ formData.ont_mac }}</td>
            </tr>
            <tr>
              <td class="col-md-3">Номер наряда</td>
              <td>{{ formData.order }}</td>
            </tr>
            <tr>
              <td class="col-md-3">Дата подключения</td>
              <td>{{ formData.connected_at }}</td>
            </tr>

          </tbody>
        </table>

      </div>

      <!-- Ошибки в форме -->
      <div v-if="errors" class="alert alert-danger p-2 text-center">
        <div class="py-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-3"
               viewBox="0 0 16 16">
            <path
                d="M7.005 3.1a1 1 0 1 1 1.99 0l-.388 6.35a.61.61 0 0 1-1.214 0L7.005 3.1ZM7 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0Z"/>
          </svg>
          <span>Были замечены ошибки. Проверьте правильность введенных данных</span>
        </div>
      </div>

      <!-- Кнопки -->
      <div v-if="!form_submitted_successfully" class="d-flex justify-content-between mx-5">

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

      <!-- Успешно создано -->
      <div v-else class="alert alert-success p-2 text-center">
        <div class="py-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-3"
               viewBox="0 0 16 16">
            <path
                d="M12.5 16a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm1.679-4.493-1.335 2.226a.75.75 0 0 1-1.174.144l-.774-.773a.5.5 0 0 1 .708-.708l.547.548 1.17-1.951a.5.5 0 1 1 .858.514ZM8 1c-1.573 0-3.022.289-4.096.777C2.875 2.245 2 2.993 2 4s.875 1.755 1.904 2.223C4.978 6.711 6.427 7 8 7s3.022-.289 4.096-.777C13.125 5.755 14 5.007 14 4s-.875-1.755-1.904-2.223C11.022 1.289 9.573 1 8 1Z"></path>
            <path
                d="M2 7v-.839c.457.432 1.004.751 1.49.972C4.722 7.693 6.318 8 8 8s3.278-.307 4.51-.867c.486-.22 1.033-.54 1.49-.972V7c0 .424-.155.802-.411 1.133a4.51 4.51 0 0 0-4.815 1.843A12.31 12.31 0 0 1 8 10c-1.573 0-3.022-.289-4.096-.777C2.875 8.755 2 8.007 2 7Zm6.257 3.998L8 11c-1.682 0-3.278-.307-4.51-.867-.486-.22-1.033-.54-1.49-.972V10c0 1.007.875 1.755 1.904 2.223C4.978 12.711 6.427 13 8 13h.027a4.552 4.552 0 0 1 .23-2.002Zm-.002 3L8 14c-1.682 0-3.278-.307-4.51-.867-.486-.22-1.033-.54-1.49-.972V13c0 1.007.875 1.755 1.904 2.223C4.978 15.711 6.427 16 8 16c.536 0 1.058-.034 1.555-.097a4.507 4.507 0 0 1-1.3-1.905Z"></path>
          </svg>
          <span>Данные добавлены</span>

        </div>
        <div class="text-center">
          <a href="/gpon/subscriber-data" class="btn btn-outline-success">Вернуться к перечню</a>
        </div>
      </div>
    </div>

    {{ formData }}

  </div>
</template>

<script>
import Calendar from "primevue/calendar/Calendar.vue";
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
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue";
import formatAddress from "../helpers/address";
import api_request from "../api_request";

export default {
  name: "Gpon_base.vue",
  components: {
    AddressGetCreate,
    AddressForm,
    Asterisk,
    BuildingIcon,
    Button,
    Checkbox,
    Calendar,
    Dialog,
    Dropdown,
    InputMask,
    InputText,
    RadioButton,
    RizerFiberColorExample,
    TechCapabilityBadge,
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
      form_submitted_successfully: false,
      errors: null,
      _deviceNames: null,
      _portsNames: null,
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
          contract: {valid: true},
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
                this.contract.valid && this.transit.valid && this.phone.valid
            )
          }
        },
        thirdStep: {
          ont_id: {valid: true},
          isValid() {
            return this.ont_id.valid
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
        customer: {
          type: "person", // person, company, state
          firstName: "", 
          surname: "",
          lastName: "",
          companyName: "",
          contract: null,
          phone: null,
        },
        transit: null,
        order: null,
        services: [],
        ip: null,
        ont_id: null,
        ont_serial: null,
        ont_mac: null,
        connected_at: null,
      }
    }
  },
  computed: {
    devicesList() {
      if (this._deviceNames == null) this.getDeviceNames();
      return this._deviceNames;
    },

    isMobile() {
      return this.windowWidth <= 768
    },

    devicePortList() {
      if (this.formData.techData.deviceName.length === 0) return []
      if (this._portsNames == null) this.getPortsNames();
      return this._portsNames;
    },

  },
  methods: {

    getDeviceNames() {
      api_request.get("/gpon/api/devices-names")
          .then(res => this._deviceNames = Array.from(res.data))
    },
    getPortsNames() {
      api_request.get("/gpon/api/ports-names/" + this.formData.techData.deviceName)
          .then(res => this._portsNames = Array.from(res.data))
    },

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
      this.getPortsNames()
    },


    subscriberVerbose(type) {
      if (type === 'person') {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                  <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"/>
                  <path fill-rule="evenodd" d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1z"/>
                </svg><span>Физ. лицо</span>`
      }
      if (type === 'company') {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                  <path d="M6.5 1A1.5 1.5 0 0 0 5 2.5V3H1.5A1.5 1.5 0 0 0 0 4.5v1.384l7.614 2.03a1.5 1.5 0 0 0 .772 0L16 5.884V4.5A1.5 1.5 0 0 0 14.5 3H11v-.5A1.5 1.5 0 0 0 9.5 1h-3zm0 1h3a.5.5 0 0 1 .5.5V3H6v-.5a.5.5 0 0 1 .5-.5z"/>
                  <path d="M0 12.5A1.5 1.5 0 0 0 1.5 14h13a1.5 1.5 0 0 0 1.5-1.5V6.85L8.129 8.947a.5.5 0 0 1-.258 0L0 6.85v5.65z"/>
                </svg><span>Юр. лицо</span>`
      }
      if (type === 'contract') {
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
        let data = this.formData.customer
        this.formState.secondStep.subscriberType = data.type

        this.formState.secondStep.person.firstName.valid = data.firstName.length > 2
        this.formState.secondStep.person.surname.valid = data.surname.length > 2
        this.formState.secondStep.person.lastName.valid = data.lastName.length > 2

        this.formState.secondStep.companyName.valid = data.companyName.length > 4
        this.formState.secondStep.contract.valid = data.contract != null
        this.formState.secondStep.transit.valid = this.formData.transit != null
        this.formState.secondStep.phone.valid = data.phone != null && data.phone.match(/\d/g).length === 11
        return this.formState.secondStep.isValid()

      } else if (this.current_step === 3) {
        this.formState.thirdStep.ont_id.valid = this.formData.ont_id !== null
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