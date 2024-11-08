<template>
  <Toast/>

  <div class="flex items-center py-3">
    <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
      <circle cx="8" cy="8" r="8"/>
    </svg>
    <div class="text-xl font-semibold m-0 me-3">
      <span class="p-2">Адрес:</span>
      <a :href="'/gpon/tech-data/building/'+buildingData.address.id">
        <Button outlined rounded
                :icon="buildingData.address.building_type === 'building'?'pi pi-building':'pi pi-home'"
                :label="getFullAddress(buildingData.address)"/>
      </a>
    </div>

    <!-- Сохранить изменения -->
    <Button v-if="editMode && (hasPermissionToUpdateHouseB || hasPermissionToUpdateHouseOLTState)" text
            severity="success" @click="updateBuildingInfo" class="save-button">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
        <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
      </svg>
      <span v-if="!isMobile">Обновить</span>
    </Button>
  </div>

  <div class="md:ml-20">

    <div class="flex items-center gap-2 py-4">

      <!-- РЕДАКТИРОВАНИЕ АДРЕСА ДОМА -->
      <div v-if="editMode && hasPermissionToUpdateHouseB">
        <AddressGetCreate :is-mobile="isMobile" :allow-create="true" :data="buildingData"></AddressGetCreate>
      </div>

      <!-- ПРОСМОТР ДОМА -->
      <template v-else>
        <BuildingIcon :type="buildingData.address.building_type" width="64" height="64"/>
        <div>
          <template v-if="buildingData.address.building_type === 'building'">
            Многоквартирный дом. Количество этажей: {{ buildingData.address.floors }} /
            Количество подъездов: {{ buildingData.address.total_entrances }}
          </template>
          <template v-else>
            Частный дом.
          </template>
        </div>
      </template>

    </div>

    <!-- ПОДЪЕЗДЫ В ДОМЕ -->
    <div class="py-2 flex flex-wrap items-center justify-around sm:grid grid-cols-2"
         :class="editMode?'':'bg-gray-200 dark:bg-gray-800'">
      <div class="p-2">Задействованные подъезды в доме для данного OLT порта</div>
      <div v-if="editMode && hasPermissionToUpdateHouseOLTState">
        <InputText v-model.trim="buildingData.entrances" fluid placeholder="Укажите подъезды"/>
      </div>
      <div v-else class="p-2">{{ buildingData.entrances || '-' }}</div>
    </div>

    <!-- ОПИСАНИЕ -->
    <div class="py-2 flex flex-wrap items-center justify-around sm:grid grid-cols-2">
      <div class="p-2">Описание сплиттера 2го каскада</div>
      <Textarea v-if="editMode && hasPermissionToUpdateHouseOLTState" fluid auto-resize
                v-model="buildingData.description" rows="5"/>
      <div v-else class="p-2">{{ buildingData.description || '-' }}</div>
    </div>

  </div>

</template>

<script>
import AddressGetCreate from "./AddressGetCreate.vue";
import BuildingIcon from "./BuildingIcon.vue";

import api from "@/services/api";
import {formatAddress} from "@/formats";

export default {
  name: "HouseOltStateViewEdit",
  components: {
    AddressGetCreate,
    BuildingIcon,
  },

  props: {
    buildingData: {required: true, type: Object},
    isMobile: {required: true, type: Boolean},
    editMode: {required: true, type: Boolean},
    userPermissions: {required: true, type: Array},
  },

  computed: {
    hasPermissionToUpdateHouseB() {
      return this.userPermissions.includes("gpon.change_houseb")
    },

    hasPermissionToUpdateHouseOLTState() {
      return this.userPermissions.includes("gpon.change_houseoltstate")
    },
  },

  methods: {
    getFullAddress(address) {
      return formatAddress(address)
    },

    updateBuildingInfo() {
      this.handleRequest(
          api.put("/gpon/api/tech-data/house-olt-state/" + this.buildingData.id, this.buildingData),
          'Данные дома были обновлены'
      )
    },


    /**
     * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
     * @param {Promise} request
     * @param {String} successInfo
     */
    handleRequest(request, successInfo) {
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
                this.$toast.add({
                  severity: 'error',
                  summary: `Ошибка ${status}`,
                  detail: reason.response.data,
                  life: 5000
                })
              }
          )
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
</style>