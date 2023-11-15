<template>
  <Toast />

  <div v-for="port in end3PortsArray" class="align-items-center row py-1">
    <div class="col-1">{{port.number}}</div>
    <div :class="editMode?['col-auto']:['col-3']">
      <Dropdown v-if="editMode && hasPermissionToUpdateTechCapability"
                v-model="port.status" :options="['empty', 'active', 'pause', 'reserved', 'bad']"
                scroll-height="300px" :input-style="{padding: '0.2rem 1rem'}"
                @change="updateTechCapabilityStatus(port)"
                placeholder="Выберите статус порта" class="me-2">
        <template #value="slotProps"><TechCapabilityBadge :status="slotProps.value"/></template>
        <template #option="slotProps"><TechCapabilityBadge :status="slotProps.option"/></template>
      </Dropdown>
      <TechCapabilityBadge v-else :status="port.status"/>
    </div>

    <div class="col-auto">
      <div class="d-flex" v-for="subscriber in port.subscribers">
        <div class="me-2">{{subscriber.name}}</div>
        <div>{{ subscriber.transit }}</div>
      </div>
      <div class="text-muted flex-row" v-if="!port.subscribers.length">
        <span class="me-2">нет абонента</span>

        <template v-if="hasPermissionsToCreateSubscriberData">
          <div @click="showCreateSubscriberDataDialog[port.number]=!showCreateSubscriberDataDialog[port.number]">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#198754" style="cursor: pointer" viewBox="0 0 16 16">
              <path d="M6 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0zm4 8c0 1-1 1-1 1H1s-1 0-1-1 1-4 6-4 6 3 6 4zm-1-.004c-.001-.246-.154-.986-.832-1.664C9.516 10.68 8.289 10 6 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10z"/>
              <path fill-rule="evenodd" d="M13.5 5a.5.5 0 0 1 .5.5V7h1.5a.5.5 0 0 1 0 1H14v1.5a.5.5 0 0 1-1 0V8h-1.5a.5.5 0 0 1 0-1H13V5.5a.5.5 0 0 1 .5-.5z"/>
            </svg>
          </div>
          <Dialog v-model:visible="showCreateSubscriberDataDialog[port.number]"
                  style="max-height: 100%; width: 100vw; height: 100vw;" modal header="Добавление абонентского подключения">
            <CreateSubscriberData
                @successfullyCreated="() => createdNewSubscriberConnection(port.number)"
                :init-device-name="deviceName"
                :init-device-port="devicePort"
                :init-building-address="buildingAddress"
                :init-end3="end3Object"
                :init-end3-port="port"
                :is-modal-view="true"
            />
          </Dialog>
        </template>

      </div>
    </div>
  </div>
</template>

<script>
import Dialog from "primevue/dialog/Dialog.vue";
import Dropdown from "primevue/dropdown/Dropdown.vue";
import Toast from "primevue/toast/Toast.vue"

import TechCapabilityBadge from "./TechCapabilityBadge.vue";
import Create_Subscriber_data from "../Create_Subscriber_data.vue";
import api_request from "../../api_request";

export default {
  name: "End3PortsViewEdit",
  components: {
    Dialog,
    Dropdown,
    TechCapabilityBadge,
    Toast,
    CreateSubscriberData: Create_Subscriber_data,
  },
  props: {
    end3Object: {required: true, type: Object},
    end3PortsArray: {required: true, type: Array},
    userPermissions: {required: true, type: Array},

    deviceName: {required: false, default: null, type: String},
    devicePort: {required: false, default: null, type: String},
    buildingAddress: {required: false, default: null, type: Object},
    editMode: {required: false, default: false, type: Boolean},
  },

  data() {
    return {
      showCreateSubscriberDataDialog: {}
    }
  },


  computed: {
    hasPermissionsToCreateSubscriberData(){
      return [
          "gpon.add_customer",
          "gpon.add_subscriberconnection",
      ].every(elem => {return this.userPermissions.includes(elem)})
    },

    hasPermissionToUpdateTechCapability(){
      return this.userPermissions.includes("gpon.change_techcapability")
    },

  },


  methods: {

    /** @param {Object} capability */
    updateTechCapabilityStatus(capability){
      const data = {status: capability.status}
      this.handleRequest(
          api_request.patch("/gpon/api/tech-data/tech-capability/"+capability.id, data)
      )
      this.$emit("changeStatus", capability.status)
    },

    /**
     * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
     * @param {Promise} request
     */
    handleRequest(request){
      request.then(
          () => {
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

    createdNewSubscriberConnection(portNumber) {
      this.$emit('getInfo');
      this.showCreateSubscriberDataDialog[portNumber]=false;
      this.$toast.add({severity: 'success', summary: 'Обновлено', detail: 'Абонентское подключение было создано', life: 3000})
    }

  }

}
</script>

<style scoped>

</style>