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

      <!-- Станционные данные -->
      <div class="py-3">

        <div class="d-flex align-items-center py-3">
          <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
            <circle cx="8" cy="8" r="8"/>
          </svg>
          <h4 class="m-0 me-3">Станционные данные</h4>
          <!-- Сохранить изменения -->
          <button v-if="editMode && hasPermissionToUpdateOLTState" @click="updateOLTStateInfo" class="save-button">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
            </svg>
            <span v-if="!isMobile" class="m-2">Обновить</span>
          </button>
        </div>

        <div class="ml-40">

          <!-- ОБОРУДОВАНИЕ -->
          <div class="py-2 row align-items-center">
            <div class="col-4 fw-bold">OLT оборудование</div>
            <div class="col-auto">

              <!-- Редактирование имени оборудования -->
              <div v-if="editMode && hasPermissionToUpdateOLTState">
                    <Dropdown v-model="detailData.deviceName" :options="devicesList" filter
                              :option-label="x => x"
                              @change="deviceNameSelected" placeholder="Выберите устройство">
                      <template #value="slotProps">
                        <div v-if="slotProps.value" class="flex align-items-center"><div>{{ slotProps.value }}</div></div>
                        <span v-else>{{ slotProps.placeholder }}</span>
                      </template>
                      <template #option="slotProps">
                        <div class="flex align-items-center"><div>{{ slotProps.option }}</div></div>
                      </template>
                    </Dropdown>
              </div>

              <!-- Device Name -->
              <span v-else id="deviceName" class="badge fs-6" style="color: black">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                  <path d="M2 9a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zM2 2a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1z"/>
                </svg>
                {{detailData.deviceName}}
              </span>

            </div>

            <InlineMessage class="my-2" v-if="editMode && hasPermissionToUpdateOLTState" severity="warn">
              Будьте осторожны при выборе нового оборудования, данное действие необходимо только после физического
              переключения линии на другое оборудование.
            </InlineMessage>

          </div>

          <!-- ПОРТ -->
          <div class="py-2 row align-items-center ">
            <div class="col-4 fw-bold">Порт</div>
            <div class="col-auto fw-bold">

              <!-- Редактирование порта -->
              <div v-if="editMode && hasPermissionToUpdateOLTState">
                    <Dropdown v-model="detailData.devicePort" :options="devicePortList" filter
                              :option-label="x => x" placeholder="Выберите порт">
                      <template #value="slotProps">
                        <div v-if="slotProps.value" class="flex align-items-center"> <div>{{ slotProps.value }}</div> </div>
                        <span v-else> {{ slotProps.placeholder }} </span>
                      </template>
                      <template #option="slotProps">
                        <div class="flex align-items-center"><div>{{ slotProps.option }}</div></div>
                      </template>
                    </Dropdown>
              </div>

              <!-- Просмотр порта -->
              <template v-else>
                {{ detailData.devicePort }} <button class="btn btn-outline-primary rounded-5 py-1">status</button>
              </template>

            </div>

            <InlineMessage v-if="editMode && hasPermissionToUpdateOLTState" class="my-2" severity="warn">
              Будьте осторожны при выборе нового порта, данное действие необходимо только после физического
              переключения порта на оборудовании.
            </InlineMessage>

          </div>

          <!-- ВОЛОКНО -->
          <div class="py-2 row align-items-center">
            <div class="col-4 fw-bold">Волокно</div>
            <InputText v-if="editMode && hasPermissionToUpdateOLTState"
                       v-model.trim="detailData.fiber" class="w-100 my-1" type="text" placeholder="Название кабеля/номер волокна в кабеле"/>
            <div v-else class="col-auto">{{ detailData.fiber }}</div>
          </div>

          <!-- ОПИСАНИЕ -->
          <div class="py-2 row align-items-center ">
            <div class="col-4 fw-bold">Описание сплиттера 1го каскада</div>
            <Textarea v-if="editMode && hasPermissionToUpdateOLTState"
                      class="w-100 my-1" v-model="detailData.description" rows="5"/>
            <div v-else class="col-auto">{{ detailData.description }}</div>
          </div>

        </div>

      </div>


      <template v-for="(building, BIndex) in detailData.structures">

        <!-- АДРЕС -->
        <div class="py-3">

          <HouseOltStateViewEdit
              :building-data="building"
              :is-mobile="isMobile"
              :user-permissions="userPermissions"
              :edit-mode="editMode"
          />

        </div>

        <!-- Абонентская линия -->
        <div class="py-3">

          <div class="d-flex">
            <h4 class="px-5">Абонентская линия</h4>
          </div>

          <div class="ml-40">
            <End3CollapsedView
                @getInfo="index => getEnd3DetailInfo(BIndex, index)"
                @deleteInfo="index => deleteEnd3DetailInfo(BIndex, index)"
                @deletedEnd3="(end3, end3Index) => deleteEnd3(BIndex, end3Index)"
                :customer-lines="building.customerLines"
                :user-permissions="userPermissions"
                :edit-mode="editMode"

                :device-name="detailData.deviceName"
                :device-port="detailData.devicePort"
                :building-address="building.address"
            />
          </div>

        </div>
      </template>


    </div>

  </div>

  <ScrollTop/>

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
import HouseOltStateViewEdit from "./components/HouseOltStateViewEdit.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue";
import ViewPrintEditButtons from "./components/ViewPrintEditButtons.vue";
import api_request from "../api_request";
import formatAddress from "../helpers/address";
import printElementById from "../helpers/print";

