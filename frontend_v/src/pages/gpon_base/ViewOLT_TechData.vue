<template>
  <Header/>

  <div class="mx-auto py-5 xl:w-2/3">

    <ViewPrintEditButtons
        @print="printData"
        @changeMode="mode => editMode = mode"
        @exit="() => $router.push({name: 'gpon-tech-data'})"
        title="Технические данные"
        :sub-title="deviceName"
        :has-permission-to-edit="hasAnyPermissionToUpdate"
        :is-mobile="isMobile"
    />

    <!-- ОШИБКА ЗАГРУЗКИ -->
    <Message v-if="errorStatus" severity="error" class="my-2 p-3">
      Ошибка при загрузке данных.
      <br> {{ errorMessage || '' }}
      <br> Статус: {{ errorStatus }}
    </Message>

    <div v-if="detailData" id="tech-data-block" class="plate">

      <!-- Станционные данные -->
      <div class="py-3">

        <div class="flex items-center py-3">
          <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
            <circle cx="8" cy="8" r="8"/>
          </svg>
          <div class="text-xl font-semibold m-0 me-3">Станционные данные</div>
          <!-- Сохранить изменения -->
          <Button v-if="editMode && hasPermissionToUpdateOLTState" @click="updateOLTStateInfo"
                  severity="success" class="save-button" text>
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
              <path
                  d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
            </svg>
            <span v-if="!isMobile">Обновить</span>
          </Button>
        </div>

        <div>

          <!-- ОБОРУДОВАНИЕ -->
          <div class="py-2 sm:grid grid-cols-2">
            <div class="p-2">OLT оборудование</div>
            <div>

              <!-- Редактирование имени оборудования -->
              <div v-if="editMode && hasPermissionToUpdateOLTState">
                <Select v-model="detailData.deviceName" :options="devicesList" filter
                        :option-label="x => x" fluid
                        :virtualScrollerOptions="{ itemSize: 38 }"
                        @change="deviceNameSelected" placeholder="Выберите устройство">
                  <template #value="slotProps">
                    <div v-if="slotProps.value" class="flex items-center">
                      <div>{{ slotProps.value }}</div>
                    </div>
                    <span v-else>{{ slotProps.placeholder }}</span>
                  </template>
                  <template #option="slotProps">
                    <div class="flex items-center">
                      <div>{{ slotProps.option }}</div>
                    </div>
                  </template>
                </Select>
              </div>

              <!-- Device Name -->
              <span v-else id="deviceName" class="items-center flex flex-wrap gap-3 text-primary font-mono">
                <router-link :to="'/device/'+detailData.deviceName" target="_blank">
                  <Button text>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor"
                         viewBox="0 0 16 16">
                      <path
                          d="M2 9a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zM2 2a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1z"/>
                    </svg>
                  </Button>
                </router-link>
                <span>{{ detailData.deviceName }}</span>
                <OltPortsSubscriberStatistic :device-name="detailData.deviceName"/>
              </span>
            </div>

            <Message class="my-4 col-span-2" v-if="editMode && hasPermissionToUpdateOLTState" severity="warn">
              Будьте осторожны при выборе нового оборудования, данное действие необходимо только после физического
              переключения линии на другое оборудование.
            </Message>

          </div>

          <!-- ПОРТ -->
          <div class="py-2 flex flex-wrap items-center justify-around sm:grid grid-cols-2"
               :class="editMode?'':'bg-gray-200 dark:bg-gray-800'">
            <div class="p-2">Порт</div>
            <div>

              <!-- Редактирование порта -->
              <div v-if="editMode && hasPermissionToUpdateOLTState">
                <Select v-model="detailData.devicePort" :options="devicePortList" filter fluid
                        :option-label="x => x" placeholder="Выберите порт">
                  <template #value="slotProps">
                    <div v-if="slotProps.value" class="flex items-center">
                      <div>{{ slotProps.value }}</div>
                    </div>
                    <span v-else> {{ slotProps.placeholder }} </span>
                  </template>
                  <template #option="slotProps">
                    <div class="flex items-center">
                      <div>{{ slotProps.option }}</div>
                    </div>
                  </template>
                </Select>
              </div>

              <!-- Просмотр порта -->
              <div v-else class="p-2">{{ detailData.devicePort }}</div>

            </div>

            <Message v-if="editMode && hasPermissionToUpdateOLTState" class="my-3 col-span-2" severity="warn">
              Будьте осторожны при выборе нового порта, данное действие необходимо только после физического
              переключения порта на оборудовании.
            </Message>

          </div>

          <!-- ВОЛОКНО -->
          <div class="py-2 flex flex-wrap items-center justify-around sm:grid grid-cols-2">
            <div class="p-2">Волокно</div>
            <InputText v-if="editMode && hasPermissionToUpdateOLTState" v-model.trim="detailData.fiber" fluid
                       placeholder="Название кабеля/номер волокна в кабеле"/>
            <div v-else class="p-2">{{ detailData.fiber }}</div>
          </div>

          <!-- ОПИСАНИЕ -->
          <div class="py-2 flex flex-wrap items-center justify-around sm:grid grid-cols-2"
               :class="editMode?'':'bg-gray-200 dark:bg-gray-800'">
            <div class="p-2">Описание сплиттера 1го каскада</div>
            <Textarea v-if="editMode && hasPermissionToUpdateOLTState" auto-resize fluid
                      v-model="detailData.description" rows="5"/>
            <div v-else class="p-2">{{ detailData.description }}</div>
          </div>

        </div>

      </div>


      <Fieldset v-for="(building, BIndex) in detailData.structures" :toggleable="true" class="my-2">
        <template #legend="{toggleCallback}">
          <div class="flex items-center p-1">
            <svg width="32" height="32" fill="#633BBC" @click="toggleCallback" viewBox="0 0 16 16"
                 class="cursor-pointer">
              <circle cx="8" cy="8" r="8"/>
            </svg>
            <div class="text-xl font-semibold m-0 me-3">
              <span class="p-2">Адрес:</span>
              <router-link :to="'/gpon/tech-data/building/'+building.address.id">
                <Button outlined rounded
                        :icon="building.address.building_type === 'building'?'pi pi-building':'pi pi-home'"
                        :label="getFullAddress(building.address)"/>
              </router-link>
            </div>
          </div>
        </template>

        <!-- АДРЕС -->
        <div class="py-3">
          <HouseOltStateViewEdit
              :building-data="building"
              :is-mobile="isMobile"
              :user-permissions="userPermissions"
              :edit-mode="editMode"/>

        </div>

        <!-- Абонентская линия -->
        <div class="py-3 md:ml-20">

          <div class="text-xl font-semibold m-0 p-2">Абонентская линия</div>

          <div>
            <End3CollapsedView
                @getInfo="index => getEnd3DetailInfo(BIndex, index)"
                @deleteInfo="index => deleteEnd3DetailInfo(BIndex, index)"
                @deletedEnd3="(end3, end3Index) => deleteEnd3FromList(BIndex, end3Index)"
                @createNewEnd3="newEnd3List => createNewEnd3(BIndex, newEnd3List)"
                :customer-lines="building.customerLines"
                :user-permissions="userPermissions"
                :edit-mode="editMode"

                :device-name="detailData.deviceName"
                :device-port="detailData.devicePort"
                :building-address="building.address"
            />
          </div>

        </div>
      </Fieldset>


    </div>

    <div v-else class="flex justify-center p-4">
      <ProgressSpinner/>
    </div>


  </div>

  <Footer/>

