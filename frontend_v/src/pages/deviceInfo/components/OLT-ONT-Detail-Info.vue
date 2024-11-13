<template>
  <tr :style="lineStyle(line[1])" :class="lineClasses">
    <!--        ONT ID-->
    <td class="btn-fog" style="text-align: right">

      <div class="flex items-center justify-end">

        <Comment :interface="ontInterface" :device-name="deviceName"/>
        <!--        Название Интерфейса-->
        <div @click="toggleDetailInfo" class="text-xl font-mono text-center px-4">{{ line[0] }}</div>

        <!--        Управление состоянием интерфейсов-->
        <PortControlButtons
            :device-name="deviceName"
            :interface="ontInterface"
            :permission-level="permissionLevel"/>

        <!--        Посмотреть порт -->
        <Button @click="toggleDetailInfo" text>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box"
               viewBox="0 0 16 16">
            <path
                d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"></path>
          </svg>
        </Button>

      </div>
    </td>

    <td :style="statusStyles(line[1])" class="font-mono">
      {{ line[1] }}
    </td>

    <!--            Equipment ID или АБОНЕНТ `Subscriber` -->
    <td v-if="showSubscribersData">
      <div v-for="customer in getCustomersIDAndFullNameList(Number(line[0]))">
        <router-link :to="{ name: 'gpon-view-subscriber', params: { id: customer.id } }" target="_blank">
          <Button text size="small" class="w-full" icon="pi pi-user" :label="customer.fullName"/>
        </router-link>
      </div>
    </td>
    <td v-else class="font-mono">{{ line[2] }}</td>

    <!--            RSSI [dBm] или АДРЕС -->
    <td v-if="showSubscribersData" class="px-3">
      <div v-for="address in getCustomersAddressList(Number(line[0]))">{{ address }}</div>
    </td>
    <td v-else class="font-mono px-3">{{ line[3] }}</td>

    <!--            Serial или УСЛУГИ -->
    <td v-if="showSubscribersData" class="font-mono px-3">
      <div v-for="services in getCustomersServicesList(Number(line[0]))">{{ services }}</div>
    </td>
    <td v-else class="font-mono px-3">{{ line[4] }}</td>

    <!--            Description или ТРАНЗИТ -->
    <td v-if="showSubscribersData" class="font-mono px-3">
      <div v-for="transit in getCustomersTransitList(Number(line[0]))">{{ transit }}</div>
    </td>
    <td v-else class="font-mono px-3" style="text-align: left">{{ line[5] }}</td>

  </tr>


  <tr v-if="showDetailInfo">
    <td colspan="6">

      <!--      DETAIL PORT INFO  -->
      <div v-if="complexInfo?.portDetailInfo" class="p-3">
        <div v-if="complexInfo.portDetailInfo.type==='html'" class="shadow py-3"
             v-html="complexInfo.portDetailInfo.data"></div>
      </div>

      <!--      ANOTHER INFO  -->
      <ComplexInterfaceInfo v-if="complexInfo" :complex-info="complexInfo" :interface="interface"
                            :device-name="deviceName"/>

    </td>
  </tr>

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import {AxiosResponse} from "axios";

import Comment from "@/components/Comment.vue";
import PortControlButtons from "./PortControlButtons.vue";
import ComplexInterfaceInfo from "@/pages/deviceInfo/components/ComplexInterfaceInfo.vue";

import api from "@/services/api";
import {Address} from "@/types/address";
import {formatAddress} from "@/formats";
import {Customer} from "@/types/customer";
import SubscribersData from "../subscribersData";
import {DeviceInterface} from "@/services/interfaces";
import {ComplexInterfaceInfoType} from "../detailInterfaceInfo";

