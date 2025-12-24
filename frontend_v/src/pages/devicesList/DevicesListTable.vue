<template>
  <div class="px-1">
    <DataTable ref="dt" :value="devicesFiltered" v-model:filters="filters" :paginator-position="paginatorPosition"
               :loading="loading" class="font-mono !bg-transparent"
               paginator :rows="50" :rowsPerPageOptions="[10, 20, 50]"
               export-filename="devices" @valueChange="filterDevices"
               filterDisplay="menu" stripedRows size="small" removableSort resizableColumns
               dataKey="ip">

      <template #empty>
        <div v-if="!loading" class="p-4 text-center"><h2>Оборудование не найдено</h2></div>
      </template>

      <template #paginatorstart>
        <div v-tooltip.right="'Обновить данные'" style="cursor: pointer;" @click="updateData">
          <i class="pi pi-refresh text-xl"/>
        </div>
      </template>
      <template #paginatorend>
        <Button severity="success" @click="exportCSV" icon="pi pi-file-excel" fluid outlined
                v-tooltip.left="'Экспорт текущей таблицы по фильтру, но без сортировки'" label="export csv"/>
      </template>

      <!--      IP АДРЕС-->
      <Column field="ip" header="IP" :sortable="true">
        <template #body="{data}">
          <div class="flex flex-row gap-3 items-center group/ip">
            <div>{{ data['ip'] }}</div>
            <a v-if="data['console_url']" :href="data['console_url']"
               class="group/console opacity-0 group-hover/ip:opacity-100 cursor-pointer text-indigo-500"
               target="_blank">
              <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" fill="currentColor"
                   class="inline group-hover/console:hidden" viewBox="0 0 16 16">
                <path
                    d="M6 9a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3A.5.5 0 0 1 6 9M3.854 4.146a.5.5 0 1 0-.708.708L4.793 6.5 3.146 8.146a.5.5 0 1 0 .708.708l2-2a.5.5 0 0 0 0-.708z"/>
                <path
                    d="M2 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2zm12 1a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z"/>
              </svg>
              <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" fill="currentColor"
                   class="hidden group-hover/console:inline" viewBox="0 0 16 16">
                <path
                    d="M0 3a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2zm9.5 5.5h-3a.5.5 0 0 0 0 1h3a.5.5 0 0 0 0-1m-6.354-.354a.5.5 0 1 0 .708.708l2-2a.5.5 0 0 0 0-.708l-2-2a.5.5 0 1 0-.708.708L4.793 6.5z"/>
              </svg>
            </a>
          </div>
        </template>
      </Column>

      <!--      НАЗВАНИЕ-->
      <Column field="name" header="Имя" :sortable="true">
        <template #body="{data}">
          <div class="group/device-name flex items-center gap-1">
            <router-link :to="'/device/'+data.name">
              <Button text icon="pi pi-box" :label="data.name"/>
            </router-link>
            <span class="opacity-0 group-hover/device-name:opacity-100"
                  :class="{'!opacity-100': pinnedDevices.isPinned(data.name)}">
              <PinDevice :device="data"/>
            </span>
          </div>
          <InterfacesWorkload class="p-2" :dev="data"/>
        </template>
      </Column>

      <!--      ЗАГРУЖЕННОСТЬ ИНТЕРФЕЙСОВ-->
      <Column v-if="devices.length > 0 && devices[0].interfaces_count" :showFilterMatchModes="false"
              export-header="Абонентские порты"
              field="interfaces_count.abons_up" header="Абоненты" :sortable="true">
        <template #body="{data}">{{ data.interfaces_count.abons_up }}</template>
        <template #filter>
          <div class="flex gap-1 items-center">
            от
            <InputNumber input-class="w-[5rem]" v-model="workloadRange[0]"/>
            до
            <InputNumber input-class="w-[5rem]" v-model="workloadRange[1]"/>
          </div>
        </template>
        <template #filterapply></template>
        <template #filterclear></template>
      </Column>

      <!--      ВЕНДОР-->
      <Column field="vendor" header="Вендор" :sortable="true" :showFilterMatchModes="false"
              :filterMenuStyle="{ width: '14rem' }">
        <template #body="{data}">
          <Button v-if="data.vendor" @click="filters.vendor.value = data.vendor" text class="ps-9">
            <div class="relative">
              {{ data['vendor'] }}
              <div :style="{'background-color': stringToColour(data.vendor)}"
                   class="absolute -left-6 top-1 p-2 rounded-full">
              </div>
            </div>
          </Button>
        </template>
        <template #filtericon>
          <i :class="filters.vendor.value?'pi pi-filter-fill text-indigo-500':'pi pi-filter'"/>
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <Select focus-on-hover auto-filter-focus auto-option-focus v-model="filterModel.value"
                  @change="filterCallback()" :options="vendors" placeholder="Выбрать"
                  scroll-height="300px" style="min-width: 12rem" :showClear="true">
            <template #option="slotProps">
              <div class="relative ps-10 pb-6">
                <div class="absolute">
                  <span class="m-3 font-mono">{{ slotProps.option }}</span>
                  <div :style="{'background-color': stringToColour(slotProps.option)}"
                       class="absolute -left-6 top-1 p-2 rounded-full">
                  </div>
                </div>
              </div>
            </template>
          </Select>
        </template>
        <template #filterapply></template>
        <template #filterclear></template>
      </Column>

      <!--МОДЕЛЬ-->
      <Column field="model" header="Модель" :sortable="true" :showFilterMatchModes="false">
        <template #body="{data}">
          <div v-if="data.model" class="group/model-filter flex items-center gap-2">
            <div class="">{{ data.model }}</div>
            <Button v-if="filters.model.value != data.model" @click="filters.model.value = data.model"
                    icon="pi pi-filter" size="small"
                    class="opacity-0 group-hover/model-filter:opacity-100" outlined/>
            <Button v-else @click="filters.model.value = null" icon="pi pi-filter-slash" size="small"
                    v-tooltip="'Сбросить фильтр'"
                    class="opacity-0 group-hover/model-filter:opacity-100" outlined/>
          </div>
        </template>
        <template #filtericon>
          <i :class="filters.model.value?'pi pi-filter-fill text-indigo-500':'pi pi-filter'"/>
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <Select v-model="filterModel.value" :showClear="true"
                  filter
                  optionGroupLabel="label" optionGroupChildren="items" @change="filterCallback()" :options="models"
                  scroll-height="400px"
                  placeholder="Выберите модель" class="md:w-80 w-full relative">
            <template #optiongroup="slotProps">
              <div class="relative ps-10 pb-6">
                <div class="absolute">
                  <span class="font-mono">{{ slotProps.option.label }}</span>
                  <div :style="{'background-color': stringToColour(slotProps.option.label)}"
                       class="absolute -left-6 top-1 p-2 rounded-full">
                  </div>
                </div>
              </div>
            </template>
            <template #option="slotProps">
              <div class="ps-3 font-mono">{{ slotProps.option }}</div>
            </template>
          </Select>
        </template>
        <template #filterapply></template>
        <template #filterclear></template>
      </Column>

      <!--      ГРУППА-->
      <Column field="group" header="Группа" :sortable="true" :showFilterMatchModes="false"
              :filterMenuStyle="{ width: '14rem' }">
        <template #body="{data}">
          <div v-if="data.group" class="group/group-filter flex items-center gap-2">
            <div class="">{{ data.group }}</div>
            <Button v-if="filters.group.value != data.group" @click="filters.group.value = data.group"
                    icon="pi pi-filter" size="small"
                    class="opacity-0 group-hover/group-filter:opacity-100" outlined/>
            <Button v-else @click="filters.group.value = null" icon="pi pi-filter-slash" size="small"
                    class="opacity-0 group-hover/group-filter:opacity-100" outlined/>
          </div>
        </template>
        <template #filtericon>
          <i :class="filters.group.value?'pi pi-filter-fill text-indigo-500':'pi pi-filter'"/>
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <Select v-model="filterModel.value" @change="filterCallback()" :options="groups" placeholder="Выбрать"
                  scroll-height="300px"
                  class="p-column-filter" style="min-width: 12rem" :showClear="true">
            <template #option="slotProps">
              <div class="font-mono">{{ slotProps.option }}</div>
            </template>
          </Select>
        </template>
        <template #filterapply></template>
        <template #filterclear></template>
      </Column>
    </DataTable>
  </div>

