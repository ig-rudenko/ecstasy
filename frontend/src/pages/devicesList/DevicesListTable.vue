<template>
  <div>
    <DataTable ref="dt" :value="devices" v-model:filters="filters" :paginator-position="paginatorPosition"
               :loading="loading"
               paginator :rows="50" :rowsPerPageOptions="[10, 20, 50]"
               export-filename="devices" @valueChange="filterDevices"
               filterDisplay="menu" stripedRows size="small" removableSort
               dataKey="ip" :globalFilterFields="['name', 'ip']">

      <template #empty>
        <div v-if="!loading" class="p-4 text-center"><h2>Оборудование не найдено</h2></div>
      </template>

      <template #paginatorstart>
        <div v-tooltip.right="'Обновить данные'" style="cursor: pointer;" @click="updateData">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor"
               class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
            <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2z"/>
            <path
                d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466"/>
          </svg>
        </div>
      </template>
      <template #paginatorend>
        <button class="btn btn-outline-success" @click="exportCSV"
                v-tooltip.left="'Экспорт текущей таблицы по фильтру, но без сортировки'">export csv
        </button>
      </template>

      <!--      IP АДРЕС-->
      <Column field="ip" header="IP" :sortable="true">
        <template #body="{data}">{{ data['ip'] }}</template>
      </Column>

      <!--      НАЗВАНИЕ-->
      <Column field="name" header="Имя" :sortable="true">
        <template #body="{data}">
          <a class="text-decoration-none nowrap btn btn-outline-primary" style="border: none;"
             :href="'/device/' + data.name">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-right"
                 viewBox="0 0 16 16">
              <path
                  d="M6 12.796V3.204L11.481 8 6 12.796zm.659.753 5.48-4.796a1 1 0 0 0 0-1.506L6.66 2.451C6.011 1.885 5 2.345 5 3.204v9.592a1 1 0 0 0 1.659.753z"/>
            </svg>
            {{ data['name'] }}
          </a>
          <InterfacesWorkload class="p-2" :dev="data"/>
        </template>
      </Column>

      <!--      ЗАГРУЖЕННОСТЬ ИНТЕРФЕЙСОВ-->
      <Column v-if="devices.length > 0 && devices[0].interfacesCount" :showFilterMatchModes="false"
              export-header="Абонентские порты"
              field="interfacesCount.abonsUp" header="Абоненты" :sortable="true">
        <template #body="{data}">{{ data['interfacesCount'].abonsUp }}</template>
        <template #filter>
          <div class="d-flex gap-1 align-items-center">
            от
            <InputText style="width: 5rem;" v-model="workloadRange[0]"/>
            до
            <InputText style="width: 5rem;" v-model="workloadRange[1]"/>
          </div>
        </template>
        <template #filterapply></template>
        <template #filterclear></template>
      </Column>

      <!--      ВЕНДОР-->
      <Column field="vendor" header="Вендор" :sortable="true" :showFilterMatchModes="false"
              :filterMenuStyle="{ width: '14rem' }">
        <template #body="{data}">
          <button v-if="data.vendor" @click="filters.vendor.value = data.vendor" class="btn position-relative">
            {{ data['vendor'] }}
            <span :style="{'background-color': stringToColour(data.vendor)}"
                  class="position-absolute top-50 start-0 translate-middle p-2 border border-light rounded-circle">
            </span>
          </button>
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <Dropdown focus-on-hover auto-filter-focus auto-option-focus v-model="filterModel.value"
                    @change="filterCallback()" :options="vendors" placeholder="Выбрать"
                    scroll-height="300px" style="min-width: 12rem" :showClear="true">
            <template #option="slotProps">
              <span class="position-absolute">
                <span class="m-3">{{ slotProps.option }}</span>
                <span :style="{'background-color': stringToColour(slotProps.option)}"
                      class="position-absolute top-50 start-0 translate-middle p-2 border border-light rounded-circle"></span>
              </span>
            </template>
          </Dropdown>
        </template>
        <template #filterapply></template>
        <template #filterclear></template>
      </Column>

      <!--      МОДЕЛЬ-->
      <Column field="model" header="Модель" :sortable="true" :showFilterMatchModes="false"
              :filterMenuStyle="{ width: '20rem' }">
        <template #body="{data}">{{ data['model'] }}</template>
        <template #filter="{ filterModel, filterCallback }">
          <Dropdown v-model="filterModel.value" @change="filterCallback()" :options="models" placeholder="Выбрать"
                    scroll-height="300px"
                    class="p-column-filter" style="min-width: 15rem" :showClear="true">
            <template #option="slotProps">
              <div class="position-absolute">{{ slotProps.option }}</div>
            </template>
          </Dropdown>
        </template>
        <template #filterapply></template>
        <template #filterclear></template>
      </Column>

      <!--      ГРУППА-->
      <Column field="group" header="Группа" :sortable="true" :showFilterMatchModes="false"
              :filterMenuStyle="{ width: '14rem' }">
        <template #body="{data}">{{ data['group'] }}</template>
        <template #filter="{ filterModel, filterCallback }">
          <Dropdown v-model="filterModel.value" @change="filterCallback()" :options="groups" placeholder="Выбрать"
                    scroll-height="300px"
                    class="p-column-filter" style="min-width: 12rem" :showClear="true">
            <template #option="slotProps">
              <div class="position-absolute">{{ slotProps.option }}</div>
            </template>
          </Dropdown>
        </template>
        <template #filterapply></template>
        <template #filterclear></template>
      </Column>
    </DataTable>
  </div>

</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dropdown from "primevue/dropdown";
import InputText from "primevue/inputtext";
import Slider from "primevue/slider";

import {FilterMatchMode} from "primevue/api";
import InterfacesWorkload from "./InterfacesWorkload.vue";
import {Device} from "./devices";


export default defineComponent({
  name: "DevicesListTable",
  components: {InterfacesWorkload, Button, Column, DataTable, Dropdown, InputText, Slider},
  props: {
    devices: {required: true, type: Object as PropType<Device[]>},
    vendors: {required: true},
    models: {required: true},
    groups: {required: true},
    globalSearch: {required: true, type: String},
  },
  emits: ["update:data", "filter:devices", "filter:clear"],

  updated() {
    this.filters.global.value = this.globalSearch;
  },

  data() {
    return {
      paginatorPosition: 'both' as 'top' | 'bottom' | 'both' | undefined,
      _filters: {
        global: {value: "", matchMode: FilterMatchMode.CONTAINS},
        vendor: {value: null, matchMode: FilterMatchMode.EQUALS},
        model: {value: null, matchMode: FilterMatchMode.EQUALS},
        group: {value: null, matchMode: FilterMatchMode.EQUALS},
      },
      workloadRange: [0, 1000]
    }
  },

  computed: {
    loading() {
      return !this.devices || this.devices.length == 0
    },
    filters: {
      get() {
        if (this.devices.length && this.devices[0].interfacesCount) {
          this._filters["interfacesCount.abonsUp"] = {value: this.workloadRange, matchMode: FilterMatchMode.BETWEEN}
        } else {
          this._filters["interfacesCount.abonsUp"] = {value: null, matchMode: FilterMatchMode.BETWEEN}
        }
        return this._filters
      },
      set(value) {
        console.log(value)
        this._filters = value
      }
    }
  },

  methods: {
    updateData() {
      this.clearFilters();
      this.$emit("update:data");
    },

    clearFilters() {
      this.$emit("filter:clear");
      this.filters.global.value = "";
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
      (<DataTable>this.$refs.dt).exportCSV();
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