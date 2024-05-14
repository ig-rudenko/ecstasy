<template id="app">

  <div class="row py-2">
    <div class="col-md-3"><h4 class="fw-bold py-4">Выберите оборудование</h4></div>

    <!--Переключение режимов работы-->
    <!--Нагрузка по портам-->
      <div v-if="displayMode === 'default'" class="col-md-3 py-2">
          <button @click="getDeviceWithStats" class="btn">
              <img src="/static/img/loading_circle.svg" height="50" class="me-2" alt="loading-circle">
              Нагрузка по портам
          </button>
      </div>
    <!--Ожидание-->
      <div v-if="displayMode === 'waiting'" class="col-md-3 py-2">
          <button class="btn">
              <img src="/static/img/loading_circle.svg" class="spinner-border me-2"
                   style="vertical-align: middle; height: 50px; width: 50px; border: none;" alt="loading-circle">
              Нагрузка по портам
          </button>
      </div>
    <!--Обычный режим-->
      <div v-if="displayMode === 'interfaces_loading'" class="col-md-3 py-2">
          <button @click="getDevices" class="btn">
              <img src="/static/img/default_view.svg" height="50" class="me-2" alt="default-view">
              Обычный вид
          </button>
      </div>

    <!--Картинка оборудования-->
      <div class="col-md-6" style="text-align: right">
          <img style="width: 100%" v-bind:src="'/static/img/device-icon-'+imageIndex+'.svg'" alt="search-description-image">
      </div>
  </div>

  <!--Отображение подсказки по нагрузке портов-->
  <div v-show="displayMode === 'interfaces_loading'"
       class="border my-4 rounded-4 row shadow" style="padding: 20px;">

    <!--Просмотр загрузки оборудования-->
    <div v-if="chartData.length > 0">
      <h3 class="fs-4 fw-bold">Общая загрузка интерфейсов</h3>
      <div class="d-flex flex-wrap justify-content-center align-items-center">
        <div style="display: block; box-sizing: border-box; height: 270px; width: 270px;">
          <DoughnutChart :data="chartData"/>
        </div>
        <div style="display: block; box-sizing: border-box; height: 100%; max-width: 770px; width: 100%;">
          <BarChart :data="chartData"/>
        </div>
          </div>
      </div>

    <!--Расшифровка цвета-->
      <div class="py-2 text-muted">Расшифровка цвета</div>
      <div>
          <div class="progress" style="height: 25px;">
            <div class="progress-bar bg-success" role="progressbar" style="width: 20%; height: 25px;">Активные порты с
              описанием
            </div>
            <div class="progress-bar" role="progressbar"
                 style="background-color: rgb(116, 191, 156); width: 20%; height: 25px;">Активные порты без описания
            </div>
            <div class="progress-bar text-dark" role="progressbar"
                 style="background-color: rgb(255, 189, 189); width: 20%; height: 25px;">Неактивные порты с описанием
            </div>
            <div class="progress-bar text-dark" role="progressbar"
                 style="background-color: rgb(207, 207, 207); width: 20%; height: 25px;">Незадействованные порты
            </div>
            <div class="progress-bar text-dark bg-info" role="progressbar" style="width: 20%; height: 25px;">Служебные
              порты
            </div>
          </div>
      </div>
  </div>


  <!-- Строка поиска-->
  <SearchInput :update-search="updateSearch" :active-mode="true" placeholder="Поиск по Имени или IP адресу"/>


  <ul class="nav nav-tabs">
    <li class="nav-link text-dark">Найдено: {{ devicesCount }}</li>
  </ul>

  <DevicesListTable :globalSearch="search" :devices="devices"
                    :groups="groups" :vendors="vendors" :models="models"
                    @filter:devices="processFilteredDevices"
                    @filter:clear="() => search = ''"
                    @update:data="getDevices"/>

  <ScrollTop :threshold="100"/>

</template>

<script lang="ts">
import {defineComponent} from "vue";
import ScrollTop from "primevue/scrolltop";

