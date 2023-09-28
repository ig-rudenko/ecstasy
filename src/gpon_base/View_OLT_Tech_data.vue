<template>
  <div id="app" class="w-75" style="margin: auto;">

    <div class="header">
      <h2 class="py-3">Технические данные - просмотр</h2>

      <div class="d-flex">
        <button @click="goToTechDataURL" class="back-button me-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
            <path d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/>
          </svg>
          <span class="me-2">Назад</span>
        </button>

        <button @click="printData" class="print-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
            <path d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2H5zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1z"/>
            <path d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2V7zm2.5 1a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
          </svg>
          Печать
        </button>
      </div>
    </div>

    <div v-if="errorStatus" class="alert alert-danger">
      Ошибка при загрузке данных.
      <br> {{errorMessage||''}}
      <br> Статус: {{errorStatus}}
    </div>

    <div v-if="detailData" id="tech-data-block" class="plate">

      <!-- Станционные данные -->
      <div class="py-3">

        <div class="d-flex">
          <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
            <circle cx="8" cy="8" r="8"/>
          </svg>
          <h4>Станционные данные</h4>
        </div>

        <div class="ml-40">

          <div class="py-2 row align-items-center">
            <div class="col-4 fw-bold">OLT оборудование</div>
            <div class="col-auto">
              <span id="deviceName" class="badge fs-6" style="color: black">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                  <path d="M2 9a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zM2 2a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1z"/>
                </svg>
                {{detailData.deviceName}}
              </span>
            </div>
          </div>

          <div class="py-2 row align-items-center grey-back">
            <div class="col-4 fw-bold">Порт</div>
            <div class="col-auto fw-bold">
              {{ detailData.devicePort }}
              <button class="btn btn-outline-primary rounded-5 py-1">
                status
              </button>
            </div>
          </div>

          <div class="py-2 row align-items-center">
            <div class="col-4 fw-bold">Волокно</div>
            <div class="col-auto">{{ detailData.fiber }}</div>
          </div>

          <div class="py-2 row align-items-center grey-back">
            <div class="col-4 fw-bold">Описание сплиттера 1го каскада</div>
            <div class="col-auto">{{ detailData.description }}</div>
          </div>

        </div>

      </div>


      <template v-for="building in detailData.structures">

        <!-- АДРЕС -->
        <div class="py-3">

          <div class="d-flex">
            <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
              <circle cx="8" cy="8" r="8"/>
            </svg>
            <h4>Адрес: {{ getFullAddress(building.address) }}</h4>
          </div>

          <div class="ml-40">

            <div class="row align-items-center">
              <div class="col-auto">
                <BuildingIcon class="m-3" :type="building.address.building_type" width="64" height="64"/>
              </div>
              <div class="col-8">
                <template v-if="building.address.building_type === 'building'">
                  Многоквартирный дом. Количество этажей: {{ building.address.floors }} /
                  Количество подъездов: {{ building.address.total_entrances }}
                </template>
                <template v-else>
                  Частный дом.
                </template>
              </div>
            </div>
            <div class="py-2 row align-items-center grey-back">
              <div class="col-5 fw-bold">Задействованные подъезды в доме для данного OLT порта</div>
              <div class="col-auto">{{ building.entrances }}</div>
            </div>
            <div class="py-2 row align-items-center">
              <div class="col-5 fw-bold">Описание сплиттера 2го каскада</div>
              <div class="col-auto">{{ building.description }}</div>
            </div>

          </div>

        </div>

        <!-- Абонентская линия -->
        <div class="py-3">

          <div class="d-flex">
            <h4 class="px-5">Абонентская линия</h4>
          </div>

          <div class="ml-40">

            <div v-for="(line, index) in building.customerLines"
                 :class="getCustomerLineClasses(index)">

              <div class="col-md-2 fw-bold">{{ customerLineTypeName(line.type) }} {{ index + 1 }}</div>
              <div class="col-auto">
                  {{ getFullAddress(line.address) }}
                  <br>
                  Локация: {{ line.location }}.
              </div>
              <div class="col-auto">{{ customerLineNumbers(line) }}</div>
              <div class="col-auto">
                  <button class="btn btn-outline-primary rounded-5 py-1">
                    detail
                  </button>
              </div>
            </div>

          </div>

        </div>
      </template>


    </div>

  </div>
</template>

<script>
import BuildingIcon from "./components/BuildingIcon.vue"
import Table from "./components/Table.vue";

import formatAddress from "../helpers/address";
import api_request from "../api_request";

export default {
  name: "Gpon_base.vue",
  components: {
    BuildingIcon,
    Table,
  },
  data() {
    return {
      detailData: null,
      errorStatus: null,
      errorMessage: null,
      windowWidth: window.innerWidth,
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
    window.addEventListener('resize', () => {
      this.windowWidth = window.innerWidth
    })
  },

  computed: {
    isMobile() {
      return this.windowWidth <= 768
    }
  },

  methods: {

    getCustomerLineClasses(index){
      let class_list = ['py-2', 'row', 'align-items-center']
      if (index % 2 === 0) class_list.push('grey-back');
      return class_list
    },

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

    goToTechDataURL() {
      window.location.href = "/gpon/tech-data"
    }
  }
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.grey-back {
  background-color: #ebebeb;
}

.print-button {
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #6D5BD0;
  border: 1px #6D5BD0 solid;
}

.print-button:hover {
  box-shadow: 0 0 3px #6D5BD0;
}

.back-button {
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #4a4a4a;
  border: 1px #4a4a4a solid;
}

.back-button:hover {
  box-shadow: 0 0 3px #4a4a4a;
}

.plate {
  padding: 40px;
  border-radius: 14px;
  border: 1px solid #A3A3A3;
}

.ml-40 {
  margin-left: 40px;
}

@media (max-width: 835px) {
  .container {
    margin-left: 0!important;
    margin-right: 0!important;
    max-width: 100%!important;
  }

  .w-75, .col-5 {
    width: 100% !important;
  }

  .header {
    padding: 0 40px;
  }

  .plate {
    border: none;
  }

  .ml-40 {
    margin-left: 0;
  }

  .p-5 {
    padding-left: 0 !important;
    padding-right: 0 !important;
  }
}

</style>