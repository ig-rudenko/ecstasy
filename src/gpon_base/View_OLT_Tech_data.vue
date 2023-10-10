<template>
  <div id="app" class="w-75" style="margin: auto;">

    <Toast />

    <div class="header">
      <h2 class="py-3">Технические данные - OLT</h2>

      <!-- ДЕЙСТВИЯ -->
      <div class="d-flex">
        <button @click="goToTechDataURL" class="back-button me-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
            <path d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/>
          </svg>
          <span v-if="!isMobile" class="m-2">Выйти</span>
        </button>

        <!-- Режим редактирования -->
        <button v-if="editMode" @click="editMode = false" class="view-button me-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
            <path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/>
            <path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/>
          </svg>
          <span v-if="!isMobile" class="m-2">Просмотр</span>
        </button>

        <!-- Режим просмотра -->
        <template v-else>
          <button @click="printData" class="print-button me-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
              <path d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2H5zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1z"/>
              <path d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2V7zm2.5 1a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
            </svg>
            <span v-if="!isMobile" class="m-2">Печать</span>
          </button>

          <button @click="editMode = true" class="edit-button">
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

    <div v-if="detailData" id="tech-data-block" class="plate">

      <!-- Станционные данные -->
      <div class="py-3">

        <div class="d-flex align-items-center py-3">
          <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
            <circle cx="8" cy="8" r="8"/>
          </svg>
          <h4 class="m-0 me-3">Станционные данные</h4>
          <!-- Сохранить изменения -->
          <button v-if="editMode" @click="updateOLTStateInfo" class="save-button">
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

              <!-- Device Name -->
              <span v-if="!editMode" id="deviceName" class="badge fs-6" style="color: black">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2" viewBox="0 0 16 16">
                  <path d="M2 9a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zM2 2a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1z"/>
                </svg>
                {{detailData.deviceName}}
              </span>

              <!-- Редактирование имени оборудования -->
              <div v-else>
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
            </div>

            <InlineMessage class="my-2" v-if="editMode" severity="warn">
              Будьте осторожны при выборе нового оборудования, данное действие необходимо только после физического
              переключения линии на другое оборудование.
            </InlineMessage>

          </div>

          <!-- ПОРТ -->
          <div class="py-2 row align-items-center ">
            <div class="col-4 fw-bold">Порт</div>
            <div class="col-auto fw-bold">

              <!-- Просмотр порта -->
              <template v-if="!editMode">
                {{ detailData.devicePort }} <button class="btn btn-outline-primary rounded-5 py-1">status</button>
              </template>

              <!-- Редактирование порта -->
              <template v-else>
                <div>
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
              </template>
            </div>

            <InlineMessage class="my-2" v-if="editMode" severity="warn">
              Будьте осторожны при выборе нового порта, данное действие необходимо только после физического
              переключения порта на оборудовании.
            </InlineMessage>

          </div>

          <!-- ВОЛОКНО -->
          <div class="py-2 row align-items-center">
            <div class="col-4 fw-bold">Волокно</div>
            <div v-if="!editMode" class="col-auto">{{ detailData.fiber }}</div>
            <InputText v-else v-model.trim="detailData.fiber" class="w-100 my-1" type="text" placeholder="Название кабеля/номер волокна в кабеле"/>
          </div>

          <!-- ОПИСАНИЕ -->
          <div class="py-2 row align-items-center ">
            <div class="col-4 fw-bold">Описание сплиттера 1го каскада</div>
            <div v-if="!editMode" class="col-auto">{{ detailData.description }}</div>
            <Textarea v-else class="w-100 my-1" v-model="detailData.description" rows="5"/>
          </div>

        </div>

      </div>


      <template v-for="(building, BIndex) in detailData.structures">

        <!-- АДРЕС -->
        <div class="py-3">

          <div class="d-flex align-items-center py-3">
            <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
              <circle cx="8" cy="8" r="8"/>
            </svg>
            <h4 class="m-0 me-3">
              Адрес: <a :href="'/gpon/tech-data/building/'+building.id">{{ getFullAddress(building.address) }}</a>
            </h4>

            <!-- Сохранить изменения -->
            <button v-if="editMode" @click="updateBuildingInfo(building)" class="save-button">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
                <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
              </svg>
              <span v-if="!isMobile" class="m-2">Обновить</span>
            </button>
          </div>

          <div class="ml-40">

            <div class="row align-items-center">

              <!-- ПРОСМОТР ДОМА -->
              <template v-if="!editMode">
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
              </template>

              <!-- РЕДАКТИРОВАНИЕ АДРЕСА ДОМА -->
              <div v-else>
                <AddressGetCreate :is-mobile="isMobile" :allow-create="true" :data="building"></AddressGetCreate>
              </div>

            </div>

            <!-- ПОДЪЕЗДЫ В ДОМЕ -->
            <div class="py-2 row align-items-center grey-back">
              <div class="col-5 fw-bold">Задействованные подъезды в доме для данного OLT порта</div>
              <div v-if="!editMode" class="col-auto">{{ building.entrances }}</div>
              <InputText v-else v-model.trim="building.entrances" class="w-100 my-1" type="text" placeholder="Укажите подъезды"/>
            </div>

            <!-- ОПИСАНИЕ -->
            <div class="py-2 row align-items-center">
              <div class="col-5 fw-bold">Описание сплиттера 2го каскада</div>
              <div v-if="!editMode" class="col-auto">{{ building.description }}</div>
              <Textarea v-else class="w-100 my-1" v-model="building.description" rows="5"/>
            </div>

          </div>

        </div>

        <!-- Абонентская линия -->
        <div class="py-3">

          <div class="d-flex">
            <h4 class="px-5">Абонентская линия</h4>
          </div>

          <div class="ml-40">

            <template v-for="(line, index) in building.customerLines">

              <div :class="getCustomerLineClasses(index)">

                <div class="col-md-2 fw-bold">
                  <a :href="'/gpon/tech-data/end3/' + line.id">
                    {{ customerLineTypeName(line.type) }} {{ index + 1 }}
                  </a>
                </div>
                <div class="col-auto">
                    {{ getFullAddress(line.address) }}
                    <br>
                    Локация: {{ line.location }}.
                </div>
                <div class="col-auto">{{ customerLineNumbers(line) }}</div>
                <div class="col-auto">
                    <button v-if="line.detailInfo" @click="deleteEnd3DetailInfo(BIndex, index)" class="btn btn-outline-warning rounded-5 py-1">
                      close
                    </button>
                    <button v-else @click="getEnd3DetailInfo(BIndex, index)" class="btn btn-outline-primary rounded-5 py-1">
                      detail
                    </button>
                </div>
              </div>

              <div v-if="line.errorStatus" class="alert alert-danger">Ошибка при загрузке данных.
                <br> {{line.errorMessage||''}} <br> Статус: {{line.errorStatus}}
              </div>

              <div v-if="line.detailInfo" class="card px-3 rounded-0" style="border-top: none; margin-bottom: 10px">
                <div v-for="part in line.detailInfo" class="align-items-center row py-1">
                  <div class="col-1">{{part.number}}</div>
                    <div class="col-2">
                      <TechCapabilityBadge v-if="!editMode" :status="part.status"/>
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

            </template>

          </div>

        </div>
      </template>


    </div>

  </div>
