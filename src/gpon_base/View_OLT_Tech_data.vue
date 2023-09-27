<template>
  <div id="app" class="container w-75">

    <div class="header">
      <h2 class="py-3">Технические данные - просмотр</h2>

      <button @click="printData" class="print-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2"
             viewBox="0 0 16 16">
          <path
              d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2H5zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1z"/>
          <path
              d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2V7zm2.5 1a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
        </svg>
        Печать
      </button>
    </div>

    <div v-if="errorStatus" class="alert alert-danger">
      Ошибка при загрузке данных.
      <br> {{errorMessage||''}}
      <br> Статус: {{errorStatus}}
    </div>

    <div v-if="detailData" id="tech-data-block" class="plate">

      <div class="py-3">

        <div class="d-flex">
          <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
            <circle cx="8" cy="8" r="8"/>
          </svg>
          <h4>Станционные данные</h4>
        </div>

        <div style="margin-left: 40px;">
          <table class="table table-striped" style="width: max-content; margin: 10px 0 0 0">
            <tbody>
            <tr>
              <th scope="row">OLT оборудование</th>
              <td>{{ detailData.deviceName }}</td>
            </tr>
            <tr>
              <th scope="row">Порт</th>
              <td>
                {{ detailData.devicePort }}
                <button class="btn btn-outline-primary rounded-5 py-1">
                  status
                </button>
              </td>
            </tr>
            <tr>
              <th scope="row">Волокно</th>
              <td>{{ detailData.fiber }}</td>
            </tr>
            <tr>
              <th scope="row">Описание сплиттера 1го каскада</th>
            </tr>
            </tbody>
          </table>
          <div style="padding: 10px">{{ detailData.description }}</div>
        </div>

      </div>

      <template v-for="building in detailData.structures">
        <div class="py-3">

          <div class="d-flex">
            <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
              <circle cx="8" cy="8" r="8"/>
            </svg>
            <h4>Адрес: {{ getFullAddress(building.address) }}</h4>
          </div>
          <h6 class="px-5 p-2">
            <template v-if="building.address.building_type === 'building'">
              Многоквартирный дом. Количество этажей: {{ building.address.floors }} /
              Количество подъездов: {{ building.address.total_entrances }}
            </template>
            <template v-else>
              Частный дом.
            </template>
          </h6>

          <div style="margin-left: 40px;">
            <table class="table table-striped" style="width: max-content; margin: 10px 0 0 0">
              <tbody>
              <tr>
                <th scope="row">Задействованные подъезды в доме для данного OLT порта</th>
                <td>{{ building.entrances }}</td>
              </tr>
              <tr>
                <th scope="row">Описание сплиттера 2го каскада</th>
              </tr>
              </tbody>
            </table>
            <div style="padding: 10px">{{ building.description }}</div>
          </div>

        </div>

        <div class="py-3">

          <div class="d-flex">
            <h4 class="px-5">Абонентская линия</h4>
          </div>

          <div style="margin-left: 40px;">
            <table class="table table-striped" style="width: max-content; margin: 10px 0 0 0">
              <tbody>
              <tr v-for="(line, index) in building.customerLines">
                <th scope="row">{{ customerLineTypeName(line.type) }} {{ index + 1 }}</th>
                <td>
                  {{ getFullAddress(line.address) }}
                  <br>
                  Локация: {{ line.location }}.
                </td>
                <td>{{ customerLineNumbers(line) }}</td>
                <td>
                  <button class="btn btn-outline-primary rounded-5 py-1">
                    detail
                  </button>
                </td>
              </tr>
              </tbody>
            </table>
          </div>

        </div>
      </template>


    </div>

  </div>
</template>

<script>
import Table from "./components/Table.vue";

import formatAddress from "../helpers/address";
import api_request from "../api_request";

export default {
  name: "Gpon_base.vue",
  components: {
    Table,
  },
  data() {
    return {
      detailData: null,
      errorStatus: null,
      errorMessage: null,
    }
  },
  mounted() {
    let url = window.location.href
    // /gpon/api/tech-data/{device_name}?port={olt_port}
    api_request.get("/gpon/api/" + url.match(/tech-data\S+/)[0])
        .then(resp => this.detailData = resp.data)
        .catch(reason => {
          this.errorStatus = reason.response.status
          this.errorMessage = reason.response.data
        })
  },
  methods: {

    getFullAddress(address) {
      return formatAddress(address)
    },

    customerLineTypeName(type) {
      if (type === "splitter") {
        return "Сплиттер"
      } else if (type === "rizer") {
        return "Райзер"
      } else {
        return type
      }
    },

    customerLineNumbers(line) {
      if (line.type === "splitter") {
        return `${line.capacity} портов`
      } else if (line.type === "rizer") {
        return `${line.capacity} волокон`
      } else {
        return line
      }
    },

    printData() {
      let prtHtml = document.getElementById('tech-data-block').innerHTML
      // remove all buttons
      prtHtml = prtHtml.replace(/<button.*?>.*?<\/button>/g, "")

      // Get all stylesheets HTML
      let stylesHtml = '';
      for (const node of [...document.querySelectorAll('link[rel="stylesheet"], style')]) {
        stylesHtml += node.outerHTML;
      }
      // Open the print window
      const WinPrint = window.open('', '', 'width=1200,height=900,toolbar=0,scrollbars=0,status=0');
      WinPrint.document.write(`<!DOCTYPE html>
      <html lang="ru">
        <head>
          ${stylesHtml}
          <title></title>
        </head>
        <body>
          ${prtHtml}
        </body>
      </html>`);
      WinPrint.document.close();
      WinPrint.focus();
      WinPrint.print();
    },
  }
}
</script>

<style scoped>
.header {
  text-align: right;
  display: flex;
  justify-content: space-between;
  align-items: center;
}


.print-button {
  margin: 15px;
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #6D5BD0;
  border: 1px #6D5BD0 solid;
}

.print-button:hover {
  box-shadow: 0 0 3px #6D5BD0;
}

.plate {
  padding: 40px;
  border-radius: 14px;
  border: 1px solid #A3A3A3;
}
</style>