import DevicesListTable from "./DevicesListTable.vue";
import Pagination from "../../components/Pagination.vue";
import SearchInput from "../../components/SearchInput.vue";
import DoughnutChart from "./DoughnutChart.vue";
import api_request from "../../api_request";
import {Device, newDevicesList} from "./devices";
import BarChart from "./BarChart.vue";

export default defineComponent({
  name: 'DevicesList',

  components: {
    BarChart,
    DoughnutChart,
    DevicesListTable,
    Pagination,
    SearchInput,
    ScrollTop,
  },

  data() {
    return {
      imageIndex: 0,
      devices: [] as Device[],
      devicesCount: 0,
      search: "",

      groups: [] as Array<string>,
      vendors: [] as Array<string>,
      models: [] as Array<string>,

      displayMode: "default",
      chartData: [] as Array<number>,
    }
  },

  mounted() {
    this.getDevices()
    this.changeImageIndex()
  },

  methods: {
    updateSearch(event: Event): void {
      this.search = (<HTMLInputElement>event.target).value.trim()
    },

    changeImageIndex(): void {
      let min = Math.ceil(1);
      let max = Math.floor(5);
      this.imageIndex = Math.floor(Math.random() * (max - min + 1)) + min;
    },

    /** Метод вызывается при создании */
    getDevices(): void {
      api_request.get("/device/api/list_all")
          .then(
              (value: any) => {
                this.devices = newDevicesList(value.data)
                this.devicesCount = this.devices.length

                // Режим по умолчанию
                this.displayMode = "default"
                this.getUniqueVendorsGroupsModels()
              }
          )
          .catch((reason: any) => console.log(reason))
    },

    getDeviceWithStats(): void {
      // Включаем режим отображения как "загружается"
      this.displayMode = "waiting"

      api_request.get("/device/api/workload/interfaces")
          .then(
              (value: any) => {
                // Список устройств
                this.devices = newDevicesList(value.data.devices)
                this.devicesCount = this.devices.length

                // Включаем режим отображения нагрузки по интерфейсам
                this.displayMode = "interfaces_loading"
                this.getUniqueVendorsGroupsModels()
                this.calculateInterfacesWorkload(this.devices)
              }
          )
          .catch((reason: any) => console.log(reason))
    },

    getUniqueVendorsGroupsModels() {
      let devices_groups: Array<string> = []
      let devices_vendors: Array<string> = []
      let devices_models: Array<string> = []
      // Определяем список уникальных имен вендоров и групп
      for (let dev of this.devices) {
          if (dev.group && devices_groups.indexOf(dev.group) === -1){
              devices_groups.push(dev.group || "")
          }
          if (dev.vendor && devices_vendors.indexOf(dev.vendor) === -1){
              devices_vendors.push(dev.vendor)
          }
        if (dev.model && devices_models.indexOf(dev.model) === -1) {
          devices_models.push(dev.model)
        }
      }
      this.groups = devices_groups
      this.vendors = devices_vendors
      this.models = devices_models
    },

    calculateInterfacesWorkload(devicesArray: Array<Device>) {
      if (this.displayMode!=='interfaces_loading' || !devicesArray.length) {
        this.chartData = []
        return
      }
      let abonsUpWithDesc = 0
      let abonsUpNoDesc = 0
      let abonsDownWithDesc = 0
      let abonsDownNoDesc = 0
      let systems = 0
      for (let dev of devicesArray) {

        if (!dev.interfacesCount) continue;

        const i = dev.interfacesCount

        abonsUpWithDesc += i.abonsUpWithDesc
        abonsUpNoDesc += i.abonsUpNoDesc
        abonsDownWithDesc += i.abonsDownWithDesc
        abonsDownNoDesc += i.abonsDownNoDesc
        systems += i.count - (i.abonsUpWithDesc + i.abonsUpNoDesc + i.abonsDownWithDesc + i.abonsDownNoDesc)
      }
      this.chartData = [abonsUpWithDesc, abonsUpNoDesc, abonsDownWithDesc, abonsDownNoDesc, systems]
    },

    processFilteredDevices(devices: Device[]): void {
      this.devicesCount = devices.length;
      this.calculateInterfacesWorkload(devices);
    }

  },

});
</script>