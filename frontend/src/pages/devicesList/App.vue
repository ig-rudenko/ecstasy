<template id="app">

  <div class="row py-2">
      <div class="col-md-3">
          <h4 class="fw-bold py-4">Выберите оборудование</h4>
      </div>

<!--        Переключение режимов работы-->
<!--        Нагрузка по портам-->
      <div v-if="displayMode === 'default'" class="col-md-3 py-2">
          <button @click="getDeviceWithStats" class="btn">
              <img src="/static/img/loading_circle.svg" height="50" class="me-2" alt="loading-circle">
              Нагрузка по портам
          </button>
      </div>
<!--        Ожидание-->
      <div v-if="displayMode === 'waiting'" class="col-md-3 py-2">
          <button class="btn">
              <img src="/static/img/loading_circle.svg" class="spinner-border me-2"
                   style="vertical-align: middle; height: 50px; width: 50px; border: none;" alt="loading-circle">
              Нагрузка по портам
          </button>
      </div>
<!--        Обычный режим-->
      <div v-if="displayMode === 'interfaces_loading'" class="col-md-3 py-2">
          <button @click="getDevices" class="btn">
              <img src="/static/img/default_view.svg" height="50" class="me-2" alt="default-view">
              Обычный вид
          </button>
      </div>

<!--    Картинка оборудования-->
      <div class="col-md-6" style="text-align: right">
          <img style="width: 100%" v-bind:src="'/static/img/device-icon-'+imageIndex+'.svg'" alt="search-description-image">
      </div>
  </div>

<!--      Отображение подсказки по нагрузке портов-->
  <div v-show="displayMode === 'interfaces_loading'"
       class="border my-4 rounded-4 row shadow" style="padding: 20px;">

      <!--    Просмотр загрузки оборудования-->
      <div class="col d-flex align-items-start" style="justify-content: center;">
          <div style="display: flex; flex-wrap: wrap; align-content: center; justify-content: center;">
              <h3 class="fs-4 fw-bold">Общая абонентская загрузка интерфейсов</h3>
              <div style="display: block; box-sizing: border-box; height: 270px; width: 270px;">
                  <DoughnutChart :data="chartData" />
              </div>
          </div>
      </div>

      <!--    Фильтр по загруженности-->
      <div class="col d-flex align-items-start">
          <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" fill="currentColor" class="me-3 bi-search" viewBox="0 0 16 16">
              <path d="M3.5 12.5a.5.5 0 0 1-1 0V3.707L1.354 4.854a.5.5 0 1 1-.708-.708l2-1.999.007-.007a.498.498 0 0 1 .7.006l2 2a.5.5 0 1 1-.707.708L3.5 3.707V12.5zm3.5-9a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zM7.5 6a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1h-5zm0 3a.5.5 0 0 0 0 1h3a.5.5 0 0 0 0-1h-3zm0 3a.5.5 0 0 0 0 1h1a.5.5 0 0 0 0-1h-1z"></path>
          </svg>
          <div>
              <h3 class="fs-4 fw-bold">Фильтр по загруженности</h3>
              <p class="">В строке поиска вы можете указывать фильтры.</p>
              <p>Например: отобразить оборудования, загруженность которых больше 50% <kbd class="bg-secondary" style="font-family: monospace; font-size: larger;">::load&gt;50</kbd></p>
              <p>Оборудования, загруженность которых менее 20% <kbd class="bg-secondary" style="font-family: monospace; font-size: larger; ">::load&lt;20</kbd></p>
          </div>
      </div>

      <!--    Расшифровка цвета-->
      <div class="py-2 text-muted">Расшифровка цвета</div>
      <div>
          <div class="progress" style="height: 25px;">
              <div class="progress-bar bg-success" role="progressbar" style="width: 25%; height: 25px;">Активные порты с описанием</div>
              <div class="progress-bar" role="progressbar" style="background-color: rgb(116, 191, 156); width: 25%; height: 25px;">Активные порты без описания</div>
              <div class="progress-bar text-dark" role="progressbar" style="background-color: rgb(255, 189, 189); width: 25%; height: 25px;">Неактивные порты с описанием</div>
              <div class="progress-bar text-dark" role="progressbar" style="background-color: rgb(207, 207, 207); width: 25%; height: 25px;">Прочие неактивные порты</div>
          </div>
      </div>
  </div>


<!--      Строка поиска-->
  <SearchInput
    :update-search="updateSearch"
    :active-mode="displayMode==='interfaces_loading'"
    :placeholder="'Поиск по Имени или IP адресу' + (displayMode==='interfaces_loading'?' и по загруженности ::load':'')"/>


  <ul class="nav nav-tabs">
    <li class="nav-link text-dark">
      Всего найдено: {{ paginator.count }}
    </li>
  </ul>

  <Pagination :p-object="paginator" />

  <div class="table-responsive-lg">
      <DevicesTable
              :current-group="selectedGroup"
              :current-vendor="selectedVendor"
              :groups="groups"
              :vendors="vendors"
              :devices="filteredDevices"
              :set-vendor="setVendor"
              :set-group="setGroup" />
  </div>

  <Pagination :p-object="paginator"/>

  <ScrollTop :threshold="100"/>

