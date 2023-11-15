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

    <End3PortsViewEdit
        @getInfo="$emit('getInfo', index)"
        :edit-mode="editMode"
        :user-permissions="userPermissions"
        :end3-object="line"
        :end3-ports-array="line.detailInfo"

        :device-name="deviceName"
        :device-port="devicePort"
        :building-address="buildingAddress"
    />
  </div>

</template>
</template>

<script>
import Dialog from "primevue/dialog/Dialog.vue";
import Dropdown from "primevue/dropdown/Dropdown.vue"

import End3PortsViewEdit from "./End3PortsViewEdit.vue";
import TechCapabilityBadge from "./TechCapabilityBadge.vue";
import Create_Subscriber_data from "../Create_Subscriber_data.vue";
import formatAddress from "../../helpers/address";

export default {
  name: "End3CollapsedView",
  components: {
    End3PortsViewEdit,
    TechCapabilityBadge,
    Dialog,
    Dropdown,
    CreateSubscriberData: Create_Subscriber_data,
  },
  props: {
    customerLines: {required: true, type: Array},
    userPermissions: {required: true, type: Array},
    deviceName: {required: false, default: null, type: String},
    devicePort: {required: false, default: null, type: String},
    buildingAddress: {required: false, default: null, type: Object},
    editMode: {required: false, default: false, type: Boolean},
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