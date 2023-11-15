<template>
  <div id="app" class="w-75" style="margin: auto;">

    <Toast />

    <div class="header">
      <h2 class="py-3">Технические данные - дом</h2>

      <!-- ДЕЙСТВИЯ -->
      <div class="d-flex">
        <button @click="goToTechDataURL" class="back-button me-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
            <path d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/>
          </svg>
          <span v-if="!isMobile" class="m-2">Назад</span>
        </button>

        <button @click="printData" class="print-button me-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
            <path d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2H5zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1z"/>
            <path d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2V7zm2.5 1a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
          </svg>
          <span v-if="!isMobile" class="m-2">Печать</span>
        </button>

      </div>
    </div>

    <!-- ОШИБКА ЗАГРУЗКИ -->
    <div v-if="errorStatus" class="alert alert-danger">
      Ошибка при загрузке данных.
      <br> {{errorMessage||''}}
      <br> Статус: {{errorStatus}}
    </div>

    <div v-if="detailData" id="tech-data-block" class="plate">

      <!-- ДАННЫЕ ДОМА -->
      <div class="py-3">

        <div class="d-flex align-items-center py-3">
          <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
            <circle cx="8" cy="8" r="8"/>
          </svg>
          <h4 class="m-0 me-3">Адрес: {{ getFullAddress(detailData) }}</h4>
        </div>

        <div class="ml-40 row align-items-center">
          <div class="col-auto">
            <BuildingIcon class="m-3" :type="detailData.building_type" width="64" height="64"/>
          </div>
          <div class="col-8">
            <template v-if="detailData.building_type === 'building'">
              Многоквартирный дом. Количество этажей: {{ detailData.floors }} /
              Количество подъездов: {{ detailData.total_entrances }}
            </template>
            <template v-else>
              Частный дом.
            </template>
          </div>
        </div>

      </div>


      <template v-for="(oltState, oltID) in detailData.oltStates">

        <div class="d-flex align-items-center py-3">
          <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
            <circle cx="8" cy="8" r="8"/>
          </svg>
          <h4 class="m-0 me-3">Задействованные подъезды: {{ oltState.entrances }}</h4>
        </div>

        <div class="ml-40">

          <!-- ОПИСАНИЕ 2 -->
          <div class="py-2 row align-items-center">
            <div class="col-5 fw-bold">Описание сплиттера 2го каскада</div>
            <div v-if="!editMode" class="col-auto">{{ oltState.description }}</div>
            <Textarea v-else class="w-100 my-1" v-model="oltState.description" rows="5"/>
          </div>


          <!-- ОБОРУДОВАНИЕ -->
          <div class="py-2 row align-items-center grey-back">
            <div class="col-4 fw-bold">OLT оборудование</div>
            <div class="col-auto">
              <span id="deviceName" class="badge fs-6" style="color: black">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                  <path d="M2 9a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zM2 2a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1z"/>
                </svg>
                {{oltState.statement.deviceName}}
              </span>
            </div>

          </div>

          <!-- ПОРТ -->
          <div class="py-2 row align-items-center ">
            <div class="col-4 fw-bold">Порт</div>
            <div class="d-flex col-auto fw-bold align-items-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M6 3.5a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-2a.5.5 0 0 0-1 0v2A1.5 1.5 0 0 0 6.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-9A1.5 1.5 0 0 0 14.5 2h-8A1.5 1.5 0 0 0 5 3.5v2a.5.5 0 0 0 1 0v-2z"/>
                <path fill-rule="evenodd" d="M11.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L10.293 7.5H1.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3z"/>
              </svg>
              <a :href="getOLTTechDataURL(oltState.statement)" class="me-2">{{ oltState.statement.devicePort }}</a>
              <button class="btn btn-outline-primary rounded-5 py-1">status</button>
            </div>
          </div>

          <!-- ВОЛОКНО -->
          <div class="py-2 row align-items-center grey-back">
            <div class="col-4 fw-bold">Волокно</div>
            <div class="col-auto">{{ oltState.statement.fiber }}</div>
          </div>

          <!-- ОПИСАНИЕ -->
          <div class="py-2 row align-items-center ">
            <div class="col-4 fw-bold">Описание сплиттера 1го каскада</div>
            <div class="col-auto">{{ oltState.statement.description }}</div>
          </div>

        </div>

        <!-- Абонентская линия -->
        <div class="py-3">

          <div class="d-flex">
            <h4 class="px-5">Абонентская линия</h4>
          </div>

          <div class="ml-40">
            <End3CollapsedView
                @getInfo="index => getEnd3DetailInfo(oltID, index)"
                @deleteInfo="index => deleteEnd3DetailInfo(oltID, index)"
                :customer-lines="oltState.customerLines" />
          </div>

        </div>

      </template>


    </div>

  </div>
</template>

<script>
import Dropdown from "primevue/dropdown/Dropdown.vue"
import InlineMessage from "primevue/inlinemessage/InlineMessage.vue"
import InputText from "primevue/inputtext/InputText.vue"
import Textarea from "primevue/textarea/Textarea.vue";
import Toast from "primevue/toast/Toast.vue"

import AddressGetCreate from "./components/AddressGetCreate.vue";
import BuildingIcon from "./components/BuildingIcon.vue"
import End3CollapsedView from "./components/End3CollapsedView.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue";
import api_request from "../api_request";
import formatAddress from "../helpers/address";
import printElementById from "../helpers/print";

export default {
  name: "Gpon_base.vue",
  components: {
    End3CollapsedView,
    AddressGetCreate,
    BuildingIcon,
    Dropdown,
    InlineMessage,
    InputText,
    TechCapabilityBadge,
    Textarea,
    Toast,
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
    // /gpon/api/tech-data/building/{device_name}?port={olt_port}
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
    },

  },

  methods: {

    getFullAddress(address) {
      return formatAddress(address)
    },

    goToTechDataURL() {
      window.location.href = "/gpon/tech-data"
    },

    getOLTTechDataURL(statement){
      return "/gpon/tech-data/" + statement.deviceName + "?port=" + statement.devicePort
    },

    getEnd3DetailInfo(oltID, end3Index) {
      const end3ID = this.detailData.oltStates[oltID].customerLines[end3Index].id
      api_request.get("/gpon/api/tech-data/end3/" + end3ID)
          .then(resp => this.detailData.oltStates[oltID].customerLines[end3Index].detailInfo = resp.data.capability)
          .catch(reason => {
            this.detailData.oltStates[oltID].customerLines[end3Index].errorStatus = reason.response.status
            this.detailData.oltStates[oltID].customerLines[end3Index].errorMessage = reason.response.data
          })
    },

    deleteEnd3DetailInfo(oltID, end3Index) {
      this.detailData.oltStates[oltID].customerLines[end3Index].detailInfo = null
    },

    printData() {printElementById('tech-data-block')},

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

  .header {
    justify-content: center;
    flex-wrap: wrap;
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