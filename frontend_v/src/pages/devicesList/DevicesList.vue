<template>
  <Header />

  <div class="container mx-auto p-4">

    <div class="flex flex-wrap justify-center md:grid sm:grid-cols-4 items-center p-4">

      <div class="text-2xl font-bold py-4">Выберите оборудование</div>

      <!--Переключение режимов работы-->
      <!--Нагрузка по портам-->
      <div v-if="displayMode === 'default'" class=" py-2">
        <Button @click="getDeviceWithStats" text >
          <img src="/img/loading_circle.svg" class="me-2 w-[50px]" alt="loading-circle">
          Нагрузка по портам
        </Button>
      </div>
      <!--Ожидание-->
      <div v-if="displayMode === 'waiting'" class=" py-2">
        <Button text>
          <img src="/img/loading_circle.svg" class="pi-spin me-2 w-[50px]" alt="loading-circle">
          Нагрузка по портам
        </Button>
      </div>
      <!--Обычный режим-->
      <div v-if="displayMode === 'interfaces_loading'" class=" py-2">
        <Button @click="getDevices" text>
          <img src="/img/default_view.svg"  class="me-2 w-[50px]" alt="default-view">
          Обычный вид
        </Button>
      </div>

      <!--Картинка оборудования-->
      <div class="col-span-2 w-full" style="text-align: right">
        <img class="w-full" :src="'/img/device-icon-'+imageIndex+'.svg'" alt="search-description-image">
      </div>
    </div>

    <!--Отображение подсказки по нагрузке портов-->
    <div v-show="displayMode === 'interfaces_loading'" class="border my-4 mx-2 rounded-xl row shadow" style="padding: 20px;">
      <!--Просмотр загрузки оборудования-->
      <div v-if="chartData.length > 0">
        <div class="text-2xl">Общая загрузка интерфейсов</div>
        <div class="flex flex-wrap justify-center items-center">
          <div style="display: block; box-sizing: border-box; height: 270px; width: 270px;">
            <DoughnutChart :data="chartData"/>
          </div>
          <div style="display: block; box-sizing: border-box; height: 100%; max-width: 770px; width: 100%;">
            <BarChart :data="chartData"/>
          </div>
        </div>
      </div>

      <!--Расшифровка цвета-->
      <div class="py-2 text-muted-color">Расшифровка цвета</div>
      <div class="flex flex-wrap text-center">
        <div class="bg-green-700 w-full sm:w-[20%] text-gray-200">Активные порты с описанием</div>
        <div class="text-gray-900 bg-green-500 w-full sm:w-[20%]">Активные порты без описания</div>
        <div class="text-gray-900 bg-red-300 w-full sm:w-[20%]">Неактивные порты с описанием</div>
        <div class="text-gray-900 bg-gray-300 w-full sm:w-[20%]">Незадействованные порты</div>
        <div class="text-gray-900 bg-blue-400 w-full sm:w-[20%]">Служебные порты</div>
      </div>
    </div>


    <!-- Строка поиска-->
    <SearchInput @update:modelValue="(v: string) => search = v" :active-mode="true" placeholder="Поиск по Имени или IP адресу"/>

    <div class="p-4 py-2 font-mono">Найдено: {{ devices.length }}</div>

    <DevicesListTable :globalSearch="search" :devices="devices"
                      :groups="groups" :vendors="vendors" :models="models"
                      @filter:devices="processFilteredDevices"
                      @filter:clear="() => search = ''"
                      @update:data="getDevices"/>
  </div>

  <Footer/>

</template>

<script lang="ts">
import {defineComponent} from "vue";
import ScrollTop from "primevue/scrolltop";

import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import SearchInput from "@/components/SearchInput.vue";
import BarChart from "./BarChart.vue";
import DoughnutChart from "./DoughnutChart.vue";
import DevicesListTable from "./DevicesListTable.vue";
import devicesService, {Device} from "@/services/devices";
import {calculateInterfacesWorkload} from "@/services/interfaces";

export default defineComponent({
  name: 'DevicesList',

  components: {
    Footer,
    Header,
    BarChart,
    DoughnutChart,
    DevicesListTable,
    SearchInput,
    ScrollTop,
  },

  data() {
    return {
      imageIndex: 0,
      devices: [] as Device[],
      search: "",

      groups: [] as string[],
      vendors: [] as string[],
      models: [] as string[],

      displayMode: "default",
      chartData: [] as number[],
    }
  },

  mounted() {
    this.getDevices()
    this.changeImageIndex()
  },

  methods: {
    changeImageIndex(): void {
      let min = Math.ceil(1);
      let max = Math.floor(5);
      this.imageIndex = Math.floor(Math.random() * (max - min + 1)) + min;
    },

    /** Метод вызывается при создании */
    getDevices(): void {
      this.devices = []
      devicesService.getDevicesList()
          .then(
              devices => {
                this.devices = devices;
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

      devicesService.getDevicesListWithInterfacesWorkload()
          .then(
              devices => {
                // Список устройств
                this.devices = devices
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

    calculateInterfacesWorkload(devices: Device[]) {
      if (this.displayMode!=='interfaces_loading' || !devices.length) {
        this.chartData = []
      } else {
        this.chartData = calculateInterfacesWorkload(this.devices)
      }
    },

    processFilteredDevices(devices: Device[]): void {
      this.calculateInterfacesWorkload(devices);
    }

  },

});
</script>