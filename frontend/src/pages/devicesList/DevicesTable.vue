<template>
<table class="table head-padding">
  <thead>
    <tr>

      <th scope="col" class="text-center">IP</th>

      <th scope="col" style="padding-left: 2.5rem;">Имя</th>

      <th scope="col" class="noselect" style="padding-left: 0;">

          <span class="badge bg-primary" data-bs-toggle="dropdown" role="button" style="font-size: 15px;">
              {{ "Вендор: " + currentVendor }}
          </span>
          <ul class="dropdown-menu" style="cursor: pointer">
                <li class="dropdown-item" @click="setVendor('')">Все вендоры</li>
                <li class="dropdown-item"
                 v-for="vendor in vendors"
                 @click="setVendor(vendor)">{{ vendor }}</li>
          </ul>
      </th>

      <th scope="col">Модель</th>

      <th scope="col"  class="noselect" style="padding-left: 0;">
          <span class="badge bg-primary" data-bs-toggle="dropdown" role="button" style="font-size: 15px;">
              {{ "Группа: " + currentGroup }}
          </span>
          <ul class="dropdown-menu" style="cursor: pointer">
                <li class="dropdown-item" @click="setGroup('')">Все группы</li>
                <li class="dropdown-item"
                 v-for="group in groups"
                 @click="setGroup(group)">{{ group }}</li>
          </ul>
      </th>
    </tr>
  </thead>


  <tbody style="vertical-align: middle;">

      <template v-for="dev in devices">
        <tr :style="dev.interfacesCount?{'border-bottom': 'hidden'}:{}">
    <!--    IP-->
            <td class="text-center table-padding">{{ dev.ip }}</td>

    <!--    NAME-->
            <td>
              <a class="text-decoration-none nowrap btn btn-outline-primary" style="border: none;"
                 :href="'/device/' + dev.name">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-right" viewBox="0 0 16 16">
                  <path d="M6 12.796V3.204L11.481 8 6 12.796zm.659.753 5.48-4.796a1 1 0 0 0 0-1.506L6.66 2.451C6.011 1.885 5 2.345 5 3.204v9.592a1 1 0 0 0 1.659.753z"/>
                </svg>
                {{ dev.name }}
              </a>
            </td>

    <!--    VENDOR-->
            <td>
              <button v-if="dev.vendor" @click="setVendor(dev.vendor)" class="btn position-relative">
                {{ dev.vendor }}
                <span :style="{'background-color': stringToColour(dev.vendor)}"
                      class="position-absolute top-50 start-0 translate-middle p-2 border border-light rounded-circle">
                </span>
              </button>
            </td>

            <td class="table-padding">{{ dev.model }}</td>

            <td class="table-padding">{{ dev.group }}</td>
          </tr>

          <tr v-if="dev.interfacesCount && dev.interfacesCount.abons">

            <td class="table-padding" colspan="5" style="padding-bottom: 1.5rem;">
            <div class="col-5">
              <div class="progress">

<!--                Абонентские порты UP С ОПИСАНИЕМ -->
                <div v-if="dev.interfacesCount.abonsUpWithDesc"
                     class="progress-bar bg-success" role="progressbar"
                     :style="{width: dev.interfacesCount.abonsUpWithDesc / dev.interfacesCount.abons * 100 + '%'}"
                     :aria-valuemax="dev.interfacesCount.abons">
                  {{ dev.interfacesCount.abonsUpWithDesc }}
                </div>

<!--                Абонентские порты UP Без описания -->
                <div class="progress-bar" role="progressbar" style="background-color: #74bf9c"
                     v-if="dev.interfacesCount.abonsUpNoDesc"
                     :style="{width: dev.interfacesCount.abonsUpNoDesc / dev.interfacesCount.abons * 100 + '%'}"
                     :aria-valuemax="dev.interfacesCount.abons">
                  {{ dev.interfacesCount.abonsUpNoDesc }}
                </div>

<!--                Абонентские порты DOWN С ОПИСАНИЕМ -->
                <div class="progress-bar text-dark" role="progressbar" style="background-color: #ffbdbd"
                     v-if="dev.interfacesCount.abonsDownWithDesc"
                     :style="{width: dev.interfacesCount.abonsDownWithDesc / dev.interfacesCount.abons * 100 + '%'}"
                     :aria-valuemax="dev.interfacesCount.abons">
                  {{ dev.interfacesCount.abonsDownWithDesc }}
                </div>

<!--                Абонентские порты Остальные-->
                <div class="progress-bar text-dark" role="progressbar" style="background-color: #cfcfcf"
                     v-if="dev.interfacesCount.abonsDownNoDesc"
                     :style="{width: dev.interfacesCount.abonsDownNoDesc / dev.interfacesCount.abons * 100 + '%'}"
                     :aria-valuemax="dev.interfacesCount.abons">
                  {{ dev.interfacesCount.abonsDownNoDesc }}
                </div>

              </div>
            </div>
            </td>
          </tr>

      </template>

  </tbody>
</table>
</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";

import {Device} from "./devices";

export default defineComponent({
  props: {
      devices: {
        required: true,
        type: [] as PropType<Array<Device>>
      },
      setVendor: { required: true, type: Function as PropType<(vendor: string) => void> },
      setGroup: { required: true, type: Function as PropType<(group: string) => void> },
      currentVendor: { required: true, type: String },
      currentGroup: { required: true, type: String },
      vendors: { required: true, type: [] as PropType<Array<string>> },
      groups: { required:true, type: [] as PropType<Array<string>> }
  },

  methods: {
    stringToColour(str: string): string {
      if (!str) return '';
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
         hash = str.toLowerCase().charCodeAt(i) + ((hash << 5) - hash);
      }
      let c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
      return "#" + "00000".substring(0, 6 - c.length) + c;
    }
  }
})
</script>

<style scoped>
.head-padding th {
  padding: 0.875rem 1.25rem;
}
</style>