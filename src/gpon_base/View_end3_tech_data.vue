<template>
  <div id="app" class="w-75" style="margin: auto;">

    <Toast />

    <div class="header">
      <h2 class="py-3">Техническая возможность</h2>

      <div class="d-flex">
        <button @click="goToTechDataURL" class="back-button me-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
            <path d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/>
          </svg>
          <span v-if="!isMobile" class="m-2">Выйти</span>
        </button>

        <!-- Режим редактирования -->
        <template v-if="editMode">

          <!-- Сохранить изменения -->
          <button @click="updateEnd3Info" class="save-button me-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
            </svg>
            <span v-if="!isMobile" class="m-2">Сохранить</span>
          </button>

          <button @click="editMode = false" class="view-button me-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
              <path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/>
              <path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/>
            </svg>
            <span v-if="!isMobile" class="m-2">Просмотр</span>
          </button>

        </template>


        <!-- Режим просмотра -->
        <template v-else>
          <button @click="printData" class="print-button me-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
              <path d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2H5zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1z"/>
              <path d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2V7zm2.5 1a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
            </svg>
            <span v-if="!isMobile" class="m-2">Печать</span>
          </button>

          <button v-if="hasAnyPermissionToUpdate" @click="editMode = true" class="edit-button">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
              <path d="M12.854.146a.5.5 0 0 0-.707 0L10.5 1.793 14.207 5.5l1.647-1.646a.5.5 0 0 0 0-.708l-3-3zm.646 6.061L9.793 2.5 3.293 9H3.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.207l6.5-6.5zm-7.468 7.468A.5.5 0 0 1 6 13.5V13h-.5a.5.5 0 0 1-.5-.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.5-.5V10h-.5a.499.499 0 0 1-.175-.032l-.179.178a.5.5 0 0 0-.11.168l-2 5a.5.5 0 0 0 .65.65l5-2a.5.5 0 0 0 .168-.11l.178-.178z"/>
            </svg>
            <span v-if="!isMobile" class="m-2">Редактировать</span>
          </button>
        </template>


      </div>

    </div>

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


            <div v-if="detailData" class="px-3 rounded-0">
              <div v-for="(part, index) in detailData.capability" class="align-items-center row py-1">
                <div class="col-1">{{part.number}}</div>

                <div :class="editMode?['col-auto']:['col-3']">
                  <Dropdown v-if="editMode && hasPermissionToUpdateTechCapability"
                            v-model="part.status" :options="['empty', 'active', 'pause', 'reserved', 'bad']"
                            scroll-height="300px" :input-style="{padding: '0.2rem 1rem'}"
                            @change="updateTechCapability(index)"
                            placeholder="Выберите статус порта" class="me-2">
                    <template #value="slotProps"><TechCapabilityBadge :status="slotProps.value"/></template>
                    <template #option="slotProps"><TechCapabilityBadge :status="slotProps.option"/></template>
                  </Dropdown>
                  <TechCapabilityBadge v-else :status="part.status"/>
                </div>

                <div class="col-auto">
                  <div class="d-flex" v-for="subscriber in part.subscribers">
                    <div class="me-2">{{subscriber.name}}</div>
                    <div>{{ subscriber.transit }}</div>
                  </div>
                  <div class="text-muted" v-if="!part.subscribers.length">
                    нет абонента
                  </div>
                </div>
              </div>
            </div>


          </div>

        </div>

    </div>

  </div>
</template>

<script>
import Button from "primevue/button/Button.vue"
import Dropdown from "primevue/dropdown/Dropdown.vue"
import InlineMessage from "primevue/inlinemessage/InlineMessage.vue"
import InputText from "primevue/inputtext/InputText.vue"
import Toast from "primevue/toast/Toast.vue"
import AddressGetCreate from "./components/AddressGetCreate.vue";

import formatAddress from "../helpers/address";
import api_request from "../api_request";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue"
import printElementById from "../helpers/print";

export default {
  name: "Gpon_base.vue",
  components: {
    TechCapabilityBadge,
    AddressGetCreate,
    Button,
    Dropdown,
    InlineMessage,
    InputText,
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

    getCustomerLineClasses(index){
      let class_list = ['py-2', 'row', 'align-items-center']
      if (index % 2 === 0) class_list.push('grey-back');
      return class_list
    },

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

    /** @param {Integer} index */
    updateTechCapability(index){
      const capability = this.detailData.capability[index]
      const data = {status: capability.status}
      this.handleRequest(
          api_request.patch("/gpon/api/tech-data/tech-capability/"+capability.id, data)
      )
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
      request.then(
            resp => {
              this.$toast.add({severity: 'success', summary: 'Обновлено', detail: 'Статус был изменён', life: 3000})
              this.editMode = false
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

    printData() {printElementById('tech-data-block')},

    goToTechDataURL() {
      window.location.href = "/gpon/tech-data"
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

.edit-button {
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #ff802a;
  border: 1px #ff802a solid;
}
.edit-button:hover {
  box-shadow: 0 0 3px #ff802a;
}

.view-button {
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #2a4dff;
  border: 1px #2a4dff solid;
}
.view-button:hover {
  box-shadow: 0 0 3px #2a4dff;
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