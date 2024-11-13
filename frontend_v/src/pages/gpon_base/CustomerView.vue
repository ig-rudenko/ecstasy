<template>

  <Header/>

  <div class="container mx-auto py-5">

    <ConfirmPopup/>

    <div>
      <ViewPrintEditButtons
          @print="printData"
          @changeMode="mode => editMode = mode"
          title=""
          @exit="goBack"
          :has-permission-to-edit="hasPermissionToUpdate"
          :is-mobile="isMobile"/>
    </div>

    <!-- ОШИБКА ЗАГРУЗКИ -->
    <Message v-if="error.status" severity="error">
      Ошибка при загрузке данных.
      <br> {{ error.message || '' }}
      <br> Статус: {{ error.status }}
    </Message>

    <div id="subscriber-data-block">

      <div v-if="customer" class="flex flex-wrap items-center justify-center">
        <img class="header-image" style="max-height: 400px" :src="'/img/gpon/subscriber-'+gender+'.svg'"
             alt="subscriber-image">

        <div class="w-full md:w-2/3 xl:w-1/2 sm:border shadow rounded-xl p-4 sm:p-10 flex flex-col">

          <Select v-if="editMode" v-model="customer.type" fluid
                  :options="['person','company','contract']" style="width: 100%"
                  placeholder="Выберите тип абонента">
            <template #value="slotProps">
              <div v-if="slotProps.value" class="flex align-items-center"
                   v-html="subscriberVerbose(slotProps.value)"></div>
              <span v-else>{{ slotProps.placeholder }}</span>
            </template>
            <template #option="slotProps">
              <div class="flex items-center" v-html="subscriberVerbose(slotProps.option)"></div>
            </template>
          </Select>

          <!-- ФАМИЛИ ИМЯ ОТЧЕСТВО АБОНЕНТА -->
          <template v-if="customer.type==='person'">
            <template v-if="editMode">
              <div class="grid md:grid-cols-2 gap-4 py-2">
                <div>
                  <div class="px-2 flex items-center gap-1 pb-2">
                    Фамилия
                    <Asterisk/>
                  </div>
                  <InputText v-model.trim="customer.surname" fluid/>
                </div>

                <div>
                  <div class="px-2 flex items-center gap-1 pb-2">
                    Имя
                    <Asterisk/>
                  </div>
                  <InputText v-model.trim="customer.firstName" fluid/>
                </div>
              </div>

              <div class="py-2">
                <div class="px-2 flex items-center gap-1 pb-2">
                  Отчество
                  <Asterisk/>
                </div>
                <InputText v-model.trim="customer.lastName" fluid/>
              </div>
            </template>
            <div class="text-2xl p-2" v-else>{{ fullName }}</div>
          </template>

          <!-- НАЗВАНИЕ КОМПАНИИ -->
          <template v-else>
            <div v-if="editMode" class="p-2 w-100">
              <h6 class="px-2 flex items-center gap-1 pb-2">
                Название кампании
                <Asterisk/>
              </h6>
              <InputText v-model.trim="customer.companyName" fluid/>
            </div>
            <h4 class="text-2xl py-2" v-else>{{ customer.companyName }}</h4>
          </template>

          <!-- НОМЕР ТЕЛЕФОНА -->
          <div class="text-secondary flex items-center gap-2 py-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" viewBox="0 0 16 16">
              <path fill-rule="evenodd"
                    d="M1.885.511a1.745 1.745 0 0 1 2.61.163L6.29 2.98c.329.423.445.974.315 1.494l-.547 2.19a.678.678 0 0 0 .178.643l2.457 2.457a.678.678 0 0 0 .644.178l2.189-.547a1.745 1.745 0 0 1 1.494.315l2.306 1.794c.829.645.905 1.87.163 2.611l-1.034 1.034c-.74.74-1.846 1.065-2.877.702a18.634 18.634 0 0 1-7.01-4.42 18.634 18.634 0 0 1-4.42-7.009c-.362-1.03-.037-2.137.703-2.877L1.885.511z"/>
            </svg>
            <InputMask v-if="editMode" v-model="customer.phone" date="phone" style="width: 100%"
                       mask="+7 (999) 999-99-99" placeholder="+7 (999) 999-99-99"/>
            <div class="text-xl font-mono" v-else>{{ customer.phone || '-' }}</div>
          </div>

          <!-- НОМЕР КОНТРАКТА -->
          <div class="text-secondary flex items-center gap-2 py-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
              <path d="M11 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"/>
              <path
                  d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2v9.255S12 12 8 12s-5 1.755-5 1.755V2a1 1 0 0 1 1-1h5.5v2z"/>
            </svg>
            <InputText v-if="editMode" v-model.trim="customer.contract" type="text" style="width: 100%"/>
            <div class="text-xl font-mono" v-else>{{ customer.contract || '-' }}</div>
          </div>

          <!-- Сохранить изменения -->
          <div class="pt-3">
            <Button v-if="editMode" @click="updateCustomerData" class="save-button" text severity="success">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
                <path
                    d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
              </svg>
              <span v-if="!isMobile">Обновить</span>
            </Button>
          </div>

        </div>
      </div>

      <div class="mx-auto xl:w-3/4">
        <div v-if="customer">
          <div class="text-xl p-4">Подключения:</div>

          <div v-for="connection in customer.connections" class="sm:border rounded-xl shadow mb-4 relative">

            <!-- УДАЛЕНИЕ ПОДКЛЮЧЕНИЯ -->
            <div v-if="editMode && hasPermissionToDeleteConnection" class="md:absolute p-4 md:p-0 -top-5 -right-5">
              <Button @click="deleteConnection($event, connection)" severity="danger" rounded
                      icon="pi pi-trash"/>
            </div>

            <!-- АДРЕС ПОДКЛЮЧЕНИЯ -->
            <div class="p-3">
              <AddressGetCreate
                  v-if="editMode && hasPermissionToUpdateConnection"
                  :is-mobile="isMobile"
                  :allow-create="true"
                  :data="connection"
                  :is-subscriber-address="true"/>
              <div v-else class="text-xl sm:text-2xl text-center">
                <div class="me-3">{{ getFullAddress(connection.address) }}</div>
                <div>Статус подключения:
                  <TechCapabilityBadge :status="connection.status"/>
                </div>
              </div>
            </div>

            <!-- Описание подключения -->
            <div v-if="editMode && hasPermissionToUpdateConnection" class="flex flex-wrap px-2">
              <div class="px-2 pb-2">Описание подключения</div>
              <div class="px-2 w-full">
                <Textarea v-model.trim="connection.description" fluid auto-resize/>
              </div>
            </div>
            <div v-else-if="connection.description" class="mx-4 p-3">{{ connection.description }}</div>

            <div class="flex flex-wrap items-center justify-center gap-y-6 p-3">

              <!-- ОБОРУДОВАНИЕ И ПОРТ -->
              <template v-if="!(editMode && hasPermissionToUpdateConnection)">
                <div class="flex flex-wrap sm:flex-col justify-center text-right">
                  <!--DEVICE LINK-->
                  <router-link :to="{name: 'device', params: {deviceName: connection.houseOLTState.deviceName}}"
                               target="_blank">
                    <Button outlined severity="help">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                           viewBox="0 0 16 16">
                        <path
                            d="M2 9a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1a2 2 0 0 0-2-2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1m2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1M2 2a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1m2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1"/>
                      </svg>
                      {{ connection.houseOLTState.deviceName }}
                    </Button>
                  </router-link>

                  <!--INTERFACE LINK-->
                  <router-link :to="{
                        name: 'gpon-olt-tech-data',
                        params: {deviceName: connection.houseOLTState.deviceName},
                        query: {port: connection.houseOLTState.devicePort}
                      }" class="font-bold" target="_blank">
                    <Button text>
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                           viewBox="0 0 16 16">
                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
                        <path
                            d="M5 6.5A1.5 1.5 0 0 1 6.5 5h3A1.5 1.5 0 0 1 11 6.5v3A1.5 1.5 0 0 1 9.5 11h-3A1.5 1.5 0 0 1 5 9.5z"/>
                      </svg>
                      {{ connection.houseOLTState.devicePort }}
                    </Button>
                  </router-link>
                </div>

                <!-- ТЕХНИЧЕСКИЕ ДАННЫЕ -->
                <div class="p-3 flex justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor"
                       style="transform: rotate(270deg)" viewBox="0 0 16 16">
                    <path fill-rule="evenodd"
                          d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5v-1zm-6 8A1.5 1.5 0 0 1 1.5 10h1A1.5 1.5 0 0 1 4 11.5v1A1.5 1.5 0 0 1 2.5 14h-1A1.5 1.5 0 0 1 0 12.5v-1zm6 0A1.5 1.5 0 0 1 7.5 10h1a1.5 1.5 0 0 1 1.5 1.5v1A1.5 1.5 0 0 1 8.5 14h-1A1.5 1.5 0 0 1 6 12.5v-1zm6 0a1.5 1.5 0 0 1 1.5-1.5h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5v-1z"/>
                  </svg>
                  <router-link
                      :to="{name: 'gpon-end3-tech-data', params: {id: connection.end3.id}, query: {backref: $route.href}}">
                    <Button outlined severity="contrast">
                      <div class="flex flex-col">
                        <div>{{ connection.end3.location }}</div>
                        <div>{{ connection.end3.type }} port: {{ connection.end3Port }}</div>
                      </div>
                    </Button>
                  </router-link>
                </div>
              </template>

              <!-- Редактируем точку подключения -->
              <div v-else class="flex flex-wrap justify-center items-center gap-3 p-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor" class="me-3"
                     style="transform: rotate(270deg)" viewBox="0 0 16 16">
                  <path fill-rule="evenodd"
                        d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5v-1zm-6 8A1.5 1.5 0 0 1 1.5 10h1A1.5 1.5 0 0 1 4 11.5v1A1.5 1.5 0 0 1 2.5 14h-1A1.5 1.5 0 0 1 0 12.5v-1zm6 0A1.5 1.5 0 0 1 7.5 10h1a1.5 1.5 0 0 1 1.5 1.5v1A1.5 1.5 0 0 1 8.5 14h-1A1.5 1.5 0 0 1 6 12.5v-1zm6 0a1.5 1.5 0 0 1 1.5-1.5h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5v-1z"/>
                </svg>

                <div class="py-2 overflow-auto" v-if="connection.address">
                  <!-- ПОИСК СПЛИТТЕРОВ/РАЙЗЕРОВ В ВЫБРАННОМ ДОМЕ -->
                  <SplittersRizersFind @change="e => connection.end3 = e.value" :init="connection.end3"/>
                </div>

                <div v-if="connection.end3 && connection.address">
                  <!-- ПОИСК СВОБОДНОГО ПОДКЛЮЧЕНИЯ У ВЫБРАННОГО СПЛИТТЕРА/РАЙЗЕРА -->
                  <SelectSplitterRizerPort :init="{number: connection.end3Port, status: connection.status}"
                                           :end3ID="connection.end3.id"
                                           @change="e => {connection.end3Port = e.value.number; connection.tech_capability_id = e.value.id}"
                                           :get-from="connection.end3" :type="connection.end3.type"
                                           :only-unused-ports="false">
                  </SelectSplitterRizerPort>
                </div>

              </div>

              <!-- ДАННЫЕ ONT -->
              <div class="flex gap-x-4 items-center p-2" :class="editMode?'w-full flex-col':'flex-row'">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor" viewBox="0 0 16 16">
                  <path
                      d="M5.525 3.025a3.5 3.5 0 0 1 4.95 0 .5.5 0 1 0 .707-.707 4.5 4.5 0 0 0-6.364 0 .5.5 0 0 0 .707.707Z"/>
                  <path
                      d="M6.94 4.44a1.5 1.5 0 0 1 2.12 0 .5.5 0 0 0 .708-.708 2.5 2.5 0 0 0-3.536 0 .5.5 0 0 0 .707.707Z"/>
                  <path
                      d="M2.974 2.342a.5.5 0 1 0-.948.316L3.806 8H1.5A1.5 1.5 0 0 0 0 9.5v2A1.5 1.5 0 0 0 1.5 13H2a.5.5 0 0 0 .5.5h2A.5.5 0 0 0 5 13h6a.5.5 0 0 0 .5.5h2a.5.5 0 0 0 .5-.5h.5a1.5 1.5 0 0 0 1.5-1.5v-2A1.5 1.5 0 0 0 14.5 8h-2.306l1.78-5.342a.5.5 0 1 0-.948-.316L11.14 8H4.86L2.974 2.342ZM2.5 11a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1Zm4.5-.5a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Zm2.5.5a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1Zm1.5-.5a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Zm2 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Z"/>
                  <path d="M8.5 5.5a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0Z"/>
                </svg>

                <!-- РЕДАКТИРОВАНИЕ ДАННЫХ ONT -->
                <div v-if="editMode && hasPermissionToUpdateConnection" class="flex flex-col w-full">
                  <div class="grid sm:grid-cols-2 md:grid-cols-3 gap-2">
                    <div class="w-full">
                      <div class="p-2 flex items-center gap-1">
                        ONT ID
                        <Asterisk/>
                      </div>
                      <InputText v-model.number="connection.ont_id" type="number" fluid/>
                    </div>
                    <div class="w-full">
                      <div class="p-2">Серийный номер ONT</div>
                      <InputText v-model.trim="connection.ont_serial" type="text" fluid/>
                    </div>
                    <div class="w-full">
                      <div class="p-2">MAC адрес ONT</div>
                      <InputText v-model.trim="connection.ont_mac" type="text" fluid/>
                    </div>

                    <div class="w-full">
                      <div class="p-2">IP Адрес</div>
                      <InputText v-model.trim="connection.ip" type="text" fluid/>
                    </div>
                    <div class="w-full">
                      <div class="p-2">Номер наряда</div>
                      <InputText v-model.number="connection.order" type="number" fluid/>
                    </div>
                    <div class="w-full">
                      <div class="p-2">Дата подключения</div>
                      <DatePicker id="calendar-24h" dateFormat="dd/mm/yy" v-model="connection.connected_at"
                                  showTime fluid show-icon hourFormat="24"/>
                    </div>
                  </div>
                </div>

                <div v-else class="grid">
                  <div v-if="connection.ip">IP {{ connection.ip }}</div>
                  <div v-if="connection.ont_mac" class="font-mono">MAC: {{ connection.ont_mac }}</div>
                  <div class="font-mono">ONT ID:
                    <span class="px-2 bg-primary-400 rounded">{{ connection.ont_id }}</span>
                  </div>
                  <div v-if="connection.ont_serial">
                    <div>Серийный номер ONT:</div>
                    <div class="font-mono">{{ connection.ont_serial }}</div>
                  </div>
                </div>
              </div>
              <!------------------->

              <!-- ТРАНЗИТ и НАРЯД -->
              <div class="flex gap-3 p-3 items-center"
                   :class="editMode && hasPermissionToUpdateConnection?'flex-row':''">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor"
                     viewBox="0 0 16 16">
                  <path
                      d="M5 4a.5.5 0 0 0 0 1h6a.5.5 0 0 0 0-1H5zm-.5 2.5A.5.5 0 0 1 5 6h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5zM5 8a.5.5 0 0 0 0 1h6a.5.5 0 0 0 0-1H5zm0 2a.5.5 0 0 0 0 1h3a.5.5 0 0 0 0-1H5z"/>
                  <path
                      d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2zm10-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1z"/>
                </svg>
                <div class="flex items-center gap-2">
                  <div v-if="editMode && hasPermissionToUpdateConnection">
                    <div class="p-3">
                      <h6 class="px-2 flex items-center gap-1 pb-2">Транзит
                        <Asterisk/>
                      </h6>
                      <InputText v-model.number="connection.transit" type="number"/>
                    </div>
                  </div>
                  <div v-else class="grid gap-1">
                    <div class="grid grid-cols-2 gap-2">
                      <div class="fw-bold me-2">Транзит</div>
                      <div class="font-mono">{{ connection.transit }}</div>
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                      <div class="fw-bold me-4">Наряд</div>
                      <div class="font-mono">{{ connection.order }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="editMode && hasPermissionToUpdateConnection" class="p-3">
              <h6 class="p-2">Выберите услуги</h6>
              <div class="flex flex-wrap p-2">
                <div class="me-2 flex items-center gap-2">
                  <Checkbox v-model="connection.services" inputId="service-internet" value="internet"/>
                  <label for="service-internet" class="cursor-pointer">Интернет</label>
                </div>
                <div class="me-2 flex items-center gap-2">
                  <Checkbox v-model="connection.services" inputId="service-tv" value="tv"/>
                  <label for="service-tv" class="cursor-pointer">Телевидение</label>
                </div>
                <div class="me-2 flex items-center gap-2">
                  <Checkbox v-model="connection.services" inputId="service-voip" value="voip"/>
                  <label for="service-voip" class="cursor-pointer">VOIP</label>
                </div>
                <div class="me-2 flex items-center gap-2">
                  <Checkbox v-model="connection.services" inputId="service-static" value="static"/>
                  <label for="service-static" class="cursor-pointer">Статический IP</label>
                </div>
              </div>
            </div>

            <!-- Сохранить изменения -->
            <div class="p-3">
              <Button text v-if="editMode" @click="updateCustomerConnection(connection)" class="save-button"
                      severity="success">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
                  <path
                      d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
                </svg>
                <span v-if="!isMobile">Обновить</span>
              </Button>
            </div>

          </div> <!-- end for -->

        </div><!-- end if -->

      </div>


    </div>

  </div>

  <Footer/>

</template>

<script>
import Asterisk from "./components/Asterisk.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue";
import ViewPrintEditButtons from "./components/ViewPrintEditButtons.vue";
import api from "@/services/api";
import {formatAddress} from "@/formats";
import getSubscriberTypeVerbose from "@/helpers/subscribers";
import printElementById from "@/helpers/print";
import AddressGetCreate from "./components/AddressGetCreate.vue";
import SelectSplitterRizerPort from "./components/SelectSplitterRizerPort.vue";
import SplittersRizersFind from "./components/SplittersRizersFind.vue";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "CustomerView",
  components: {
    Footer,
    Header,
    SplittersRizersFind,
    SelectSplitterRizerPort,
    AddressGetCreate,
    Asterisk,
    TechCapabilityBadge,
    ViewPrintEditButtons,
  },

  data() {
    return {
      subscriberID: 0,
      customer: null,
      userPermissions: [],
      windowWidth: window.innerWidth,
      editMode: false,
      error: {
        status: null,
        message: null,
      }
    }
  },

  mounted() {
    this.subscriberID = this.$route.params.id;

    window.addEventListener('resize', () => {
      this.windowWidth = window.innerWidth
    });
    api.get("/api/v1/gpon/permissions").then(resp => {
      this.userPermissions = resp.data
    });
    this.getSubscriberData();
  },

  computed: {
    fullName() {
      return this.customer.surname + " " + this.customer.firstName + " " + this.customer.lastName
    },

    gender() {
      if (this.customer.type === "company") return "company";
      if (this.customer.type === "contract") return "contract";
      const lastName = this.customer.lastName;
      if (!lastName) return "man";
      if (RegExp(/\S+в?ич$/).test(lastName)) return "man"
      if (RegExp(/\S+в?на$/).test(lastName)) return "woman"
      return "man"
    },

    hasPermissionToUpdate() {
      return [
        "gpon.change_customer",
        "gpon.change_subscriberconnection",
      ].every(elem => {
        return this.userPermissions.includes(elem)
      })
    },

    hasPermissionToDeleteConnection() {
      return this.userPermissions.includes("gpon.delete_subscriberconnection")
    },

    hasPermissionToUpdateConnection() {
      return this.userPermissions.includes("gpon.change_subscriberconnection")
    },

    isMobile() {
      return this.windowWidth <= 768
    },


  },

  methods: {

    goBack() {
      history.go(-1)
    },

    getSubscriberData() {
      api.get("/api/v1/gpon/customers/" + this.subscriberID)
          .then(resp => this.customer = resp.data)
          .catch(reason => {
            this.error.status = reason.response.status
            this.error.message = reason.response.data
          })
    },

    printData() {
      printElementById('subscriber-data-block')
    },

    getFullAddress(address) {
      let address_string = formatAddress(address)
      if (address.apartment) {
        address_string += ` кв. ${address.apartment}`
      }
      if (address.floor) {
        address_string += ` (${address.floor} этаж)`
      }
      return address_string
    },

    updateCustomerData() {
      const data = {
        type: this.customer.type,
        companyName: this.customer.companyName,
        firstName: this.customer.firstName,
        surname: this.customer.surname,
        lastName: this.customer.lastName,
        phone: this.customer.phone,
        contract: this.customer.contract,
      }
      this.handleRequest(
          api.put("/api/v1/gpon/customers/" + this.customer.id, data),
          "Данные абонента были успешно обновлены"
      )
    },

    updateCustomerConnection(connection) {
      connection.customer = this.customer.id
      this.handleRequest(
          api.put("/api/v1/gpon/subscriber-connection/" + connection.id, connection),
          "Данные абонентского подключения были успешно обновлены"
      ).then(value => connection = value)
    },

    deleteConnection(event, connection) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Вы уверены, что хотите удалить данное подключение?',
        icon: 'pi pi-info-circle',
        acceptLabel: "Да",
        rejectLabel: "Нет",
        acceptClass: 'p-button-danger p-button-sm',
        defaultFocus: "reject",
        accept: () => {
          api.delete("/api/v1/gpon/subscriber-connection/" + connection.id).then(
              () => {
                this.$toast.add({
                  severity: 'error',
                  summary: 'Confirmed',
                  detail: 'Подключение было удалено',
                  life: 3000
                });
                this.getSubscriberData();  // Обновляем данные абонента
              }
          ).catch(
              reason => this.$toast.add({
                severity: 'error',
                summary: reason.response.status,
                detail: reason.response.data,
                life: 3000
              })
          )
        },
        reject: () => {
        }
      });
    },

    subscriberVerbose(type) {
      return getSubscriberTypeVerbose(type)
    },

    /**
     * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
     * @param {Promise} request
     * @param {String} successInfo
     */
    handleRequest(request, successInfo) {
      return request.then(
          () => {
            this.$toast.add({severity: 'success', summary: 'Обновлено', detail: successInfo, life: 3000});
          }
      )
          .catch(
              reason => {
                const status = reason.response.status
                this.$toast.add({
                  severity: 'error',
                  summary: `Ошибка ${status}`,
                  detail: reason.response.data,
                  life: 5000
                })
              }
          )
    },

  },

}
</script>

<style scoped>

.save-button {
  border-radius: 12px;
  color: #008b1e;
  border: 1px #008b1e solid;
}

.save-button:hover {
  box-shadow: 0 0 3px #008b1e;
}

@media (max-width: 835px) {

  .shadow {
    box-shadow: none !important;
  }

  img {
    max-height: 300px !important;
  }

}

</style>