<template>
  <Header/>

  <div class="mx-auto max-w-375 px-2 py-2 sm:px-6 sm:py-8 lg:px-8">
    <div class="flex flex-col gap-6">
      <section class="
          relative overflow-hidden
          rounded-3xl sm:rounded-4xl border border-gray-200/70 bg-white/80 dark:border-gray-700/70 dark:bg-gray-900/45
          backdrop-blur
          delay-0
          hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md
         ">
        <div
            class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(99,102,241,0.14),transparent_25%),radial-gradient(circle_at_85%_20%,rgba(14,165,233,0.14),transparent_22%)]"/>

        <div class="relative p-5 sm:p-8">
          <div class="flex flex-col gap-8 xl:flex-row xl:items-start xl:justify-between">
            <div class="max-w-4xl">

              <h1 class="mt-5 text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl">
                Устройства сети
              </h1>

              <p class="mt-3 max-w-3xl text-sm leading-7 text-gray-600 dark:text-gray-300 sm:text-base">
                Поиск по имени и IP, фильтры по вендору, модели и группе, закрепленные устройства и режим сводной
                нагрузки по интерфейсам.
              </p>

              <div class="mt-6 flex flex-wrap items-center gap-2">
                <PinnedDevicesPopover/>
                <Button
                    v-if="displayMode === 'default'"
                    @click="getDeviceWithStats"
                    icon="pi pi-chart-pie"
                    label="Нагрузка по портам"
                    text
                    class="rounded-2xl! hover:shadow-sm"
                />
                <Button
                    v-else-if="displayMode === 'waiting'"
                    icon="pi pi-spin pi-spinner"
                    label="Загружаю нагрузку..."
                    text
                    disabled
                    class="rounded-2xl! hover:shadow-sm"
                />
                <Button
                    v-else-if="displayMode === 'interfaces_loading'"
                    @click="getDevices"
                    icon="pi pi-list"
                    label="Обычный вид"
                    text
                    class="rounded-2xl! hover:shadow-sm"
                />
              </div>

              <div class="mt-2 sm:mt-8 grid gap-3 sm:grid-cols-3">
                <div
                    class="rounded-3xl border border-white/70 bg-white/70 p-4 dark:border-gray-700/80 dark:bg-gray-900/60">
                  <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">
                    Всего
                  </div>
                  <div class="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">{{ devices.length }}</div>
                  <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Устройств в текущем наборе</div>
                </div>
                <div
                    class="rounded-3xl border border-white/70 bg-white/70 p-4 dark:border-gray-700/80 dark:bg-gray-900/60">
                  <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">
                    Найдено
                  </div>
                  <div class="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">{{ devices_count }}</div>
                  <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">После фильтрации и поиска</div>
                </div>
              </div>
            </div>

            <div class="hidden xl:block w-130 shrink-0">
              <div
                  class="rounded-[1.75rem] border border-gray-200/80 bg-white/75 p-5 dark:border-gray-700/80 dark:bg-gray-900/60 hover:shadow-sm">
                <img class="w-full opacity-95" :src="`/img/device-icon-${imageIndex}.svg`" alt="devices">
              </div>
            </div>
          </div>

          <div v-show="displayMode === 'interfaces_loading'" class="mt-8 grid gap-4 xl:grid-cols-12">

            <div
                class="rounded-[1.75rem] border border-gray-200/80 bg-white/30 p-5 dark:border-gray-700/80 dark:bg-gray-900/60 xl:col-span-9">
              <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div class="md:pl-6">
                  <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">Общая загрузка интерфейсов</div>
                  <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">По текущему набору устройств после
                    фильтров.
                  </div>
                </div>
              </div>

              <div v-if="chartData.length > 0" class="mt-5 md:m-5 sm:flex flex-wrap gap-6 xl:flex-row justify-center">
                <div class="sm:shrink-0">
                  <DoughnutChart :data="chartData"/>
                </div>
                <div class="min-w-0 sm:flex-1">
                  <BarChart :data="chartData"/>
                </div>
              </div>

              <div v-else
                   class="mt-4 rounded-2xl border border-dashed border-gray-200/80 bg-gray-50/70 px-4 py-8 text-sm text-gray-500 dark:border-gray-700/80 dark:bg-gray-900/30 dark:text-gray-400">
                Нет данных для построения графиков.
              </div>
            </div>

            <div
                class="rounded-[1.75rem] border border-gray-200/80 bg-white/30 p-5 dark:border-gray-700/80 dark:bg-gray-900/60 xl:col-span-3">
              <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Легенда</div>
              <div class="mt-4 grid gap-3 text-sm">
                <div class="flex items-center gap-3">
                  <span class="h-3 w-3 rounded-full bg-green-700"></span>
                  <span class="text-gray-700 dark:text-gray-200">Активные порты с описанием</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="h-3 w-3 rounded-full bg-green-500"></span>
                  <span class="text-gray-700 dark:text-gray-200">Активные порты без описания</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="h-3 w-3 rounded-full bg-red-300"></span>
                  <span class="text-gray-700 dark:text-gray-200">Неактивные порты с описанием</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="h-3 w-3 rounded-full bg-gray-300"></span>
                  <span class="text-gray-700 dark:text-gray-200">Незадействованные порты</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="h-3 w-3 rounded-full bg-blue-400"></span>
                  <span class="text-gray-700 dark:text-gray-200">Служебные порты</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
          class="rounded-3xl sm:rounded-4xl border border-gray-200/70 bg-white/80 sm:p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.35)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:p-6">
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div class="w-full md:max-w-xl">
            <SearchInput
                @update:modelValue="(v: string) => search = v"
                :active-mode="true"
                :init-search="search"
                placeholder="Поиск по имени или IP адресу"
            />
          </div>
          <div
              class="rounded-2xl sm:border border-gray-200/80 bg-gray-50/80 px-4 py-2 font-mono text-sm text-gray-600 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300">
            Найдено: <span class="font-semibold text-gray-900 dark:text-gray-100">{{ devices_count }}</span>
          </div>
        </div>

        <div class="sm:mt-5">
          <DevicesListTable
              :globalSearch="search"
              :devices="devices"
              :groups="groups"
              :vendors="vendors"
              :models="models"
              @filter:devices="processFilteredDevices"
              @filter:clear="() => search = ''"
              @update:data="getDevices"
          />
        </div>
      </section>
    </div>
  </div>

  <Footer/>
