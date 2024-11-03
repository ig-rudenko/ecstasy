<template>
  <Header/>

  <div class="p-6">
    <div class="container mx-auto row py-3">
      <div class="flex flex-wrap justify-between pb-5">
        <div>
          <div class="text-3xl font-bold">Description search</div>
          <div class="py-3">Поиск конкретной строки в описании порта и его комментариев на
            всех собранных заранее интерфейсах у каждого оборудования</div>
        </div>

        <img class="h-[100px]" src="/img/search-description-2.svg" alt="search-description-image">
      </div>
      <SearchInput @submit_input="searchDescription" @update:modelValue="(v: string) => pattern = v"
                   :active-mode="true"
                   placeholder="Введите строку для поиска"/>
    </div>

    <div v-show="interfaces.length" class="py-4">

      <!--Нашли по паттерну-->
      <div v-if="interfaces.length && !waitResult">
        <div>
          <h4 class="text-center py-2">Поиск по паттерну: "<span class="font-mono">{{ lastPattern }}</span>"</h4>
          <h6 class="py-2 ml-5 font-mono">Найдено: {{ interfaces.length }}</h6>
        </div>

        <DataTable ref="descriptionSearchTable" :value="interfaces"
                   :rows="rows" :paginator="interfaces.length > rows" paginator-position="both"
                   filterDisplay="row" v-model:filters="filters" removableSort>

          <template #paginatorend>
            <Button severity="success" @click="exportCSV" icon="pi pi-file-excel" fluid outlined
                    v-tooltip.left="'Экспорт текущей таблицы по фильтру, но без сортировки'" label="export csv" />
          </template>

          <Column field="device" header="Оборудование" :sortable="true" class="font-mono">
            <template #body="{data}">
              <router-link :to="'/device/' + data.device">
                <Button text icon="pi pi-box" class="text-nowrap" :label="data['device']" />
              </router-link>
            </template>
            <template #filter="{ filterModel, filterCallback }">
              <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Поиск по имени" />
            </template>
          </Column>

          <Column field="interface.name" filter-field="interface.name" header="Порт" :sortable="true" class="font-mono">
            <template #filter="{ filterModel, filterCallback }">
              <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Поиск порта" />
            </template>
          </Column>

          <Column field="interface.status" header="Статус" :sortable="true" class="font-mono">
            <template #body="{data}">
              <div v-tooltip="'Время опроса: ' + data.interface.savedTime.toString()" class="text-nowrap p-2 flex items-center justify-center rounded"
                   :style="statusStyle(data.interface.status)">
                <span class="me-1">{{ data.interface.status }}</span>
                <i class="pi pi-clock"/>
              </div>
            </template>
            <template #filter="{ filterModel, filterCallback }">
              <Select v-model="filterModel.value" @change="filterCallback()" placeholder="Выберите статус" :options="['up','down','admin down', 'noPresent']" />
            </template>
          </Column>

          <Column field="interface.description" header="Описание" :sortable="true" class="font-mono">
            <template #body="{data}">
              <div v-html="markDescription(data.interface.description)"></div>
            </template>
            <template #filter="{ filterModel, filterCallback }">
              <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Поиск" />
            </template>
          </Column>

          <Column field="comments.0.text" header="Комментарии" :sortable="true" class="font-mono">
            <template #body="{data}">
              <Comment :interface="getInterface(data)" :markedText="lastPattern" />
            </template>
          </Column>

          <Column field="interface.vlans" header="VLAN" :sortable="true" class="font-mono">
            <template #body="{data}">
              <div @click="toggleVlansList($event, data.interface)" style="cursor: pointer">
                {{ truncateVlans(data.interface.vlans) }}
              </div>
            </template>
            <template #filter="{ filterModel, filterCallback }">
              <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Поиск VLAN" />
            </template>
          </Column>

        </DataTable>

      </div>

      <!--Не нашли-->
      <div v-else-if="!interfaces.length" class="py-4">
        <h4 style="text-align: center">
          Поиск по паттерну: "<span style="background: #fff6d5">{{ pattern }}</span>" не дал результатов
        </h4>
        <br>
        <div class="container text-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" fill="currentColor" class="bi bi-emoji-frown" viewBox="0 0 16 16">
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
            <path d="M4.285 12.433a.5.5 0 0 0 .683-.183A3.498 3.498 0 0 1 8 10.5c1.295 0 2.426.703 3.032 1.75a.5.5 0 0 0 .866-.5A4.498 4.498 0 0 0 8 9.5a4.5 4.5 0 0 0-3.898 2.25.5.5 0 0 0 .183.683zM7 6.5C7 7.328 6.552 8 6 8s-1-.672-1-1.5S5.448 5 6 5s1 .672 1 1.5zm4 0c0 .828-.448 1.5-1 1.5s-1-.672-1-1.5S9.448 5 10 5s1 .672 1 1.5z"/>
          </svg>
        </div>
      </div>

    </div>

    <!--Выполняется поиск-->
    <div v-show="waitResult" class="text-center">
      <div class="text-2xl py-2">Поиск по паттерну: "<span class="font-mono">{{ pattern }}</span>"</div>
      <img class="mx-auto h-[200px]" src="/img/load_desc.gif" alt="load-desc">
    </div>
  </div>

  <!--  VLANS FULL LIST-->
  <Popover ref="vlansList">
    <div class="text-sm text-muted-color pb-4"><i class="pi pi-clock me-2 text-sm" />{{ selectedVlansTime }}</div>
    <div>{{ selectedVlans }}</div>
  </Popover>

  <Footer/>