</template>

<script>
import AddressGetCreate from "./components/AddressGetCreate.vue";
import BuildingIcon from "./components/BuildingIcon.vue"
import End3CollapsedView from "./components/End3CollapsedView.vue";
import HouseOltStateViewEdit from "./components/HouseOltStateViewEdit.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue";
import ViewPrintEditButtons from "./components/ViewPrintEditButtons.vue";
import OltPortsSubscriberStatistic from "./components/OltPortsSubscriberStatistic.vue";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

import api from "@/services/api";
import {formatAddress} from "@/formats";
import printElementById from "@/helpers/print";

export default {
  name: "ViewOLT_TechData",
  components: {
    Footer,
    Header,
    OltPortsSubscriberStatistic,
    HouseOltStateViewEdit,
    ViewPrintEditButtons,
    End3CollapsedView,
    AddressGetCreate,
    BuildingIcon,
    TechCapabilityBadge,
  },
  data() {
    return {
      deviceName: "",
      oltPort: "",

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
    this.deviceName = this.$route.params.deviceName;
    this.oltPort = this.$route.query.port;

    api.get("/api/v1/gpon/permissions").then(resp => {
      this.userPermissions = resp.data
    })

    this.getTechData()
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

    hasPermissionToUpdateOLTState() {
      return this.userPermissions.includes("gpon.change_oltstate")
    },

    hasPermissionToUpdateHouseOLTState() {
      return this.userPermissions.includes("gpon.change_houseoltstate")
    },

    hasPermissionToUpdateHouseB() {
      return this.userPermissions.includes("gpon.change_houseb")
    },

    hasAnyPermissionToUpdate() {
      return this.hasPermissionToUpdateOLTState || this.hasPermissionToUpdateHouseOLTState || this.hasPermissionToUpdateHouseB
    },

  },

  methods: {

    getTechData() {
      let url = window.location.href
      // /api/v1/gpon/tech-data/{device_name}?port={olt_port}
      api.get("/api/v1/gpon/" + url.match(/tech-data\S+/)[0])
          .then(resp => this.detailData = resp.data)
          .catch(reason => {
            this.errorStatus = reason.response.status
            this.errorMessage = reason.response.data
          })
    },

    getFullAddress(address) {
      return formatAddress(address)
    },

    /**
     * Получаем подробные данные для конкретного сплиттера/райзера
     * @param {Number} BIndex Индекс в списке домов текущего OTL State
     * @param {Number} end3Index Индекс в списке end3 текущего end3
     */
    getEnd3DetailInfo(BIndex, end3Index) {
      const end3ID = this.detailData.structures[BIndex].customerLines[end3Index].id
      api.get("/api/v1/gpon/tech-data/end3/" + end3ID)
          .then(resp => this.detailData.structures[BIndex].customerLines[end3Index].detailInfo = resp.data.capability)
          .catch(reason => {
            this.detailData.structures[BIndex].customerLines[end3Index].errorStatus = reason.response.status
            this.detailData.structures[BIndex].customerLines[end3Index].errorMessage = reason.response.data
          })
    },

    deleteEnd3DetailInfo(BIndex, end3Index) {
      this.detailData.structures[BIndex].customerLines[end3Index].detailInfo = null
    },

    deleteEnd3FromList(BIndex, end3Index) {
      this.detailData.structures[BIndex].customerLines.splice(end3Index, 1)
    },

    /**
     * Создаем новый сплиттер/райзер
     * @param {Number} BIndex Индекс House OTL State в списке домов
     * @param {Object} newEnd3 Объект с новыми данными End3
     */
    createNewEnd3(BIndex, newEnd3) {
      const data = {
        houseOltStateID: this.detailData.structures[BIndex].id,
        end3: newEnd3,
      }
      this.handleRequest(
          api.post("/api/v1/gpon/tech-data/end3", data), "Успешно создано"
      ).then(() => {
        // Обновляем все данные, чтобы загрузить новый перечень End3
        this.getTechData();
        // Очищаем список только что созданных End3
        newEnd3.list = []
      })
    },

    printData() {
      printElementById('tech-data-block')
    },

    updateOLTStateInfo() {
      const data = {
        deviceName: this.detailData.deviceName,
        devicePort: this.detailData.devicePort,
        fiber: this.detailData.fiber,
        description: this.detailData.description,
      }
      const olt_id = this.detailData.id

      this.handleRequest(
          api.put("/api/v1/gpon/tech-data/olt-state/" + olt_id, data),
          'Станционные данные были обновлены'
      )
    },

    /**
     * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
     * @param {Promise} request
     * @param {String} successInfo
     */
    handleRequest(request, successInfo) {
      return request.then(
          () => {
            this.$toast.add({severity: 'success', summary: 'Обновлено', detail: successInfo, life: 3000});
          }
      )
          .catch(
              reason => {
                const status = reason.response.status
                this.$toast.add({
                  severity: 'error',
                  summary: `Ошибка ${status}`,
                  detail: reason.response.data,
                  life: 5000
                })
              }
          )
    },

    getDeviceNames() {
      api.get("/api/v1/gpon/devices-names")
          .then(res => this._deviceNames = Array.from(res.data))
    },
    getPortsNames() {
      api.get("/api/v1/gpon/ports-names/" + this.detailData.deviceName)
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

.save-button {
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

@media (max-width: 835px) {
  .container {
    margin-left: 0 !important;
    margin-right: 0 !important;
    max-width: 100% !important;
  }

  .plate {
    border: none;
  }
}

</style>