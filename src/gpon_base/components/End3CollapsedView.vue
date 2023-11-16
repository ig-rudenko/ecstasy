<template>

  <ConfirmPopup/>

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

    <div v-if="editMode && hasPermissionToDeleteEnd3" class="col-auto">
        <button v-if="line.detailInfo" @click="deleteEnd3($event, line, index)" class="btn btn-outline-danger rounded-5 py-1">
          delete
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
import ConfirmPopup from "primevue/confirmpopup";
import Toast from "primevue/toast";

import End3PortsViewEdit from "./End3PortsViewEdit.vue";
import TechCapabilityBadge from "./TechCapabilityBadge.vue";
import Create_Subscriber_data from "../Create_Subscriber_data.vue";
import formatAddress from "../../helpers/address";
import api_request from "../../api_request";

export default {
  name: "End3CollapsedView",
  components: {
    ConfirmPopup,
    End3PortsViewEdit,
    TechCapabilityBadge,
    Dialog,
    Dropdown,
    CreateSubscriberData: Create_Subscriber_data,
    Toast,
  },
  props: {
    customerLines: {required: true, type: Array},
    userPermissions: {required: true, type: Array},
    deviceName: {required: false, default: null, type: String},
    devicePort: {required: false, default: null, type: String},
    buildingAddress: {required: false, default: null, type: Object},
    editMode: {required: false, default: false, type: Boolean},
  },

  computed: {
    hasPermissionToDeleteEnd3(){
      return this.userPermissions.includes("gpon.delete_end3")
    },
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

    deleteEnd3(event, end3, end3Index) {
      const end3VerboseType = this.customerLineTypeName(end3.type)
      for (const end3Port of end3.detailInfo) {
        if (end3Port.subscribers.length > 0) {
          this.$toast.add({ severity: 'warn', summary: 'Warning', detail: end3VerboseType+' содержит абонентов', life: 3000 });
          return
        }
      }

      this.$confirm.require({
          target: event.currentTarget,
          message: 'Вы уверены, что хотите удалить данный '+end3VerboseType+"?",
          icon: 'pi pi-info-circle',
          acceptLabel: "Да",
          rejectLabel: "Нет",
          acceptClass: 'p-button-danger p-button-sm',
          defaultFocus: "reject",
          accept: () => {
              api_request.delete("/gpon/api/tech-data/end3/"+end3.id).then(
                  () => {
                    this.$toast.add({
                      severity: 'error',
                      summary: 'Confirmed',
                      detail: end3VerboseType + ' был удален',
                      life: 3000
                    });
                    this.$emit("deletedEnd3", end3, end3Index)
                  }
              ).catch(
                  reason => this.$toast.add({ severity: 'error', summary: reason.response.status, detail: reason.response.data, life: 3000 })
              )
          },
          reject: () => {}
      });
    }

  }
}
</script>

<style scoped>
.grey-back {
  background-color: #ebebeb;
}
</style>