</template>

<script lang="ts">
import {defineComponent} from "vue";

import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import Comment from "@/components/Comment.vue";
import SearchInput from "@/components/SearchInput.vue";
import {DeviceInterface, findInterfacesByDescription, InterfaceDescriptionMatchResult} from "@/services/interfaces";
import {FilterMatchMode} from "@primevue/core/api";
import {markText} from "@/formats.ts";

export default defineComponent({
  components: {Footer, Header, Comment, SearchInput},

  data() {
    return {
      interfaces: [] as InterfaceDescriptionMatchResult[],
      pattern: "" as string,
      lastPattern: "" as string,
      waitResult: false as boolean,
      rows: 25, // количество строк в таблице

      selectedVlans: "",
      selectedVlansTime: "",
      filters: {
        device: { value: null, matchMode: FilterMatchMode.CONTAINS },
        'interface.name': { value: null, matchMode: FilterMatchMode.CONTAINS },
        'interface.status': { value: null, matchMode: FilterMatchMode.EQUALS },
        'interface.description': { value: null, matchMode: FilterMatchMode.CONTAINS },
        'interface.vlans': { value: null, matchMode: FilterMatchMode.CONTAINS },
      },
    }
  },
  methods: {

    getInterface(data: InterfaceDescriptionMatchResult): DeviceInterface {
      return {
        name: data.interface.name,
        description: data.interface.description,
        status: data.interface.status,
        vlans: [],
        comments: data.comments,
      }
    },

    searchDescription() {
      if (this.pattern.length < 2) return;
      this.waitResult = true

      findInterfacesByDescription(this.pattern)
          .then(
            data => {
              this.interfaces = data
              this.lastPattern = this.pattern
              this.waitResult = false
            },
            () => this.waitResult = false
          )
          .catch(() => this.waitResult = false)
    },

    markDescription(desc: string): string {
      return markText(desc, this.lastPattern)
    },

    statusStyle(status: string): any {
      status = status.toLowerCase()
      let style: any = {
        color: 'black',
        width: '120px',
      }
      if (status === "admin down") {
        style['background-color'] = "#ffb4bb";
      } else if (status === "notpresent") {
        style['background-color'] = "#c1c1c1"
      } else if (status === "dormant") {
        style['background-color'] = "#ffe389"
      } else if (status !== "down") {
        style['background-color'] = "#22e58b"
      }

      style.color = style['background-color']? "black" : ""

      return style
    },

    truncateVlans(vlans: string): string {
      if (vlans.length > 17) {
        return vlans.slice(0, 15) + "..."
      }
      return vlans
    },

    toggleVlansList(event: Event, intf: { vlans: string, vlansSavedTime: string }) {
      this.selectedVlans = intf.vlans;
      this.selectedVlansTime = intf.vlansSavedTime;

      // @ts-ignore
      this.$refs.vlansList.toggle(event);
    },

    exportCSV() {
      // @ts-ignore
      this.$refs.descriptionSearchTable.exportCSV();
    },

  },


});

</script>
