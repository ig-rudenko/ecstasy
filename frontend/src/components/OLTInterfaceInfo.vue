<template>
<div class="container" id="port-info">
    <button type="button" class="btn btn">
      Всего <span class="badge text-bg-primary">{{ data.total_count }}</span>
    </button>

    <button type="button" class="btn me-3">
      Online <span class="badge text-bg-success">{{ data.online_count }}</span>
    </button>

    <button v-if="showSubscribersData" @click="showSubscribersData=false" type="button" class="btn btn-outline-secondary">
      Переключить на обычный вид
    </button>
    <button v-else @click="getSubscribersData" type="button" class="btn btn-outline-primary">
      Переключить на просмотр абонентов
    </button>

<br><br>

<div class="table-responsive-lg">
    <table class="table" style="text-align: center">
      <thead>
        <tr>
          <th scope="col">ONT ID</th>
          <th scope="col">Статус</th>
          <th scope="col">{{ showSubscribersData?'Абонент':'Equipment ID' }}</th>
          <th scope="col">{{ showSubscribersData?'Адрес':'RSSI [dBm]' }}</th>
          <th scope="col">{{ showSubscribersData?'Услуги':'Serial' }}</th>
          <th scope="col">{{ showSubscribersData?'Транзит':'Описание' }}</th>
        </tr>
      </thead>
      <tbody>

        <template v-for="line in data.onts_lines">
          <OLT_ONT_Detail_info
              @find-mac="findMacEvent"
              @session-mac="sessionEvent"
              :interface="interface"
              :register-interface-action="registerInterfaceAction"
              :permission-level="permissionLevel"
              :line="line"
              :show-subscribers-data="showSubscribersData"
              :subscribers-data="subscribersData"
          />
        </template>

      </tbody>
    </table>
</div>
</div>

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import OLT_ONT_Detail_info from "./OLT-ONT-Detail-Info.vue"
import api_request from "../api_request";
import Interface from "../types/interfaces";

type ontData = {
  total_count: number,
  online_count: number,
  onts_lines: any[]
}

export default defineComponent({
  components: {
    OLT_ONT_Detail_info,
  },
  props: {
    deviceName: {required: true, type: String},
    permissionLevel: {required: true, type: Number},
    data: {required: true, type: Object as PropType<ontData> },
    interface: {required: true, type: Object as PropType<Interface>},
    registerInterfaceAction: {
      required: true,
      type: Function as PropType<(action:("up"|"down"|"reload"), port: string, description: string) => void>
    }
  },

  emits: ["find-mac", "session-mac"],

  data() {
    return {
      showDetailInfo: false,
      showSubscribersData: false,
      subscribersData: {},
    }
  },

  methods: {

    getSubscribersData() {
      if (!this.subscribersData) {
        api_request.get("/gpon/api/subscribers-on-device/"+this.deviceName+"?port="+this.interface.name)
            .then(resp => {
              this.showSubscribersData = true;
              this.addSubscribersData(resp.data)
            })
            .catch(reason => {console.log(reason.response)})
      } else {
        this.showSubscribersData = true;
      }
    },

    addSubscribersData(subscribersData) {
      this.subscribersData = {}
      for (let sub of subscribersData) {
        if (!this.subscribersData[sub.ont_id]) {
          this.subscribersData[sub.ont_id] = []
        }
        this.subscribersData[sub.ont_id].push(sub)
      }
    },

    findMacEvent(mac: string) { this.$emit("find-mac", mac) },
    sessionEvent(mac: string, port: string) { this.$emit("session-mac", mac, port) },

  }
})
</script>