</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {FilterMatchMode} from "@primevue/core/api";

import {Device} from "@/services/devices";
import InterfacesWorkload from "./InterfacesWorkload.vue";
import PinDevice from "@/components/PinDevice.vue";
import pinnedDevices from "@/services/pinnedDevices.ts";


export default defineComponent({
  name: "DevicesListTable",
  components: {PinDevice, InterfacesWorkload},
  props: {
    devices: {required: true, type: Object as PropType<Device[]>},
    vendors: {required: true, type: Object as PropType<string[]>},
    models: {required: true, type: Object as PropType<any[]>},
    groups: {required: true, type: Object as PropType<string[]>},
    globalSearch: {required: true, type: String},
  },
  emits: ["update:data", "filter:devices", "filter:clear"],

  updated() {
    this.search = this.globalSearch.trim() || "";
  },

  data() {
    return {
      model: null,
      paginatorPosition: undefined as 'top' | 'bottom' | 'both' | undefined,
      search: '',
      _filters: {
        vendor: {value: null, matchMode: FilterMatchMode.EQUALS},
        model: {value: null, matchMode: FilterMatchMode.EQUALS},
        group: {value: null, matchMode: FilterMatchMode.EQUALS},
      } as any,
      workloadRange: [0, 1000]
    }
  },

  computed: {
    pinnedDevices() {
      return pinnedDevices;
    },
    loading() {
      return !this.devices || this.devices.length == 0
    },
    filters: {
      get() {
        if (this.devices.length && this.devices[0].interfaces_count) {
          this._filters["interfaces_count.abons_up"] = {value: this.workloadRange, matchMode: FilterMatchMode.BETWEEN}
        } else {
          this._filters["interfaces_count.abons_up"] = {value: null, matchMode: FilterMatchMode.BETWEEN}
        }
        return this._filters
      },
      set(value: any) {
        this._filters = value
      }
    },

    devicesFiltered(): Device[] {
      if (this.search) {
        const defaultFiltered = this.devices.filter(d => {
          return d.name.toLowerCase().includes(this.search.toLowerCase()) || d.ip.includes(this.search)
        });
        if (defaultFiltered.length) return defaultFiltered;
      }

      if (this.search && this.devices?.length) {
        const names = this.devices.map(d => d.name);
        const matched = this.smartSearch(this.search, names, 0.7);

        let filtered: Device[] = [];
        for (let i = 0; i < matched.length; i++) {
          if (this.devices.find(d => d.name == matched[i])) {
            filtered.push({...this.devices.find(d => d.name == matched[i])!});
          }
        }
        return filtered;
      }
      return this.devices;
    }
  },

  methods: {
    updateData() {
      this.clearFilters();
      this.$emit("update:data");
    },

    clearFilters() {
      this.$emit("filter:clear");
      this.search = "";
      this.filters.vendor.value = null;
      this.filters.model.value = null;
      this.filters.group.value = null;
    },

    stringToColour(str: string): string {
      if (!str) return '';
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
        hash = str.toLowerCase().charCodeAt(i) + ((hash << 5) - hash);
      }
      let c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
      return "#" + "00000".substring(0, 6 - c.length) + c;
    },
    exportCSV() {
      // @ts-ignore
      this.$refs.dt.exportCSV();
    },
    filterDevices(devices: Device[]): void {
      if (devices.length > 10) {
        this.paginatorPosition = 'both';
      } else if (devices.length > 0) {
        this.paginatorPosition = 'top';
      } else {
        this.paginatorPosition = undefined;
      }
      this.$emit("filter:devices", devices)
    },

    // Левенштейн
    levenshtein(a: string, b: string) {
      a = a.toLowerCase();
      b = b.toLowerCase();
      const matrix = [];
      for (let i = 0; i <= b.length; i++) matrix[i] = [i];
      for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
      for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
          if (b.charAt(i - 1) === a.charAt(j - 1)) {
            matrix[i][j] = matrix[i - 1][j - 1];
          } else {
            matrix[i][j] = Math.min(
                matrix[i - 1][j - 1] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j] + 1
            );
          }
        }
      }
      return matrix[b.length][a.length];
    },
    // Коэффициент похожести
    similarity(a: string, b: string) {
      const longer = a.length > b.length ? a : b;
      const shorter = a.length > b.length ? b : a;
      const distance = this.levenshtein(longer, shorter);
      return (longer.length - distance) / longer.length;
    },
    // Умный поиск
    smartSearch(searchStr: string, list: string[], minSimilarity = 0.5) {
      searchStr = searchStr.toLowerCase();
      return list
          .map(item => {
            const itemLower = item.toLowerCase();
            let score = 0;
            if (searchStr.includes(itemLower) || itemLower.includes(searchStr)) {
              score = 1;
            } else {
              const words = searchStr.split(/\s+/).filter(Boolean);
              const wordScores = words.map(w => this.similarity(w, itemLower));
              score = Math.max(...wordScores);
            }
            return {item, score};
          })
          .filter(r => r.score >= minSimilarity)
          .sort((a, b) => b.score - a.score)
          .map(r => r.item);
    }
  }
})
</script>

<style>
ul {
  padding-left: 0 !important;
}

.p-inputtext {
  padding: 0.6rem !important;
}
</style>