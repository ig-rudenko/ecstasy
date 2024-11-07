<template>
  <div id="app" class="w-75" style="margin: auto;">

    <Toast />

    <ViewPrintEditButtons
        @print="printData"
        @changeMode="mode => editMode = mode"
        title="Техническая возможность"
        exitButtonURL="/gpon/tech-data"
        :has-permission-to-edit="hasAnyPermissionToUpdate"
        :is-mobile="isMobile"/>

    <!-- ОШИБКА ЗАГРУЗКИ -->
    <div v-if="errorStatus" class="alert alert-danger">
      Ошибка при загрузке данных.
      <br> {{errorMessage||''}}
      <br> Статус: {{errorStatus}}
    </div>

    <div v-else id="tech-data-block" class="plate">

       <div class="d-flex align-items-center flex-wrap">

          <div class="ml-40 fs-5 d-flex flex-column">
            <span>{{detailData.type}}</span>
            <AddressGetCreate v-if="editMode && hasPermissionToUpdateEnd3" :is-mobile="isMobile" :allow-create="true" :data="detailData"></AddressGetCreate>
            <span v-else>{{end3Address}}</span>

            <InputText v-if="editMode && hasPermissionToUpdateEnd3" v-model.trim="detailData.location" class="w-100 my-1" type="text" placeholder="Локация"/>
            <span v-else class="fw-bold">{{detailData.location}}</span>

            <!-- Сохранить изменения -->
            <div v-if="editMode && hasPermissionToUpdateEnd3" class="pt-3">
              <button @click="updateEnd3Info" class="save-button">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
                </svg>
                <span v-if="!isMobile" class="m-2">Обновить</span>
              </button>
            </div>

          </div>
          <div class="mx-2">
            <svg v-if="detailData.type === 'rizer'" style="transform: rotate(300grad);" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 26 32" width="128" height="128">
              <path fill="#e6e6e6" d="M23 0H3a1 1 0 0 0-1 1v20a1 1 0 0 0 1 1h20a1 1 0 0 0 1-1V1a1 1 0 0 0-1-1z" class="colore6e6e6 svgShape"></path>
              <path fill="#cccccc" d="M25 10H1a1 1 0 1 0 0 2h24a1 1 0 1 0 0-2z" class="colorccc svgShape"></path>
              <path fill="#ffcc66" d="M4 22h2v10H4z" class="colorfc6 svgShape"></path><path fill="gray" d="M8 22h2v10H8z" class="colorgray svgShape"></path>
              <path fill="#88c057" d="M12 22h2v10h-2z" class="color88c057 svgShape"></path><path fill="#48a0dc" d="M16 22h2v10h-2z" class="color48a0dc svgShape"></path>
              <path fill="#9b7cab" d="M20 22h2v10h-2z" class="color9b7cab svgShape"></path>
            </svg>
            <img height="150" v-else src="/static/img/gpon/splitter.svg" alt="splitter">
          </div>

        </div>

        <!-- Абонентская линия -->
        <div class="py-3">

          <div class="ml-40">

            <template v-if="editMode && (hasPermissionToUpdateEnd3 && hasPermissionToUpdateTechCapability)">
                <div class="d-flex align-items-center flex-wrap">
                  <div class="me-2">Изменение ёмкости</div>
                  <Dropdown v-model.number="detailData.capacity" @change="changeCapacity" :options="[4, 8, 12, 16, 24]"
                            class="w-full md:w-14rem me-2"/>

                  <InlineMessage class="my-2" v-if="capacityWarning" :severity="errorSeverity">
                    {{capacityWarning}}
                  </InlineMessage>

                </div>

                <InlineMessage class="my-2" severity="warn">
                  Будьте осторожны при выборе новой ёмкости! Данное действие необходимо только после физического
                  переключения линии либо в случае ошибки.
                </InlineMessage>
            </template>

            <End3PortsViewEdit
                @getInfo="updateEnd3Info"
                :user-permissions="userPermissions"
                :end3-ports-array="detailData.capability"
                :end3-object="detailData"
                :edit-mode="editMode"
            />

          </div>

        </div>

    </div>

  </div>

  <ScrollTop />

</template>

<script>
import Button from "primevue/button/Button.vue"
import Dropdown from "primevue/dropdown/Dropdown.vue"
import InlineMessage from "primevue/inlinemessage/InlineMessage.vue"
import InputText from "primevue/inputtext/InputText.vue"
import ScrollTop from "primevue/scrolltop";
import Toast from "primevue/toast/Toast.vue"

