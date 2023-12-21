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

<script>
import {defineComponent} from "vue";
import OLT_ONT_Detail_info from "./OLT-ONT-Detail-Info.vue"
import api_request from "../api_request";

export default defineComponent({
  props: {
    permissionLevel: {required: true, type: Number},
    registerInterfaceAction: {required: true, type: Function},
    data: {
      required: true,
      type: {
        total_count: Number,
        online_count: Number,
        onts_lines: []
      }
    },
    interface: {required: true, type: Object}
  },

  data() {
    return {
      showDetailInfo: false,
      showSubscribersData: false,
      subscribersData: null,
      deviceName: document.deviceName,
    }
  },

  components: {
    OLT_ONT_Detail_info,
  },

  methods: {

    getSubscribersData() {
      if (!this.subscribersData) {
        api_request.get("/gpon/api/subscribers-on-device/"+this.deviceName+"?port="+this.interface.Interface)
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

    findMacEvent: function (mac) { this.$emit("find-mac", mac) },
    sessionEvent: function (mac, port) { this.$emit("session-mac", mac, port) },

  }
})
</script>