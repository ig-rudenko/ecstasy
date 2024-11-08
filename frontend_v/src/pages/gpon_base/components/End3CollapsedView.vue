<template>

  <ConfirmPopup/>

  <template v-for="(line, index) in customerLines">

    <div class="flex items-center gap-10 p-2 odd:bg-gray-200 dark:odd:bg-gray-800">

      <a :href="'/gpon/tech-data/end3/' + line.id">
        <Button text class="font-bold">
          {{ customerLineTypeName(line.type) }} {{ index + 1 }}
        </Button>
      </a>

      <div>
        {{ getFullAddress(line.address) }}
        <br>
        Локация: {{ line.location }}.
      </div>

      <div>{{ customerLineNumbers(line) }}</div>

      <div>
        <Button v-if="line.detailInfo" @click="$emit('deleteInfo', index)" severity="warn" outlined rounded
                size="small" label="свернуть"/>
        <Button v-else @click="$emit('getInfo', index)" outlined rounded size="small" label="подробнее"/>
      </div>

      <div v-if="editMode && hasPermissionToDeleteEnd3">
        <Button v-if="line.detailInfo" @click="deleteEnd3($event, line, index)" rounded size="small"
                severity="danger" icon="pi pi-trash"
                label="удалить"/>
      </div>

    </div>

    <div v-if="line.errorStatus" class="alert alert-danger">Ошибка при загрузке данных.
      <br> {{ line.errorMessage || '' }} <br> Статус: {{ line.errorStatus }}
    </div>

    <div v-if="line.detailInfo" class="px-3 rounded-0">

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

  <!-- ДОБАВЛЕНИЕ НОВОГО СПЛИТТЕРА / РАЙЗЕРА -->
  <div class="py-2">
    <Button @click="showAddNewEnd3Dialog=!showAddNewEnd3Dialog" text severity="success">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2Z"/>
      </svg>
      <span>Добавить</span>
    </Button>

    <Dialog v-model:visible="showAddNewEnd3Dialog" modal header="Добавление end3">
      <div>
        <SplittersRizersFind :init="newEnd3.existingSplitter"
                             :type="newEnd3.type"
                             @change="(e) => {newEnd3.existingSplitter = e.value}"/>

        <div class="text-center py-3">Либо укажите новый сплиттер или райзер</div>
      </div>

      <!-- Выбор сплиттера или райзера -->
      <div class="">
        <div class="py-3 flex gap-4 justify-center">
          <div>
            <RadioButton v-model="newEnd3.type" input-id="splitter" value="splitter"/>
            <label for="splitter" class="ml-2 cursor-pointer">Сплиттер</label>
          </div>
          <div>
            <RadioButton v-model="newEnd3.type" input-id="rizer" value="rizer"/>
            <label for="rizer" class="ml-2 cursor-pointer">Райзер</label>
          </div>
        </div>

        <!-- Кол-во портов -->
        <div v-if="newEnd3.type==='splitter'">
          <div>
            <div class="flex gap-2 items-center p-2">
              Количество портов на сплиттере
              <Asterisk/>
            </div>
            <Select v-model="newEnd3.portCount" :options="[4, 8, 12, 16, 24]" fluid/>
          </div>
        </div>

        <!-- Кол-во волокон -->
        <div v-if="newEnd3.type==='rizer'">
          <div>
            <div class="flex gap-2 items-center p-2">Количество волокон на райзере
              <Asterisk/>
            </div>
            <Select v-model="newEnd3.portCount" :options="[4, 8, 12, 16, 24]" fluid/>
            <Button @click="showRizerColors=true" severity="primary" outlined rounded size="small"
                    icon="pi pi-palette" class="my-2" label="Посмотреть цвета"/>
          </div>

          <!-- Окно для отображения цветов волокон -->
          <Dialog v-model:visible="showRizerColors">
            <RizerFiberColorExample v-if="newEnd3.type==='rizer'" :count="newEnd3.portCount"/>
          </Dialog>

        </div>
      </div>

      <End3AddForm :initial="newEnd3.list" :end3-type="newEnd3.type"/>

      <!-- ОТПРАВИТЬ EVENT НА СОХРАНЕНИЕ ДАННЫХ -->
      <div class="pt-5 text-right">
        <Button @click="sendEventToCreateEnd3" severity="success" text>
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
            <path
                d="M12.5 16a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm.5-5v1h1a.5.5 0 0 1 0 1h-1v1a.5.5 0 0 1-1 0v-1h-1a.5.5 0 0 1 0-1h1v-1a.5.5 0 0 1 1 0Z"/>
            <path
                d="M12.096 6.223A4.92 4.92 0 0 0 13 5.698V7c0 .289-.213.654-.753 1.007a4.493 4.493 0 0 1 1.753.25V4c0-1.007-.875-1.755-1.904-2.223C11.022 1.289 9.573 1 8 1s-3.022.289-4.096.777C2.875 2.245 2 2.993 2 4v9c0 1.007.875 1.755 1.904 2.223C4.978 15.71 6.427 16 8 16c.536 0 1.058-.034 1.555-.097a4.525 4.525 0 0 1-.813-.927C8.5 14.992 8.252 15 8 15c-1.464 0-2.766-.27-3.682-.687C3.356 13.875 3 13.373 3 13v-1.302c.271.202.58.378.904.525C4.978 12.71 6.427 13 8 13h.027a4.552 4.552 0 0 1 0-1H8c-1.464 0-2.766-.27-3.682-.687C3.356 10.875 3 10.373 3 10V8.698c.271.202.58.378.904.525C4.978 9.71 6.427 10 8 10c.262 0 .52-.008.774-.024a4.525 4.525 0 0 1 1.102-1.132C9.298 8.944 8.666 9 8 9c-1.464 0-2.766-.27-3.682-.687C3.356 7.875 3 7.373 3 7V5.698c.271.202.58.378.904.525C4.978 6.711 6.427 7 8 7s3.022-.289 4.096-.777ZM3 4c0-.374.356-.875 1.318-1.313C5.234 2.271 6.536 2 8 2s2.766.27 3.682.687C12.644 3.125 13 3.627 13 4c0 .374-.356.875-1.318 1.313C10.766 5.729 9.464 6 8 6s-2.766-.27-3.682-.687C3.356 4.875 3 4.373 3 4Z"/>
          </svg>
          <span>Создать</span>
        </Button>
      </div>

    </Dialog>

  </div>

