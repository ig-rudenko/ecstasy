<template>
  <Toast />

  <div class="d-flex align-items-center py-3">
    <svg width="32" height="32" fill="#633BBC" viewBox="0 0 16 16" class="me-2">
      <circle cx="8" cy="8" r="8"/>
    </svg>
    <h4 class="m-0 me-3">
      Адрес: <a :href="'/gpon/tech-data/building/'+buildingData.id">{{ getFullAddress(buildingData.address) }}</a>
    </h4>

    <!-- Сохранить изменения -->
    <button v-if="editMode && (hasPermissionToUpdateHouseB || hasPermissionToUpdateHouseOLTState)"
            @click="updateBuildingInfo" class="save-button">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
        <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
      </svg>
      <span v-if="!isMobile" class="m-2">Обновить</span>
    </button>
  </div>

  <div class="ml-40">

    <div class="row align-items-center">

      <!-- РЕДАКТИРОВАНИЕ АДРЕСА ДОМА -->
      <div v-if="editMode && hasPermissionToUpdateHouseB">
        <AddressGetCreate :is-mobile="isMobile" :allow-create="true" :data="buildingData"></AddressGetCreate>
      </div>

      <!-- ПРОСМОТР ДОМА -->
      <template v-else>
        <div class="col-auto">
          <BuildingIcon class="m-3" :type="buildingData.address.building_type" width="64" height="64"/>
        </div>
        <div class="col-8">
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
    <div class="py-2 row align-items-center grey-back">
      <div class="col-5 fw-bold">Задействованные подъезды в доме для данного OLT порта</div>
      <InputText v-if="editMode && hasPermissionToUpdateHouseOLTState"
                 v-model.trim="buildingData.entrances" class="w-100 my-1" type="text" placeholder="Укажите подъезды"/>
      <div v-else class="col-auto">{{ buildingData.entrances }}</div>
    </div>

    <!-- ОПИСАНИЕ -->
    <div class="py-2 row align-items-center">
      <div class="col-5 fw-bold">Описание сплиттера 2го каскада</div>
      <Textarea v-if="editMode && hasPermissionToUpdateHouseOLTState"
                class="w-100 my-1" v-model="buildingData.description" rows="5"/>
      <div v-else class="col-auto">{{ buildingData.description }}</div>
    </div>

  </div>

</template>

<script>
import AddressGetCreate from "./AddressGetCreate.vue";
import InputText from "primevue/inputtext/InputText.vue";
import Textarea from "primevue/textarea/Textarea.vue";
import Toast from "primevue/toast/Toast.vue"

import BuildingIcon from "./BuildingIcon.vue";
import api_request from "../../api_request";
import formatAddress from "../../helpers/address";

export default {
  name: "HouseOltStateViewEdit",
  components: {
    AddressGetCreate,
    InputText,
    Textarea,
    BuildingIcon,
    Toast,
  },

  props: {
    buildingData: {required: true, type: Object},
    isMobile: {required: true, type: Boolean},
    editMode: {required: true, type: Boolean},
    userPermissions: {required: true, type: Array},
  },

  computed: {
    hasPermissionToUpdateHouseB(){
      return this.userPermissions.includes("gpon.change_houseb")
    },

    hasPermissionToUpdateHouseOLTState(){
      return this.userPermissions.includes("gpon.change_houseoltstate")
    },
  },

  methods: {
    getFullAddress(address) {
      return formatAddress(address)
    },

    updateBuildingInfo(){
      this.handleRequest(
          api_request.put("/gpon/api/tech-data/house-olt-state/" + this.buildingData.id, this.buildingData),
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
  }
}
</script>

<style scoped>
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
</style>