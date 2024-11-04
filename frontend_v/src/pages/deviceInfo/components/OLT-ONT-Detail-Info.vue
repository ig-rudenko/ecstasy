<template>

  <tr :style="lineStyle(line[1])" :class="lineClasses">
    <!--        ONT ID-->
    <td class="btn-fog" style="text-align: right">

      <div class="btn-group" role="group">

        <Comment :interface="ontInterface" :register-comment-action="registerCommentAction"/>
        <!--        Название Интерфейса-->
        <div @click="toggleDetailInfo" class="col-auto blockquote" style="margin: 5px 10px; cursor:pointer;">
              <span class="position-relative">
                    {{ line[0] }}
              </span>

        </div>

        <!--        Управление состоянием интерфейсов-->
        <PortControlButtons
            :port-action="registerInterfaceAction"
            :interface="ontInterface"
            :permission-level="permissionLevel"/>

        <!--        Посмотреть порт -->
        <button @click="toggleDetailInfo" class="btn btn-group" style="padding: 6px 6px 2px 6px">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box"
               viewBox="0 0 16 16">
            <path
                d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"></path>
          </svg>
        </button>

      </div>
    </td>

    <td :style="statusStyles(line[1])">
      {{ line[1] }}
    </td>

    <!--            Equipment ID или АБОНЕНТ -->
    <td v-if="showSubscribersData">
      <div v-for="customer in getCustomersIDAndFullNameList(Number(line[0]))">
        <a :href="'/gpon/subscriber-data/customers/'+customer.id" target="_blank">{{ customer.fullName }}</a>
      </div>
    </td>
    <td v-else>{{ line[2] }}</td>

    <!--            RSSI [dBm] или АДРЕС -->
    <td v-if="showSubscribersData">
      <div v-for="address in getCustomersAddressList(Number(line[0]))">{{ address }}</div>
    </td>
    <td v-else>{{ line[3] }}</td>

    <!--            Serial или УСЛУГИ -->
    <td v-if="showSubscribersData">
      <div v-for="services in getCustomersServicesList(Number(line[0]))">{{ services }}</div>
    </td>
    <td v-else>{{ line[4] }}</td>

    <!--            Description или ТРАНЗИТ -->
    <td v-if="showSubscribersData">
      <div v-for="transit in getCustomersTransitList(Number(line[0]))">{{ transit }}</div>
    </td>
    <td v-else style="text-align: left">{{ line[5] }}</td>

  </tr>


  <tr v-if="showDetailInfo">
    <td colspan="6">

      <!--      DETAIL PORT INFO  -->
      <div v-if="complexInfo?.portDetailInfo" class="container row py-3">
        <div v-if="complexInfo.portDetailInfo.type==='html'" class="card shadow py-3"
             v-html="complexInfo.portDetailInfo.data"></div>
      </div>


      <!--      ANOTHER INFO  -->
      <div class="container row py-3">

        <div class="col-auto">

          <!--        BUTTON-->
          <!--        Конфигурация порта-->
          <div v-if="complexInfo?.portConfig">
            <button type="button" @click="portDetailMenu=portDetailMenu==='portConfig'?'':'portConfig'"
                    :class="portDetailMenu==='portConfig'?['btn', 'active']:['btn']">
              <svg class="bi me-2" width="16" height="16" role="img">
                <use xlink:href="#gear-icon"></use>
              </svg>
              Конфигурация порта
            </button>
          </div>

          <!--        BUTTON-->
          <!--        Ошибки на порту-->
          <div v-if="complexInfo?.portErrors">
            <button type="button" @click="portDetailMenu=portDetailMenu==='portErrors'?'':'portErrors'"
                    :class="portDetailMenu==='portErrors'?['btn', 'active']:['btn']">
              <svg class="bi me-2" width="16" height="16" role="img">
                <use xlink:href="#warning-icon"></use>
              </svg>
              Ошибки на порту
            </button>
          </div>
        </div>

        <!--      Конфигурация порта -->
        <div v-show="portDetailMenu==='portConfig'" class="col-md">

          <div v-if="complexInfo?.portConfig" class="card shadow" style="padding: 2rem; text-align: left">
            <span v-html="formatToHtml(complexInfo.portConfig)" style="font-family: monospace"></span>
          </div>

          <div v-else class="d-flex justify-content-center">
            <div class="spinner-border" role="status"></div>
          </div>
        </div>

        <!--      Ошибки на порту -->
        <div v-show="portDetailMenu==='portErrors'" class="col-md">

          <div v-if="complexInfo?.portErrors" class="card shadow" style="padding: 2rem;">
            <span v-html="formatToHtml(complexInfo.portErrors)" style="font-family: monospace"></span>
          </div>

          <div v-else class="d-flex justify-content-center">
            <div class="spinner-border" role="status"></div>
          </div>

        </div>

      </div>


      <!--      МАС-->
      <div v-if="MACs.length > 0" class="container">
        <span>Всего: {{ MACs.length }}</span>

        <div class="table-responsive-lg">
          <table class="table">
            <thead>
            <tr>
              <th></th>
              <th scope="col">VLAN</th>
              <th scope="col">MAC</th>
              <th></th>
            </tr>
            </thead>
            <tbody id="tbody-macs">

            <tr v-for="mac in MACs">
              <td></td>

              <td style="font-family: monospace; font-size: x-large;">
                    <span :title="mac[2]" style="cursor: help; font-family: monospace;">
                        {{ mac[0] }}
                    </span>
              </td>

              <td class="mac-line" style="font-family: monospace; font-size: x-large;">
                    <span @click="findMacEvent(mac[1])" class="nowrap" style="cursor: pointer; font-family: monospace;"
                          title="Поиск MAC" data-bs-toggle="modal" data-bs-target="#modal-find-mac">
                        {{ mac[1] }}
                        <svg class="bi me-2" width="24" height="24" role="img"><use
                            xlink:href="#search-icon"></use></svg>
                    </span>
              </td>

              <td>
                <button @click="sessionEvent(mac[1], ontInterface.name)" type="button" class="btn btn-outline-primary"
                        data-bs-toggle="modal" data-bs-target="#bras-session-modal">
                  BRAS
                </button>
              </td>
            </tr>

            </tbody>
          </table>
        </div>

      </div>

      <div v-else-if="MACs.length == 0" class="container">
        <h3 class="text-center" style="padding-bottom: 40px;">Нет MAC</h3>
      </div>

      <div v-else class="d-flex justify-content-center" style="padding: 2.2rem;">
        <div class="spinner-border" role="status"></div>
      </div>

    </td>
  </tr>

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import PortControlButtons from "./PortControlButtons.vue";