</template>

<script>
import ConfirmPopup from "primevue/confirmpopup";

import Asterisk from "./Asterisk.vue";
import SplittersRizersFind from "./SplittersRizersFind.vue";
import RizerFiberColorExample from "./RizerFiberColorExample.vue";
import End3AddForm from "./End3AddForm.vue";
import End3PortsViewEdit from "./End3PortsViewEdit.vue";
import TechCapabilityBadge from "./TechCapabilityBadge.vue";
import CreateSubscriberData from "../CreateSubscriberData.vue";

import api from "@/services/api";
import {formatAddress} from "@/formats";

export default {
  name: "End3CollapsedView",
  components: {
    Asterisk,
    ConfirmPopup,
    End3AddForm,
    End3PortsViewEdit,
    TechCapabilityBadge,
    RizerFiberColorExample,
    SplittersRizersFind,
    CreateSubscriberData,
  },
  props: {
    customerLines: {required: true, type: Array},
    userPermissions: {required: true, type: Array},
    deviceName: {required: false, default: null, type: String},
    devicePort: {required: false, default: null, type: String},
    buildingAddress: {required: false, default: null, type: Object},
    editMode: {required: false, default: false, type: Boolean},
  },

  data() {
    return {
      showAddNewEnd3Dialog: false,
      newEnd3: {
        type: this.customerLines.length ? this.customerLines[0].type : "splitter",
        existingSplitter: null,
        portCount: 4,
        list: [],
      },
      showRizerColors: false,
    }
  },

  computed: {
    hasPermissionToDeleteEnd3() {
      return this.userPermissions.includes("gpon.delete_end3")
    },
  },

  methods: {
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

    sendEventToCreateEnd3() {
      this.$emit('createNewEnd3', this.newEnd3)
      this.showAddNewEnd3Dialog = false
    },

    deleteEnd3(event, end3, end3Index) {
      const end3VerboseType = this.customerLineTypeName(end3.type)
      for (const end3Port of end3.detailInfo) {
        if (end3Port.subscribers.length > 0) {
          this.$toast.add({
            severity: 'warn',
            summary: 'Warning',
            detail: end3VerboseType + ' содержит абонентов',
            life: 3000
          });
          return
        }
      }

      this.$confirm.require({
        target: event.currentTarget,
        message: 'Вы уверены, что хотите удалить данный ' + end3VerboseType + "?",
        icon: 'pi pi-info-circle',
        acceptLabel: "Да",
        rejectLabel: "Нет",
        acceptClass: 'p-button-danger p-button-sm',
        defaultFocus: "reject",
        accept: () => {
          api.delete("/gpon/api/tech-data/end3/" + end3.id).then(
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
              reason => this.$toast.add({
                severity: 'error',
                summary: reason.response.status,
                detail: reason.response.data,
                life: 3000
              })
          )
        },
        reject: () => {
        }
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