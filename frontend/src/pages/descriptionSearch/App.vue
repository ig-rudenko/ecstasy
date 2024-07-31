<template id="app">

  <div class="row py-3">
      <div class="col-md-8">
          <h4 class="fw-bold">Description search</h4>
          Поиск конкретной строки в описании порта и его комментариев на всех собранных заранее интерфейсах у каждого оборудования
      </div>

      <div class="col-md-4" style="text-align: right">
          <img height="100px" src="/static/img/search-description-2.svg" alt="search-description-image">
      </div>
  </div>

  <SearchInput
      @submit_input="searchDescription"
      :update-search="updateSearch"
      placeholder="Введите строку для поиска">
  </SearchInput>


  <div v-show="interfaces.length" class="py-4">

    <!--Нашли по паттерну-->
    <div v-if="interfaces.length && !waitResult">
        <div>
            <h4 class="text-center py-2">Поиск по паттерну: "{{ lastPattern }}"</h4>
            <h6 class="py-2" style="margin-left: 20px;">Найдено: {{ interfaces.length }}</h6>
        </div>

        <Pagination :p-object="paginator"></Pagination>

        <div class="table-responsive-lg">
        <table class="table">
          <thead>
            <tr>
              <th scope="col">Оборудование</th>
              <th scope="col" style="padding-left: 40px">Порт</th>
              <th scope="col">Был статус</th>
              <th scope="col" style="text-align: left">Описание</th>
              <th scope="col">Комментарии</th>
              <th scope="col">VLANS</th>
            </tr>
          </thead>
          <tbody style="vertical-align: middle">

            <tr v-for="intf in paginatedInterfaces">

    <!--      DEVICE NAME-->
              <td>
                  <span class="device" title="Перейти к оборудованию">
                        <svg style="vertical-align: middle; margin-right: 5px;"
                             xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box-arrow-in-right" viewBox="0 0 16 16">
                          <path fill-rule="evenodd" d="M6 3.5a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-2a.5.5 0 0 0-1 0v2A1.5 1.5 0 0 0 6.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-9A1.5 1.5 0 0 0 14.5 2h-8A1.5 1.5 0 0 0 5 3.5v2a.5.5 0 0 0 1 0v-2z"/>
                          <path fill-rule="evenodd" d="M11.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L10.293 7.5H1.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3z"/>
                        </svg>
                      <a class="text-decoration-none" target="_blank" :href="'/device/'+intf.device">
                          {{ intf.device }}
                      </a>
                  </span>
              </td>

              <!--INTERFACE-->
              <td class="nowrap">{{ intf.interface.name }}</td>

              <!--STATUS-->
              <td v-tooltip="'Время опроса: ' + intf.interface.savedTime.toString()" class="nowrap"
                  :style="statusStyle(intf.interface.status)">
                <span class="me-1">{{ intf.interface.status }}</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71z"></path>
                  <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0"></path>
                </svg>
              </td>

              <!--DESCRIPTION-->
              <td style="text-align: left" v-html="markDescription(intf.interface.description)"></td>

              <!--COMMENT-->
              <td>
                <Comment v-if="intf.comments.length" :interface="getInterface(intf)"></Comment>
              </td>

              <!--VLANS LIST-->
              <td>
                <div @click="toggleVlansList($event, intf.interface)" style="cursor: pointer">
                  {{ truncateVlans(intf.interface.vlans) }}
                </div>
              </td>

            </tr>
          </tbody>
        </table>
        </div>

        <Pagination :p-object="paginator"></Pagination>

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
      <h4 class="text-center py-2">Поиск по паттерну: "{{ pattern }}"</h4>
      <img height="200" src="/static/img/load_desc.gif" alt="load-desc">
  </div>

  <ScrollTop/>

  <!--  VLANS FULL LIST-->
  <OverlayPanel ref="vlansList">
    <div class="align-items-center d-flex pb-2">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="me-2"
           viewBox="0 0 16 16">
        <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71z"></path>
        <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0"></path>
      </svg>
      <span>{{ selectedVlansTime }}</span>
    </div>
    <div>{{ selectedVlans }}</div>
  </OverlayPanel>

</template>

<script lang="ts">
import {defineComponent} from "vue";
import ScrollTop from "primevue/scrolltop";
import OverlayPanel from 'primevue/overlaypanel';

import Comment from "../../components/Comment.vue";
import Pagination from "../../components/Pagination.vue";
import SearchInput from "../../components/SearchInput.vue";
import api_request from "../../api_request";
import {InterfaceMatchResult, MatchResult} from "./type";
import Interface from "../../types/interfaces";
import Paginator from "../../types/paginator";

export default defineComponent({
  components: {Comment, Pagination, SearchInput, ScrollTop, OverlayPanel},

  data() {
    return {
      interfaces: [] as InterfaceMatchResult[],
      pattern: "" as string,
      lastPattern: "" as string,
      waitResult: false as boolean,
      paginator: new Paginator(),

      selectedVlans: "",
      selectedVlansTime: "",
    }
  },
  methods: {
    searchDescription() {
      if (this.pattern.length < 2) return;
      this.waitResult = true

      api_request.get<MatchResult>("/tools/api/find-by-desc?pattern=" + this.pattern).then(
          value => {
            this.interfaces = value.data.interfaces
            this.lastPattern = this.pattern
            this.paginator = new Paginator(this.interfaces.length)
            this.waitResult = false
          },
          () => this.waitResult = false
      )
    },

    getInterface(match: InterfaceMatchResult): Interface {
      return new Interface(match.interface.name, "", match.interface.description, [], match.comments)
    },

    /** Обновляем паттерн поиска */
    updateSearch(event: Event) { this.pattern = (<HTMLInputElement>event.target).value },

    /** Выделяем тегом <mark></mark> часть в описании, которая совпадает с паттерном поиска */
    markDescription(desc: string): string {
      return desc.replace(new RegExp(this.lastPattern, 'ig'), s => '<mark>'+s+'</mark>')
    },

    statusStyle(status: string): any {
      status = status.toLowerCase()
      const color = () => {
        if (status === "admin down") return "#ffb4bb"
        if (status === "notpresent") return "#c1c1c1"
        if (status === "dormant") return "#ffe389"
        if (status !== "down") return "#22e58b"
      }
      return {
        'background-color': color(),
        width: '100px',
      }
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
      (<OverlayPanel>this.$refs.vlansList).toggle(event);
    }

  },
  computed: {
    paginatedInterfaces(): InterfaceMatchResult[] {
      if (!this.interfaces) return [];
      // Обрезаем по размеру страницы
      return this.interfaces.slice(
          this.paginator.page * this.paginator.rowsPerPage,
          (this.paginator.page + 1) * this.paginator.rowsPerPage
      )
    }
  },

});

</script>

<style>
mark {
    padding: 0;
}
tr {
    text-align: center;
}
a {
    cursor: pointer;
}
.device:hover svg {
    visibility: visible;
    color: #558af1;
}
.device:hover a {
    color: #558af1;
}

.device:not(:hover) svg {
    visibility: hidden;
    color: rgb(33,37,41);
}
.device:not(:hover) a {
    color: rgb(33,37,41);
}
tr:hover {
    background: #e8efff;
}
</style>