</template>

<script lang="ts">
import {defineComponent} from "vue";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import PinnedDevicesPopover from "@/components/PinnedDevicesPopover.vue";
import SearchInput from "@/components/SearchInput.vue";
import BarChart from "./BarChart.vue";
import DoughnutChart from "./DoughnutChart.vue";
import DevicesListTable from "./DevicesListTable.vue";
import devicesService, {Device} from "@/services/devices";
import {calculateInterfacesWorkload} from "@/services/interfaces";

type DisplayMode = "default" | "waiting" | "interfaces_loading";

export default defineComponent({
  name: "DevicesList",
  components: {
    Footer,
    Header,
    PinnedDevicesPopover,
    BarChart,
    DoughnutChart,
    DevicesListTable,
    SearchInput,
  },
  data() {
    return {
      imageIndex: 0,
      devices: [] as Device[],
      devices_count: 0,
      search: this.$route.query.search as string || "",
      groups: [] as string[],
      vendors: [] as string[],
      models: [] as { label: string; items: string[] }[],
      displayMode: "default" as DisplayMode,
      chartData: [] as number[],
      searchSyncTimer: null as number | null,
    };
  },
  mounted() {
    this.getDevices();
    this.changeImageIndex();
  },
  beforeUnmount() {
    if (this.searchSyncTimer) {
      clearTimeout(this.searchSyncTimer);
      this.searchSyncTimer = null;
    }
  },
  methods: {
    changeImageIndex(): void {
      this.imageIndex = Math.floor(Math.random() * 5) + 1;
    },
    getDevices(): void {
      this.devices = [];
      this.chartData = [];
      devicesService.getDevicesList()
          .then((devices) => {
            this.devices = devices;
            this.devices_count = devices.length;
            this.displayMode = "default";
            this.getUniqueVendorsGroupsModels();
          })
          .catch((reason: any) => console.log(reason));
    },
    getDeviceWithStats(): void {
      this.displayMode = "waiting";
      devicesService.getDevicesListWithInterfacesWorkload()
          .then((devices) => {
            this.devices = devices;
            this.displayMode = "interfaces_loading";
            this.devices_count = devices.length;
            this.getUniqueVendorsGroupsModels();
            this.calculateInterfacesWorkload(devices);
          })
          .catch((reason: any) => console.log(reason));
    },
    getUniqueVendorsGroupsModels() {
      const groupsSet = new Set<string>();
      const vendorsSet = new Set<string>();
      const modelsMap = new Map<string, Set<string>>();

      for (const dev of this.devices) {
        if (dev.group) groupsSet.add(dev.group);
        if (dev.vendor) {
          vendorsSet.add(dev.vendor);
          if (!modelsMap.has(dev.vendor)) {
            modelsMap.set(dev.vendor, new Set<string>());
          }
          if (dev.model) {
            modelsMap.get(dev.vendor)?.add(dev.model);
          }
        }
      }

      this.groups = [...groupsSet].sort((a, b) => a.localeCompare(b));
      this.vendors = [...vendorsSet].sort((a, b) => a.localeCompare(b));
      this.models = [...modelsMap.entries()]
          .sort((a, b) => a[0].localeCompare(b[0]))
          .map(([label, items]) => ({
            label,
            items: [...items].sort((a, b) => a.localeCompare(b))
          }));
    },
    calculateInterfacesWorkload(devices: Device[]) {
      if (this.displayMode !== "interfaces_loading" || !devices.length) {
        this.chartData = [];
        return;
      }
      this.chartData = calculateInterfacesWorkload(devices);
    },
    processFilteredDevices(devices: Device[]): void {
      this.devices_count = devices.length;
      this.calculateInterfacesWorkload(devices);

      if (this.searchSyncTimer) clearTimeout(this.searchSyncTimer);
      this.searchSyncTimer = window.setTimeout(() => {
        this.$router.replace({
          query: {
            ...this.$route.query,
            search: this.search || undefined,
          }
        });
      }, 250);
    }
  },
});
</script>
