<template>
  <div>
    <DataTable ref="dt" :value="devices" v-model:filters="filters" :paginator-position="paginatorPosition"
               :loading="loading" class="font-mono !bg-transparent"
               paginator :rows="50" :rowsPerPageOptions="[10, 20, 50]"
               export-filename="devices" @valueChange="filterDevices"
               filterDisplay="menu" stripedRows size="small" removableSort
               dataKey="ip" :globalFilterFields="['name', 'ip']">

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
          <div>{{ data['ip'] }}</div>
        </template>
      </Column>

      <!--      НАЗВАНИЕ-->
      <Column field="name" header="Имя" :sortable="true">
        <template #body="{data}">
          <div class="group/device-name flex items-center gap-1">
            <a :href="'/device/'+data.name">
              <Button text icon="pi pi-box" :label="data.name"/>
            </a>
            <span class="opacity-0 group-hover/device-name:opacity-100" :class="{'!opacity-100': pinnedDevices.isPinned(data.name)}">
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

      <!--      МОДЕЛЬ-->
      <Column field="model" header="Модель" :sortable="true" :showFilterMatchModes="false">
        <template #body="{data}">
          <div v-if="data.model" class="group/model-filter flex items-center gap-2">
            <div class="">{{ data.model }}</div>
            <Button v-if="filters.model.value != data.model" @click="filters.model.value = data.model"
                    icon="pi pi-filter" size="small"
                    class="opacity-0 group-hover/model-filter:opacity-100" outlined/>
            <Button v-else @click="filters.model.value = null" icon="pi pi-filter-slash" size="small"
                    class="opacity-0 group-hover/model-filter:opacity-100" outlined/>
          </div>
        </template>
        <template #filtericon>
          <i :class="filters.model.value?'pi pi-filter-fill text-indigo-500':'pi pi-filter'"/>
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <Select v-model="filterModel.value" :showClear="true"
                  optionGroupLabel="label" optionGroupChildren="items" @change="filterCallback()" :options="models"
                  placeholder="Выберите модель" class="md:w-80 w-full relative">
            <template #optiongroup="slotProps">
              <div class="sticky top-0 flex items-center">
                <div class="">{{ slotProps.option.label }}</div>
              </div>
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
    this.filters.global.value = this.globalSearch;
  },

  data() {
    return {
      model: null,
      paginatorPosition: undefined as 'top' | 'bottom' | 'both' | undefined,
      _filters: {
        global: {value: "", matchMode: FilterMatchMode.CONTAINS},
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