</template>

<script lang="ts">
import {defineComponent} from "vue";
import ScrollTop from "primevue/scrolltop";

import DevicesTable from "./DevicesTable.vue";
import Pagination from "../../components/Pagination.vue";
import SearchInput from "../../components/SearchInput.vue";
import DoughnutChart from "./DoughnutChart.vue";
import Paginator from "../../types/paginator";
import api_request from "../../api_request";
import {Device, newDevicesList} from "./devices";

export default defineComponent({
  name: 'DevicesList',

  components: {
    DoughnutChart,
    DevicesTable,
    Pagination,
    SearchInput,
    ScrollTop,
  },

  data() {
    return {
      imageIndex: 0,
      paginator: new Paginator(),
      devices: [] as Array<Device>,
      search: "",
      groups: [] as Array<string>,
      selectedGroup: "",
      vendors: [] as Array<string>,
      selectedVendor: "",
      displayMode: "default",
      chartData: [] as Array<number>,
    }
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
                this.paginator.count = this.devices.length

                // Режим по умолчанию
                this.displayMode = "default"
                this.getUniqueVendorsGroups()
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
                // Кол-во устройств
                this.paginator.count = this.devices.length

                // Включаем режим отображения нагрузки по интерфейсам
                this.displayMode = "interfaces_loading"
                this.getUniqueVendorsGroups()
              }
          )
          .catch((reason: any) => console.log(reason))
    },

    getUniqueVendorsGroups() {
      let devices_groups: Array<string> = []
      let devices_vendors: Array<string> = []
      // Определяем список уникальных имен вендоров и групп
      for (let dev of this.devices) {
          if (dev.group && devices_groups.indexOf(dev.group) === -1){
              devices_groups.push(dev.group || "")
          }
          if (dev.vendor && devices_vendors.indexOf(dev.vendor) === -1){
              devices_vendors.push(dev.vendor)
          }
      }
      this.groups = devices_groups
      this.vendors = devices_vendors
    },

    setVendor(vendor: string) {
      this.selectedVendor = vendor
      this.changeImageIndex()
    },
    setGroup(group: string) {
      this.selectedGroup = group
      this.changeImageIndex()
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
      for (let dev of devicesArray) {

        if (!dev.interfacesCount) continue;

        abonsUpWithDesc += dev.interfacesCount.abonsUpWithDesc
        abonsUpNoDesc += dev.interfacesCount.abonsUpNoDesc
        abonsDownWithDesc += dev.interfacesCount.abonsDownWithDesc
        abonsDownNoDesc += dev.interfacesCount.abonsDownNoDesc
      }
      this.chartData = [abonsUpWithDesc, abonsUpNoDesc, abonsDownWithDesc, abonsDownNoDesc]
    }
  },
  computed: {
    filteredDevices(): Array<Device> {
      let search_str = this.search.toLowerCase()
      let vendor = this.selectedVendor
      let group = this.selectedGroup

      // Фильтруем список устройств
      let array: Array<Device> = this.devices
          .filter(
              (elem: Device) => {
                if (vendor && elem.vendor !== vendor) {
                    return false
                }
                if (group && elem.group !== group) {
                    return false
                }

                if (search_str.length <= 0) return true;

                let match = search_str.match(/^::load([<>=])(\d+)/i)
                if (match && elem.interfacesCount) {
                  let load = match[2]
                  let operator = match[1]

                  let device_loading = elem.interfacesCount.abonsUp / elem.interfacesCount.abons * 100
                  if (operator === "<") {
                    return device_loading <= Number(load)
                  }
                  if (operator === ">") {
                    return device_loading >= Number(load)
                  }
                  if (operator === "=") {
                    return device_loading === Number(load)
                  }
                }

                let name = elem.name.toLowerCase()
                let ip = elem.ip.toLowerCase()
                return name.indexOf(search_str) > -1 || ip.indexOf(search_str) > -1
              }
          )

      // Высчитываем нагруженность интерфейсов для данного фильтра оборудования
      this.calculateInterfacesWorkload(array)

      this.paginator.count = array.length

      // Обрезаем по размеру страницы
      let slice_array = array.slice(
          this.paginator.page * this.paginator.rowsPerPage,
          (this.paginator.page + 1) * this.paginator.rowsPerPage
      )

      if (array.length && slice_array.length === 0) {
        // Если имеются данные по фильтру, но в срезе их нет, надо сбросить страницу
        this.paginator.page = 0

        // Новый срез
        slice_array = array.slice(
            this.paginator.page * this.paginator.rowsPerPage,
            (this.paginator.page + 1) * this.paginator.rowsPerPage)
      }

      return slice_array
    }
  },
  created(){
    this.getDevices()
    this.changeImageIndex()
  },
});
</script>