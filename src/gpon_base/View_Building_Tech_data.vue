<template>
  <div id="app" class="w-75" style="margin: auto;">

    <Toast />

    <ViewPrintEditButtons
        @print="printData"
        @changeMode="mode => editMode = mode"
        exitButtonURL="/gpon/tech-data"
        :has-permission-to-edit="hasAnyPermissionToUpdate"
        :is-mobile="isMobile"
    />

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
          <h4 class="m-0 me-3">Адрес: {{ getFullAddress(detailDataAddress) }}</h4>
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
                @deletedEnd3="(end3, end3Index) => deleteEnd3FromList(oltID, end3Index)"
                @createNewEnd3="newEnd3List => createNewEnd3(oltID, newEnd3List)"
                :customer-lines="oltState.customerLines"
                :user-permissions="userPermissions"
                :edit-mode="editMode"

                :device-name="oltState.statement.deviceName"
                :device-port="oltState.statement.devicePort"
                :building-address="detailDataAddress"
            />
          </div>

        </div>

      </template>


    </div>

  </div>

  <ScrollTop />
</template>

<script>
import Dropdown from "primevue/dropdown/Dropdown.vue"
import InlineMessage from "primevue/inlinemessage/InlineMessage.vue"
import InputText from "primevue/inputtext/InputText.vue"
import ScrollTop from "primevue/scrolltop";
import Textarea from "primevue/textarea/Textarea.vue";
import Toast from "primevue/toast/Toast.vue"

import AddressGetCreate from "./components/AddressGetCreate.vue";
import BuildingIcon from "./components/BuildingIcon.vue"
import End3CollapsedView from "./components/End3CollapsedView.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue";
import ViewPrintEditButtons from "./components/ViewPrintEditButtons.vue";
import api_request from "../api_request";
import formatAddress from "../helpers/address";
import printElementById from "../helpers/print";

export default {
  name: "Gpon_base.vue",
  components: {
    ViewPrintEditButtons,
    End3CollapsedView,
    AddressGetCreate,
    BuildingIcon,
    Dropdown,
    InlineMessage,
    InputText,
    ScrollTop,
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
      userPermissions: [],
      editMode: false,
    }
  },
  mounted() {
    api_request.get("/gpon/api/permissions").then(resp => {this.userPermissions = resp.data})
    this.getTechData()
    window.addEventListener('resize', () => {
      this.windowWidth = window.innerWidth
    })
  },

  computed: {
    isMobile() {
      return this.windowWidth <= 768
    },

    detailDataAddress() {
      return {
        id: this.detailData.id,
        region: this.detailData.region,
        settlement: this.detailData.settlement,
        planStructure: this.detailData.planStructure,
        street: this.detailData.street,
        house: this.detailData.house,
        block: this.detailData.block,
        building_type: this.detailData.building_type,
        floors: this.detailData.floors,
        total_entrances: this.detailData.total_entrances,
      }
    },

    hasPermissionToUpdateOLTState(){
      return this.userPermissions.includes("gpon.change_oltstate")
    },

    hasPermissionToUpdateHouseOLTState(){
      return this.userPermissions.includes("gpon.change_houseoltstate")
    },

    hasPermissionToUpdateHouseB(){
      return this.userPermissions.includes("gpon.change_houseb")
    },

    hasAnyPermissionToUpdate(){
      return this.hasPermissionToUpdateOLTState || this.hasPermissionToUpdateHouseOLTState || this.hasPermissionToUpdateHouseB
    },

  },

  methods: {

    getTechData() {
      let url = window.location.href
      // /gpon/api/tech-data/building/{device_name}?port={olt_port}
      api_request.get("/gpon/api/" + url.match(/tech-data\S+/)[0])
          .then(resp => this.detailData = resp.data)
          .catch(reason => {
            this.errorStatus = reason.response.status
            this.errorMessage = reason.response.data
          })
    },

    getFullAddress(address) {
      return formatAddress(address)
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

    deleteEnd3FromList(oltID, end3Index) {
      this.detailData.oltStates[oltID].customerLines.splice(end3Index, 1)
    },

    /**
     * Создаем новый сплиттер/райзер
     * @param {Number} oltID Индекс House OTL State в списке
     * @param {Object} newEnd3 Объект с новыми данными End3
     */
    createNewEnd3(oltID, newEnd3) {
      const data = {
        houseOltStateID: this.detailData.oltStates[oltID].id,
        end3: newEnd3,
      }
      this.handleRequest(
          api_request.post("/gpon/api/tech-data/end3", data), "Успешно создано"
      ).then(() => {
        // Обновляем все данные, чтобы загрузить новый перечень End3
        this.getTechData();
        // Очищаем список только что созданных End3
        newEnd3.list = []
      })
    },

    /**
     * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
     * @param {Promise} request
     * @param {String} successInfo
     */
    handleRequest(request, successInfo){
      return request.then(
            resp => {
              this.$toast.add({
                severity: 'success',
                summary: 'Обновлено',
                detail: successInfo,
                life: 3000
              });
              this.editMode = false;
            }
          )
          .catch(
              reason => {
                const status = reason.response.status
                this.$toast.add({severity: 'error', summary: `Ошибка ${status}`, detail: reason.response.data, life: 5000})
              }
          )
    },

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