</template>

<script>
import BuildingIcon from "./components/BuildingIcon.vue"
import Dropdown from "primevue/dropdown/Dropdown.vue"
import InlineMessage from "primevue/inlinemessage/InlineMessage.vue"
import InputText from "primevue/inputtext/InputText.vue"
import Table from "./components/Table.vue";
import Textarea from "primevue/textarea/Textarea.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue";
import Toast from "primevue/toast/Toast.vue"

import formatAddress from "../helpers/address";
import api_request from "../api_request";
import AddressGetCreate from "./components/AddressGetCreate.vue";
import printElementById from "../helpers/print";

export default {
  name: "Gpon_base.vue",
  components: {
    AddressGetCreate,
    BuildingIcon,
    Dropdown,
    InlineMessage,
    InputText,
    Table,
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
      editMode: false,
      _deviceNames: [],
      _devicesPorts: [],
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
    },

    devicesList() {
      if (this._deviceNames.length === 0) this.getDeviceNames();
      return this._deviceNames;
    },

    devicePortList() {
      if (this.detailData.devicePort.length === 0 || this._devicesPorts.length === 0) this.getPortsNames();
      return this._devicesPorts;
    },

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

    updateBuildingInfo(house_olt_state_data){
      this.handleRequest(
          api_request.put("/gpon/api/tech-data/house-olt-state/" + house_olt_state_data.id, house_olt_state_data),
          'Данные дома были обновлены'
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

    goToTechDataURL() {
      window.location.href = "/gpon/tech-data"
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