export default {
  name: "Gpon_base.vue",
  components: {
    HouseOltStateViewEdit,
    ViewPrintEditButtons,
    End3CollapsedView,
    AddressGetCreate,
    BuildingIcon,
    Dropdown,
    InlineMessage,
    InputText,
    TechCapabilityBadge,
    Textarea,
    Toast,
    ScrollTop,
  },
  data() {
    return {
      detailData: null,
      errorStatus: null,
      errorMessage: null,
      userPermissions: [],
      windowWidth: window.innerWidth,
      editMode: false,
      _deviceNames: [],
      _devicesPorts: [],
    }
  },
  mounted() {
    api_request.get("/gpon/api/permissions").then(resp => {this.userPermissions = resp.data})

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
    },

    devicesList() {
      if (this._deviceNames.length === 0) this.getDeviceNames();
      return this._deviceNames;
    },

    devicePortList() {
      if (this.detailData.devicePort.length === 0 || this._devicesPorts.length === 0) this.getPortsNames();
      return this._devicesPorts;
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


    getFullAddress(address) {
      return formatAddress(address)
    },

    getEnd3DetailInfo(BIndex, end3Index) {
      const end3ID = this.detailData.structures[BIndex].customerLines[end3Index].id
      api_request.get("/gpon/api/tech-data/end3/" + end3ID)
          .then(resp => this.detailData.structures[BIndex].customerLines[end3Index].detailInfo = resp.data.capability)
          .catch(reason => {
            this.detailData.structures[BIndex].customerLines[end3Index].errorStatus = reason.response.status
            this.detailData.structures[BIndex].customerLines[end3Index].errorMessage = reason.response.data
          })
    },

    deleteEnd3DetailInfo(BIndex, end3Index) {
      this.detailData.structures[BIndex].customerLines[end3Index].detailInfo = null
    },

    deleteEnd3(BIndex, end3Index) {
      this.detailData.structures[BIndex].customerLines.splice(end3Index, 1)
    },

    printData() {printElementById('tech-data-block')},

    updateOLTStateInfo(){
      const data = {
        deviceName: this.detailData.deviceName,
        devicePort: this.detailData.devicePort,
        fiber: this.detailData.fiber,
        description: this.detailData.description,
      }
      const olt_id = this.detailData.id

      this.handleRequest(
          api_request.put("/gpon/api/tech-data/olt-state/" + olt_id, data),
          'Станционные данные были обновлены'
      )
    },

    /**
     * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
     * @param {Promise} request
     * @param {String} successInfo
     */
    handleRequest(request, successInfo){
      request.then(
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

    getDeviceNames() {
      api_request.get("/gpon/api/devices-names")
          .then(res => this._deviceNames = Array.from(res.data))
    },
    getPortsNames() {
      api_request.get("/gpon/api/ports-names/" + this.detailData.deviceName)
          .then(res => this._devicesPorts = Array.from(res.data))
    },

    deviceNameSelected() {
      this.detailData.devicePort = ""
      this.getPortsNames()
    },

  }
}
</script>

<style scoped>
.grey-back {
  background-color: #ebebeb;
}

.save-button {
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #008b1e;
  border: 1px #008b1e solid;
}
.save-button:hover {
  box-shadow: 0 0 3px #008b1e;
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