export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    interface: {required: true, type: Object as PropType<DeviceInterface>},
    line: {required: true, type: [] as PropType<any[]>},
    permissionLevel: {required: true, type: Number},
    showSubscribersData: {required: false, type: Boolean},
    subscribersData: {
      required: false,
      type: Object as PropType<SubscribersData[][]>,
      default: {}
    },
  },

  emits: ["find-mac", "session-mac"],

  data() {
    return {
      showDetailInfo: false,
      ontID: this.line[0],
      status: this.line[1],
      equipmentID: this.line[2],
      rssi: this.line[3],
      serialNumber: this.line[4],
      description: this.line[5],
      MACs: this.line[6],
      comments: this.line[7],

      portDetailMenu: "" as "" | "portConfig" | "portErrors",
      complexInfo: null as ComplexInterfaceInfoType | null,
    }
  },

  components: {
    ComplexInterfaceInfo,
    Comment,
    PortControlButtons,
  },

  computed: {
    ontInterface(): DeviceInterface {
      return {
        name: this.interface.name + "/" + this.ontID,
        status: this.line[1],
        description: "ONT: " + this.ontID + " " + this.interface.description,
        vlans: [],
        comments: this.comments
      }
    },
    lineClasses() {
      if (this.showDetailInfo) return ["shadow", "sticky-top"];
      return []
    },
  },

  methods: {

    getCustomersIDAndFullNameList(ontID: number): { id: number, fullName: string }[] {
      let result: { id: number, fullName: string }[] = []
      if (this.subscribersData[ontID]) {
        console.log(this.subscribersData)
        for (const subscriberData of this.subscribersData[ontID]) {
          const c: Customer = subscriberData.customer
          if (c.companyName && c.companyName.length) {
            result.push({id: c.id, fullName: c.companyName})
          } else {
            result.push({id: c.id, fullName: c.surname + " " + c.firstName + " " + c.lastName})
          }
        }
      }
      return result
    },

    getCustomersAddressList(ontID: number): string[] {
      let result: string[] = []
      if (this.subscribersData[ontID]) {
        for (const subscriberData of this.subscribersData[ontID]) {
          const address: Address = subscriberData.address
          let address_string = formatAddress(address)
          if (address.apartment) {
            address_string += ` кв. ${address.apartment}`
          }
          if (address.floor) {
            address_string += ` (${address.floor} этаж)`
          }
          result.push(address_string)
        }
      }
      return result
    },

    getCustomersServicesList(ontID: number): string[] {
      let result: string[] = []
      if (this.subscribersData[ontID]) {
        for (const subscriberData of this.subscribersData[ontID]) {
          result.push(subscriberData.services.join(", "))
        }
      }
      return result
    },

    getCustomersTransitList(ontID: number): string[] {
      let result: string[] = []
      if (this.subscribersData[ontID]) {
        for (const subscriberData of this.subscribersData[ontID]) {
          result.push(subscriberData.transit.toString())
        }
      }
      return result
    },

    statusStyles(status: string): any {
      if (status === "OK") return {"background-color": "#22e58b"}
      if (status === "OFFLINE") return {"background-color": "#ffcacf"}
      return "UNKNOWN"
    },
    lineStyle(status: string): any {
      if (status.toLowerCase() === "offline") return {"background-color": "rgba(255,138,148,0.5)"}
      if (this.showDetailInfo) return {"background-color": "rgba(232,239,255,0.5)", "top": "56px"}
    },
    formatToHtml(str: string): string {
      let space_re = new RegExp(' ', 'g');
      let n_re = new RegExp('\n', 'g');
      str = str.replace(space_re, '&nbsp;').replace(n_re, '<br>')
      return str
    },

    toggleDetailInfo() {
      this.showDetailInfo = !this.showDetailInfo
      if (!this.showDetailInfo) return
      this.getDetailInfo()
    },

    getDetailInfo() {
      if (!this.showDetailInfo) return

      api.get("/api/v1/devices/" + this.deviceName + "/interface-info?port=" + this.ontInterface.name)
          .then(
              (value: AxiosResponse<ComplexInterfaceInfoType>) => {
                this.complexInfo = value.data;
              },
          )
    },

  }

})
</script>