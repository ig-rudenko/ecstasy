<template>
  <div v-for="port in end3PortsArray" class="items-center flex flex-row gap-10 py-1">
    <div class="col-1">{{ port.number }}</div>
    <div>
      <Select v-if="editMode && hasPermissionToUpdateTechCapability"
              v-model="port.status" :options="['empty', 'active', 'pause', 'reserved', 'bad']"
              :input-style="{padding: '0.2rem 1rem'}"
              @change="updateTechCapabilityStatus(port)" fluid
              placeholder="Выберите статус порта">
        <template #value="slotProps">
          <TechCapabilityBadge :status="slotProps.value"/>
        </template>
        <template #option="slotProps">
          <TechCapabilityBadge :status="slotProps.option"/>
        </template>
      </Select>
      <TechCapabilityBadge v-else :status="port.status"/>
    </div>

    <div>
      <div class="flex items-center gap-3" v-for="subscriber in port.subscribers">
        <a v-if="hasPermissionsToViewSubscriber"
           :href="'/gpon/subscriber-data/customers/'+subscriber.customerID">
          <Button icon="pi pi-user" text :label="subscriber.customerName"></Button>
        </a>
        <div v-else>{{ subscriber.customerName }}</div>
        <div class="font-mono p-2" v-tooltip="'Транзит'">{{ subscriber.transit }}</div>
      </div>
      <div class="text-muted items-center flex gap-3" v-if="!port.subscribers.length">
        <span>нет абонента</span>

        <template v-if="hasPermissionsToCreateSubscriberData">
          <Button text size="small" v-tooltip="'Добавить абонента'" severity="success"
                  @click="showCreateSubscriberDataDialog[port.number]=!showCreateSubscriberDataDialog[port.number]">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#198754" viewBox="0 0 16 16">
              <path
                  d="M6 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0zm4 8c0 1-1 1-1 1H1s-1 0-1-1 1-4 6-4 6 3 6 4zm-1-.004c-.001-.246-.154-.986-.832-1.664C9.516 10.68 8.289 10 6 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10z"/>
              <path fill-rule="evenodd"
                    d="M13.5 5a.5.5 0 0 1 .5.5V7h1.5a.5.5 0 0 1 0 1H14v1.5a.5.5 0 0 1-1 0V8h-1.5a.5.5 0 0 1 0-1H13V5.5a.5.5 0 0 1 .5-.5z"/>
            </svg>
          </Button>

          <Dialog v-model:visible="showCreateSubscriberDataDialog[port.number]" class="w-full h-full" modal
                  header="Добавление абонентского подключения">
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
import TechCapabilityBadge from "./TechCapabilityBadge.vue";
import CreateSubscriberData from "../CreateSubscriberData.vue";
import api from "@/services/api";

export default {
  name: "End3PortsViewEdit",
  components: {
    TechCapabilityBadge,
    CreateSubscriberData,
  },
  emits: ["getInfo"],
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
    hasPermissionsToCreateSubscriberData() {
      return [
        "gpon.add_customer",
        "gpon.add_subscriberconnection",
      ].every(elem => {
        return this.userPermissions.includes(elem)
      })
    },
    hasPermissionsToViewSubscriber() {
      return [
        "gpon.view_customer",
        "gpon.view_subscriberconnection",
      ].every(elem => {
        return this.userPermissions.includes(elem)
      })
    },

    hasPermissionToUpdateTechCapability() {
      return this.userPermissions.includes("gpon.change_techcapability")
    },

  },

  methods: {

    /** @param {Object} capability */
    updateTechCapabilityStatus(capability) {
      const data = {status: capability.status}
      this.handleRequest(
          api.patch("/gpon/api/tech-data/tech-capability/" + capability.id, data)
      )
      this.$emit("changeStatus", capability.status)
    },

    /**
     * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
     * @param {Promise} request
     */
    handleRequest(request) {
      request.then(
          () => {
            this.$toast.add({severity: 'success', summary: 'Обновлено', detail: 'Статус был изменён', life: 3000})
            this.editMode = false
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

    createdNewSubscriberConnection(portNumber) {
      this.$emit('getInfo');
      this.showCreateSubscriberDataDialog[portNumber] = false;
      this.$toast.add({
        severity: 'success',
        summary: 'Обновлено',
        detail: 'Абонентское подключение было создано',
        life: 3000
      })
    }

  }

}
</script>

<style scoped>

</style>