import AddressGetCreate from "./components/AddressGetCreate.vue";
import End3PortsViewEdit from "./components/End3PortsViewEdit.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue"
import ViewPrintEditButtons from "./components/ViewPrintEditButtons.vue";
import api_request from "../api_request";
import formatAddress from "../helpers/address";
import printElementById from "../helpers/print";

export default {
  name: "Gpon_base.vue",
  components: {
    ViewPrintEditButtons,
    End3PortsViewEdit,
    TechCapabilityBadge,
    AddressGetCreate,
    Button,
    Dropdown,
    InlineMessage,
    InputText,
    ScrollTop,
    Toast,
  },
  data() {
    return {
      detailData: {
        "id": 1,
        "address": {
            "region": "Севастополь",
            "settlement": "Севастополь",
            "planStructure": "",
            "street": "улица Колобова",
            "house": "22А",
            "block": null,
            "floor": null,
            "apartment": null
        },
        "capacity": 8,
        "location": "1 подъезд 5 этаж",
        "type": "splitter",
        "capability": [
              {
                  "id": 1,
                  "status": "empty",
                  "number": "1",
                  "subscribers": [
                      {
                          "id": 1,
                          "name": "ФИО",
                          "transit": 1234567890
                      }
                  ]
              }
          ]
      },
      errorStatus: null,
      errorMessage: null,
      errorSeverity: null,

      userPermissions: [],
      originalCapacity: null,
      capacityWarning: null,

      windowWidth: window.innerWidth,
      editMode: false,
    }
  },
  mounted() {
    api_request.get("/gpon/api/permissions").then(resp => {this.userPermissions = resp.data})

    let url = window.location.href
    api_request.get("/gpon/api/" + url.match(/tech-data\S+/)[0])
        .then(resp => this.detailData = resp.data)
        .catch(reason => {
          this.errorStatus = reason.response.status
          this.errorMessage = reason.response.data
        })

    this.originalCapacity = this.detailData.capacity
    window.addEventListener('resize', () => {
      this.windowWidth = window.innerWidth
    })
  },

  computed: {

    hasPermissionToUpdateEnd3(){
      return this.userPermissions.includes("gpon.change_end3")
    },

    hasPermissionToUpdateTechCapability(){
      return this.userPermissions.includes("gpon.change_techcapability")
    },

    hasAnyPermissionToUpdate(){
      return this.hasPermissionToUpdateEnd3 || this.hasPermissionToUpdateTechCapability
    },

    isMobile() {
      return this.windowWidth <= 768
    },

    end3Address() {
      return formatAddress(this.detailData.address)
    },

  },

  methods: {

    changeCapacity(){
      if (this.detailData.capacity < this.originalCapacity){
        if (this.deletionUsersAffected()) {
          this.errorSeverity = "error"
          this.capacityWarning = "Изменение затронет существующие подключения абонентов. " +
              "Необходимо их перенести на другую линию, а затем изменить ёмкость."
        } else {
          this.errorSeverity = "warn"
          this.capacityWarning = "Внимание, вы указали ёмкость меньше, чем была изначально! Будут удалены последние записи"
        }
      } else if (this.detailData.capacity > this.originalCapacity) {
        this.errorSeverity = "info"
        this.capacityWarning = "Будут добавлены новые"
      } else {
        this.capacityWarning = null
      }
    },

    updateEnd3Info(){
      this.handleRequest(
          api_request.patch("/gpon/api/tech-data/end3/"+this.detailData.id, this.detailData)
      )
    },

    /**
     * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
     * @param {Promise} request
     */
    handleRequest(request){
      return request.then(
          () => {
              this.$toast.add({severity: 'success', summary: 'Обновлено', detail: 'Статус был изменён', life: 3000})
            }
          )
          .catch(
              reason => {
                const status = reason.response.status
                this.$toast.add({severity: 'error', summary: `Ошибка ${status}`, detail: reason.response.data, life: 5000})
              }
          )
    },

    deletionUsersAffected() {
      const shift = this.originalCapacity - this.detailData.capacity
      for (let i = shift - 1; i < this.detailData.capability.length; i++) {
          if (this.detailData.capability[i].subscribers.length) {
            return true
          }
        }
      return false
    },

    printData() {printElementById('tech-data-block')},

    goToTechDataURL() {
      window.location.href = "/gpon/tech-data"
    },

  }
}
</script>

<style scoped>

.plate {
  padding: 40px;
  border-radius: 14px;
  border: 1px solid #A3A3A3;
}

.ml-40 {
  margin-left: 40px;
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