<template>
  <Header/>

  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
    <div class="flex flex-col gap-6">
      <div class="relative overflow-hidden rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur">
        <div class="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-transparent to-sky-500/10"/>
        <div class="relative p-6 sm:p-8">
          <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div class="max-w-2xl">
              <h1 class="text-2xl sm:text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">
                Устройства
              </h1>
              <p class="mt-2 text-sm sm:text-base text-gray-600 dark:text-gray-300">
                Поиск по имени/IP, фильтры по вендору/модели/группе, закрепление избранных. Опционально — режим сводной
                загрузки интерфейсов.
              </p>

              <div class="mt-5 flex flex-wrap items-center gap-2">
                <Button v-if="displayMode === 'default'" @click="getDeviceWithStats" icon="pi pi-chart-pie" label="Нагрузка по портам" outlined />
                <Button v-else-if="displayMode === 'waiting'" icon="pi pi-spin pi-spinner" label="Загружаю нагрузку..." outlined disabled />
                <Button v-else-if="displayMode === 'interfaces_loading'" @click="getDevices" icon="pi pi-list" label="Обычный вид" outlined />
                <Button @click="getDevices" icon="pi pi-refresh" label="Обновить" severity="secondary" outlined />
              </div>
            </div>

            <div class="hidden lg:block w-[360px]">
              <img class="w-full opacity-90" :src="'/img/device-icon-'+imageIndex+'.svg'" alt="devices">
            </div>
          </div>

          <div v-show="displayMode === 'interfaces_loading'" class="mt-6 grid gap-4 lg:grid-cols-12">
            <div class="lg:col-span-8 rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 p-5">
              <div class="flex items-center justify-between gap-3">
                <div class="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Общая загрузка интерфейсов
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">
                  (по текущему фильтру)
                </div>
              </div>

              <div v-if="chartData.length > 0" class="mt-4 flex flex-col xl:flex-row items-center gap-6">
                <div class="w-[260px] h-[260px] shrink-0">
                  <DoughnutChart :data="chartData"/>
                </div>
                <div class="w-full max-w-[900px]">
                  <BarChart :data="chartData"/>
                </div>
              </div>

              <div v-else class="mt-4 text-sm text-gray-600 dark:text-gray-300">
                Нет данных для построения графиков.
              </div>
            </div>

            <div class="lg:col-span-4 rounded-2xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 p-5">
              <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Легенда</div>
              <div class="mt-3 grid gap-2 text-sm">
                <div class="flex items-center gap-2">
                  <span class="h-3 w-3 rounded bg-green-700"></span>
                  <span class="text-gray-700 dark:text-gray-200">Активные порты с описанием</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="h-3 w-3 rounded bg-green-500"></span>
                  <span class="text-gray-700 dark:text-gray-200">Активные порты без описания</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="h-3 w-3 rounded bg-red-300"></span>
                  <span class="text-gray-700 dark:text-gray-200">Неактивные порты с описанием</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="h-3 w-3 rounded bg-gray-300"></span>
                  <span class="text-gray-700 dark:text-gray-200">Незадействованные порты</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="h-3 w-3 rounded bg-blue-400"></span>
                  <span class="text-gray-700 dark:text-gray-200">Служебные порты</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-4 sm:p-6">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div class="w-full md:max-w-xl">
            <SearchInput @update:modelValue="(v: string) => search = v"
                         :active-mode="true"
                         :init-search="search"
                         placeholder="Поиск по имени или IP адресу"/>
          </div>
          <div class="font-mono text-sm text-gray-600 dark:text-gray-300">
            Найдено: <span class="font-semibold text-gray-900 dark:text-gray-100">{{ devices_count }}</span>
          </div>
        </div>

        <div class="mt-4">
          <DevicesListTable :globalSearch="search" :devices="devices"
                            :groups="groups" :vendors="vendors" :models="models"
                            @filter:devices="processFilteredDevices"
                            @filter:clear="() => search = ''"
                            @update:data="getDevices"/>
        </div>
      </div>
    </div>
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
      devices_count: 0,
      search: this.$route.query.search as string || "",

      groups: [] as string[],
      vendors: [] as string[],
      models: [] as any[],

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
                this.devices_count = devices.length;
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
        if (dev.group && devices_groups.indexOf(dev.group) === -1) {
          devices_groups.push(dev.group || "")
        }
        if (dev.vendor && devices_vendors.indexOf(dev.vendor) === -1) {
          devices_vendors.push(dev.vendor)
          this.models.push({label: dev.vendor, items: []})
        }
        if (dev.model && devices_models.indexOf(dev.model) === -1) {
          this.models.forEach((model) => {
            if (!model.items) {
              model.items = []
            }
            if (model.label === dev.vendor) {
              model.items.push(dev.model)
            }
          });
          devices_models.push(dev.model)
        }
      }
      this.groups = devices_groups.sort((a, b) => a.localeCompare(b))
      this.vendors = devices_vendors.sort((a, b) => a.localeCompare(b))
    },

    calculateInterfacesWorkload(devices: Device[]) {
      if (this.displayMode !== 'interfaces_loading' || !devices.length) {
        this.chartData = []
      } else {
        this.chartData = calculateInterfacesWorkload(devices)
      }
    },

    processFilteredDevices(devices: Device[]): void {
      this.devices_count = devices.length;
      this.calculateInterfacesWorkload(devices);
      this.$router.replace({
        query: {
          ...this.$route.query,
          search: this.search,
        }
      });
    }

  },

});
</script>