<template>

<template v-for="(line, index) in customerLines">

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
        <button v-if="line.detailInfo" @click="$emit('deleteInfo', index)" class="btn btn-outline-warning rounded-5 py-1">
          close
        </button>
        <button v-else @click="$emit('getInfo', index)" class="btn btn-outline-primary rounded-5 py-1">
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
          <TechCapabilityBadge :status="part.status"/>
        </div>
      <div class="col-auto">
        <div class="d-flex" v-for="subscriber in part.subscribers">
          <div class="me-2">{{subscriber.name}}</div>
          <div>{{ subscriber.transit }}</div>
        </div>
        <div class="text-muted flex-row" v-if="!part.subscribers.length">
          <span class="me-2">нет абонента</span>

          <template v-if="hasPermissionsToCreateSubscriberData">
            <div @click="showCreateSubscriberDataDialog[part.number]=!showCreateSubscriberDataDialog[part.number]">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#198754" style="cursor: pointer" viewBox="0 0 16 16">
                <path d="M6 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0zm4 8c0 1-1 1-1 1H1s-1 0-1-1 1-4 6-4 6 3 6 4zm-1-.004c-.001-.246-.154-.986-.832-1.664C9.516 10.68 8.289 10 6 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10z"/>
                <path fill-rule="evenodd" d="M13.5 5a.5.5 0 0 1 .5.5V7h1.5a.5.5 0 0 1 0 1H14v1.5a.5.5 0 0 1-1 0V8h-1.5a.5.5 0 0 1 0-1H13V5.5a.5.5 0 0 1 .5-.5z"/>
              </svg>
            </div>
            <Dialog style="max-height: 100%" v-model:visible="showCreateSubscriberDataDialog[part.number]" modal header="Добавление абонентского подключения"
              :style="{ width: '100vw', height: '100vw' }">
              <CreateSubscriberData
                  @successfullyCreated="() => {$emit('getInfo', index); showCreateSubscriberDataDialog[part.number]=false;}"
                  :init-device-name="deviceName"
                  :init-device-port="devicePort"
                  :init-building-address="buildingAddress"
                  :init-end3="line"
                  :init-end3-port="part"
                  :is-modal-view="true"
              />
            </Dialog>
          </template>

        </div>
      </div>
    </div>
  </div>

</template>
</template>

<script>
import Dialog from "primevue/dialog/Dialog.vue";

import TechCapabilityBadge from "./TechCapabilityBadge.vue";
import Create_Subscriber_data from "../Create_Subscriber_data.vue";
import formatAddress from "../../helpers/address";

export default {
  name: "End3CollapsedView",
  components: {
    TechCapabilityBadge,
    Dialog,
    CreateSubscriberData: Create_Subscriber_data,
  },
  props: {
    customerLines: {required: true, type: Array},
    userPermissions: {required: true, type: Array},
    deviceName: {required: false, default: null},
    devicePort: {required: false, default: null},
    buildingAddress: {required: false, default: null},
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
    }
  },

  methods: {

    getCustomerLineClasses(index){
      let class_list = ['py-2', 'row', 'align-items-center']
      if (index % 2 === 0) class_list.push('grey-back');
      return class_list
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

    getFullAddress(address) {
      return formatAddress(address)
    },
  }
}
</script>

<style scoped>
.grey-back {
  background-color: #ebebeb;
}
</style>