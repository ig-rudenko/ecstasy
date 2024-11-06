<template>
  <div class="container" id="port-info">

    <div class="flex flex-wrap gap-3 items-center">
      <div>
        Всего <span class="px-2 rounded-full bg-primary text-white">{{ data.total_count }}</span>
      </div>
      <div>
        Online <span class="px-2 rounded-full bg-green-500 text-white">{{ data.online_count }}</span>
      </div>

      <Button v-if="showSubscribersData" @click="showSubscribersData=false"
              icon="pi pi-list" size="small" outlined label="Переключить на обычный вид"/>
      <Button v-else @click="getSubscribersData"
              outlined icon="pi pi-users" size="small" label="Переключить на просмотр абонентов"/>

    </div>

    <div class="flex justify-center">
      <table class="text-center w-full">
        <thead>
        <tr>
          <th scope="col" class="px-4 py-2">ONT ID</th>
          <th scope="col" class="px-4 py-2">Статус</th>
          <th scope="col" class="px-4 py-2">{{ showSubscribersData ? 'Абонент' : 'Equipment ID' }}</th>
          <th scope="col" class="px-4 py-2">{{ showSubscribersData ? 'Адрес' : 'RSSI [dBm]' }}</th>
          <th scope="col" class="px-4 py-2">{{ showSubscribersData ? 'Услуги' : 'Serial' }}</th>
          <th scope="col" class="px-4 py-2">{{ showSubscribersData ? 'Транзит' : 'Описание' }}</th>
        </tr>
        </thead>
        <tbody>

        <template v-for="line in data.onts_lines">
          <OLT_ONT_Detail_info
              @find-mac="findMacEvent"
              @session-mac="sessionEvent"
              :device-name="deviceName"
              :interface="interface"
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
import SubscribersData, {newSubscriberData} from "../subscribersData";
import {AxiosResponse} from "axios";
import {DeviceInterface, InterfaceComment} from "@/services/interfaces.ts";
import api from "@/services/api";

type ontData = {
  total_count: number,
  online_count: number,
  onts_lines: string[][]
}

export default defineComponent({
  components: {
    OLT_ONT_Detail_info,
  },
  props: {
    deviceName: {required: true, type: String},
    permissionLevel: {required: true, type: Number},
    data: {required: true, type: Object as PropType<ontData>},
    interface: {required: true, type: Object as PropType<DeviceInterface>},
  },

  emits: ["find-mac", "session-mac"],

  data() {
    return {
      showDetailInfo: false,
      showSubscribersData: false,
      subscribersData: {} as { number?: SubscribersData[] } | any,
    }
  },

  methods: {

    getSubscribersData() {
      if (this.isEmpty(this.subscribersData)) {
        api.get("/gpon/api/subscribers-on-device/" + this.deviceName + "?port=" + this.interface.name)
            .then(
                (resp: AxiosResponse<any[]>) => {
                  this.addSubscribersData(resp.data)
                  this.showSubscribersData = true;
                })
            .catch(reason => {
              console.log(reason.response)
            })
      } else {
        this.showSubscribersData = true;
      }
    },

    addSubscribersData(subscribersData: any[]) {
      this.subscribersData = {}
      for (let sub of subscribersData) {
        if (!this.subscribersData[sub.ont_id]) {
          this.subscribersData[sub.ont_id] = []
        }
        this.subscribersData[sub.ont_id].push(newSubscriberData(sub))
      }
    },

    findMacEvent(mac: string) {
      this.$emit("find-mac", mac)
    },
    sessionEvent(mac: string, port: string) {
      this.$emit("session-mac", mac, port)
    },

    isEmpty(obj: any): boolean {
      for (let prop in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, prop)) {
          return false;
        }
      }
      return true
    }

  }
})
</script>