import SubscribersData from "../subscribersData";
import api from "@/services/api";
import {AxiosResponse} from "axios";
import {ComplexInterfaceInfo} from "../detailInterfaceInfo";
import Comment from "../../../components/Comment.vue";
import {DeviceInterface, InterfaceComment} from "@/services/interfaces.ts";
import {Address} from "@/types/address.ts";
import {formatAddress} from "@/formats.ts";
import {Customer} from "@/types/customer.ts";

export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    interface: {required: true, type: Object as PropType<DeviceInterface>},
    line: {required: true, type: [] as PropType<any[]>},
    permissionLevel: {required: true, type: Number},
    registerCommentAction: {
      required: true,
      type: Function as PropType<(action: ("add" | "update" | "delete"), comment: InterfaceComment, interfaceName: string) => void>
    },
    registerInterfaceAction: {
      required: true,
      type: Function as PropType<(action: ("up" | "down" | "reload"), port: string, description: string) => void>
    },
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
      complexInfo: null as ComplexInterfaceInfo | null,
    }
  },

  components: {
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

    findMacEvent(mac: string) {
      this.$emit("find-mac", mac)
    },
    sessionEvent(mac: string, port: string) {
      this.$emit("session-mac", mac, port)
    },

    statusStyles(status: string): any {
      if (status === "OK") return {"background-color": "#22e58b"}
      if (status === "OFFLINE") return {"background-color": "#ffcacf"}
      return "UNKNOWN"
    },
    lineStyle(status: string): any {
      if (status === "OFFLINE") return {"background-color": "#ffcacf"}
      if (this.showDetailInfo) return {"background-color": "#e8efff", "top": "56px"}
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

      api.get("/device/api/" + this.deviceName + "/interface-info?port=" + this.ontInterface.name)
          .then(
              (value: AxiosResponse<ComplexInterfaceInfo>) => {
                this.complexInfo = value.data;
              },
          )
    },

  }

})
</script>