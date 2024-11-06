<template>

  <tr :style="interfaceStyles" :class="interfaceClasses">

    <td>

      <div class="flex gap-1">
        <!--       COMMENTS-->
        <Comment :interface="interface" :device-name="deviceName" :allow-edit="true" />

        <!-- Ссылка на графики в Zabbix -->
        <GraphsLink :interface="interface"/>
      </div>

    </td>

    <!--ПОРТ-->
    <td class="btn-fog" style="text-align: right">

      <div class="flex items-center">

        <!--Название Интерфейса-->
        <div @click="toggleDetailInfo" class="font-mono cursor-pointer">
          <span class="px-1 rounded text-gray-200" :style="portTypeStyles">
            <span v-if="complexInfo">{{ complexInfo.portType }}</span>
          </span>
          <span class="px-8 text-xl">{{ interface.name }}</span>
        </div>

        <!--Управление состоянием интерфейсов-->
        <PortControlButtons
            :interface="interface"
            :device-name="deviceName"
            :permission-level="permissionLevel"/>

        <!--Посмотреть порт -->
        <Button @click="toggleDetailInfo" text>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box"
               viewBox="0 0 16 16">
            <path d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"></path>
          </svg>
        </Button>

      </div>
    </td>

    <!--Статус порта-->
    <td :style="statusStyle(interface.status)" class="text-gray-950 text-nowrap px-3">
      <span>{{ formatStatus(interface.status) }}</span>
    </td>

    <!--Описание порта-->
    <td>
      <ChangeDescription :device-name="deviceName" :interface="interface"/>
    </td>

    <!--VLANS-->
    <td v-if="interface.vlans.length" @click="toggleVlansList" class="cursor-pointer text-nowrap overflow-x-visible max-w-20">
      {{ compressVlanRange }}
    </td>
    <td v-else></td>

  </tr>

  <tr v-if="showDetailInfo">

    <td v-if="complexInfo" colspan="5">

      <!--      DETAIL PORT INFO  -->
      <div v-if="complexInfo.portDetailInfo" class="container py-3">

        <div class="text-end">
          <span v-if="collectingDetailInfo" class="text-muted-color text-help" style="cursor: default">Обновляю...</span>
          <span v-else @click="getDetailInfo" class="text-muted-color text-help" style="cursor: pointer">Обновить</span>
        </div>

        <div v-if="complexInfo.portDetailInfo.type==='html'" class="p-3 border rounded shadow py-3"
             v-html="complexInfo.portDetailInfo.data"></div>
        <div v-else-if="complexInfo.portDetailInfo.type==='text'" class="p-3 border rounded shadow py-3 font-mono"
             v-html="formatToHtml(complexInfo.portDetailInfo.data)"></div>

        <!--      MIKROTIK -->
        <div v-else-if="complexInfo.portDetailInfo.type==='mikrotik'" class="p-3 border rounded shadow py-3">
          <MikrotikInterfaceInfo :device-name="deviceName" :data="complexInfo.portDetailInfo.data"
                                 :interface="interface"/>
        </div>

        <!--      ADSL -->
        <div v-else-if="complexInfo.portDetailInfo.type==='adsl'" class="p-3 border rounded shadow py-3">
          <ADSLInterfaceInfo :device-name="deviceName" :data="complexInfo.portDetailInfo.data" :interface="interface"/>
        </div>

        <!--      GPON -->
        <div v-else-if="complexInfo.portDetailInfo.type==='gpon'" class="p-3 border rounded shadow py-3">
          <GPONInterfaceInfo
              @session-mac="sessionEvent"
              :device-name="deviceName"
              :gpon-data="complexInfo.portDetailInfo.data"
              :permission-level="permissionLevel"
              :register-comment-action="() => {}"
              :register-interface-action="() => {}"
              :interface="interface"/>
        </div>

        <!--      ELTEX OLT -->
        <div v-else-if="complexInfo.portDetailInfo.type==='eltex-gpon'" class="p-3 border rounded shadow py-3">
          <OLTInterfaceInfo
              @session-mac="sessionEvent"
              :device-name="deviceName"
              :data="complexInfo.portDetailInfo.data"
              :permission-level="permissionLevel"
              :register-comment-action="() => {}"
              :register-interface-action="() => {}"
              :interface="interface"/>
        </div>

      </div>

      <!--      ANOTHER INFO  -->
      <div v-if="complexInfo" class="container row py-3">

        <div class="flex flex-wrap gap-1">
          <!--        BUTTON-->
          <!--        Конфигурация порта-->
          <div v-if="complexInfo.portConfig.length">
            <Button severity="primary" size="small" @click="portDetailMenu=portDetailMenu=='portConfig'?'':'portConfig'"
                    :outlined="portDetailMenu!=='portConfig'">
              <svg width="16" height="16" role="img">
                <use xlink:href="#gear-icon"></use>
              </svg>
              Конфигурация порта
            </Button>
          </div>

          <!--        BUTTON-->
          <!--        Ошибки на порту-->
          <div v-if="complexInfo.portErrors.length">
            <Button severity="primary" size="small" @click="portDetailMenu=portDetailMenu=='portErrors'?'':'portErrors'"
                    :outlined="portDetailMenu!=='portErrors'">
              <svg width="16" height="16" role="img">
                <use xlink:href="#warning-icon"></use>
              </svg>
              Ошибки на порту
            </Button>
          </div>

          <!--        BUTTON-->
          <!--        Диагностика кабеля-->
          <div v-if="complexInfo.hasCableDiag">
            <Button severity="primary" size="small" @click="portDetailMenu=portDetailMenu=='cableDiag'?'':'cableDiag'"
                    :outlined="portDetailMenu!=='cableDiag'">
              <svg width="16" height="16">
                <use xlink:href="#cable-diag-icon"></use>
              </svg>
              Диагностика кабеля
            </Button>
          </div>
        </div>


        <!--      Конфигурация порта -->
        <div v-show="portDetailMenu==='portConfig'">

          <div v-if="complexInfo.portConfig.length>0" class="p-4 m-2 border rounded shadow font-mono">
            <span v-html="formatToHtml(complexInfo.portConfig)"></span>
          </div>

          <div v-else class="d-flex justify-content-center">
            <div class="spinner-border" role="status"></div>
          </div>
        </div>

        <!--      Ошибки на порту -->
        <div v-show="portDetailMenu==='portErrors'">

          <div v-if="complexInfo.portErrors.length>0" class="p-4 m-2 border rounded shadow font-mono">
            <span v-html="formatToHtml(complexInfo.portErrors)"></span>
          </div>

          <div v-else class="d-flex justify-content-center">
            <div class="spinner-border" role="status"></div>
          </div>

        </div>

        <!--      Диагностика кабеля -->
        <div v-show="portDetailMenu==='cableDiag'">

          <div v-if="complexInfo.hasCableDiag" class="px-4 m-2 border rounded shadow">
            <CableDiag :device-name="deviceName" :port="interface.name"/>
          </div>

        </div>
      </div>


      <!--      МАС-->
      <div v-if="MACs.length > 0" class="container">
        <span>Всего: {{ MACs.length }}</span>

        <div>
          <div class="text-end">
            <span v-if="collectingMACs" class="text-muted text-help" style="cursor: default">Обновляю...</span>
            <span v-else @click="getMacs" class="text-muted text-help" style="cursor: pointer">Обновить</span>
          </div>

          <div class="flex flex-wrap gap-4 font-mono">
            <div v-for="row in macsUniqueVLANs" class="flex items-center gap-1">
              <div>v {{row[0]}}:</div>
              <div class="bg-indigo-500 text-gray-200 px-2 rounded-full text-center">{{row[1]}}</div>
            </div>
          </div>

          <div class="flex justify-center pb-10">
            <DataTable :value="MACs"
                       class="w-fit self-center"
                       :paginator="MACs.length>10" :rows="10" paginator-position="both">
              <Column field="vlanID">
                <template #body="{data}">
                  <div class="font-mono text-xl cursor-pointer" v-tooltip.left="data.vlanName.toString()">{{data.vlanID}}</div>
                </template>
              </Column>
              <Column field="mac">
                <template #body="{data}">
                  <div class="font-mono text-xl cursor-pointer" @click="macSearch(data.mac)" >{{data.mac}}</div>
                </template>
              </Column>
              <Column field="mac">
                <template #body>
                  <Button size="small" text label="BRAS"></Button>
                </template>
              </Column>
            </DataTable>
          </div>

        </div>

      </div>

      <div v-else-if="MACs.length === 0" class="container">
        <div class="text-end">
          <span v-if="collectingMACs" class="text-muted text-help">Обновляю...</span>
          <span v-else @click="getMacs" class="text-muted text-help" style="cursor: pointer">Обновить</span>
        </div>
        <div class="text-2xl text-center" style="padding-bottom: 40px;">Нет MAC</div>
      </div>

      <div v-else class="d-flex justify-content-center" style="padding: 2.2rem;">
        <div class="spinner-border" role="status"></div>
      </div>

    </td>

    <td v-else colspan="5">
      <div class="flex justify-center" >
        <ProgressSpinner />
      </div>
    </td>
  </tr>

  <!--  VLANS FULL LIST-->
  <Popover ref="vlansList">
    <div>{{ compressVlanRange }}</div>
  </Popover>

</template>


<script lang="ts">
import {defineComponent, PropType} from "vue";
import {AxiosResponse} from "axios";

import PortControlButtons from "./PortControlButtons.vue";
import ChangeDescription from "./ChangeDescription.vue";
import Comment from "@/components/Comment.vue";
import CableDiag from "./CableDiag.vue";
import ADSLInterfaceInfo from "./xDSLInterfaceInfo.vue";
import GPONInterfaceInfo from "./GPONInterfaceInfo.vue";
import OLTInterfaceInfo from "./OLTInterfaceInfo.vue";
import MikrotikInterfaceInfo from "./MikrotikInterfaceInfo.vue";
import GraphsLink from "./GraphsLink.vue";

import api from "@/services/api";
import {ComplexInterfaceInfo} from "../detailInterfaceInfo";
import {DeviceInterface} from "@/services/interfaces";
import MacInfo from "@/pages/deviceInfo/mac";
import macSearch from "@/services/macSearch";

export default defineComponent({
  components: {
    GraphsLink,
    ChangeDescription,
    PortControlButtons,
    Comment,
    CableDiag,
    ADSLInterfaceInfo,
    GPONInterfaceInfo,
    OLTInterfaceInfo,
    MikrotikInterfaceInfo,
  },

  emits: ["toast", "session-mac"],

  props: {
    deviceName: {required: true, type: String},
    interface: {required: true, type: Object as PropType<DeviceInterface>},
    permissionLevel: {required: true, type: Number},
    dynamicOpacity: {required: true, type: Object as PropType<{ opacity: Number }>},
  },

  data() {
    return {
      showDetailInfo: false,
      portDetailMenu: "" as ("" | "portConfig" | "portErrors" | "cableDiag"),
      MACs: [] as MacInfo[],
      collectingMACs: false,

      complexInfo: null as ComplexInterfaceInfo | null,
      collectingDetailInfo: false,

    }
  },

  computed: {
    interfaceStyles(): any {
      return this.dynamicOpacity
    },
    interfaceClasses(): string[] {
      if (this.showDetailInfo) return ["shadow", "border", "sticky", "top-0", "bg-white", "dark:bg-gray-800"];
      return []
    },
    portTypeStyles() {
      let styles: any = {"font-size": "0.8rem"}

      if (!this.complexInfo?.portType) return styles;

      let type_: string = this.complexInfo.portType

      if (type_ === "COPPER") {
        styles["background-color"] = "#b87333"
      } else if (type_ === "SFP") {
        styles["background-color"] = "#3e6cff"
      } else if (type_.includes("COMBO")) {
        styles["background-color"] = "#8133b8"
      } else if (type_ === "WIRELESS") {
        styles["background-color"] = "#00c191"
      }
      return styles
    },

    macsUniqueVLANs() {
      const result = new Map()
      for (const mac of this.MACs) {
        result.set(mac.vlanID, (result.get(mac.vlanID) || 1) + 1)
      }
      return result
    },

    compressVlanRange(): string {
      const list = this.interface.vlans;

      if (!list || !list.length) return "";

      // сортируем список по возрастанию
      list.sort((a: number, b: number) => a - b);
      // инициализируем пустую строку для результата
      let result = "";
      // инициализируем начальное и конечное значение диапазона
      let start = list[0];
      let end = list[0];
      // проходим по списку, начиная со второго элемента
      for (let i = 1; i < list.length; i++) {
        // если текущий элемент на единицу больше предыдущего, то продолжаем диапазон
        if (list[i] === end + 1) {
          end = list[i];
        } else {
          // иначе, добавляем текущий диапазон к результату
          result += start === end ? start + ", " : start + "-" + end + ", ";
          // и обновляем начальное и конечное значение диапазона
          start = list[i];
          end = list[i];
        }
      }
      // добавляем последний диапазон к результату
      result += start === end ? start : start + "-" + end;
      // возвращаем результат
      return result;
    },

  },

  methods: {
    macSearch(mac: string) {
      macSearch.searchMac(mac)
    },

    sessionEvent(mac: string, port: string) {
      this.$emit("session-mac", mac, port)
    },

    formatToHtml(str: string): string {
      let space_re = new RegExp(' ', 'g');
      let n_re = new RegExp('\n', 'g');
      str = str.replace(space_re, '&nbsp;').replace(n_re, '<br>')
      return str
    },

    formatStatus(status: string): string {
      if (status === "dormant") return "activating..."
      return status
    },

    toggleDetailInfo() {
      this.showDetailInfo = !this.showDetailInfo
      if (!this.showDetailInfo) return
      this.getDetailInfo()
      this.getMacs()
    },

    getMacs() {
      if (!this.showDetailInfo) return
      this.collectingMACs = true

      const error = (r: any) => {
        this.collectingMACs = false;
        this.$emit("toast", r, "Не удалось получить MAC интерфейса");
        this.showDetailInfo = false;
      }

      api.get("/device/api/" + this.deviceName + "/macs?port=" + this.interface.name)
          .then(
              (value: AxiosResponse<{ result: MacInfo[], count: number }>) => {
                this.MACs = value.data.result;
                this.collectingMACs = false;
              },
              error
          ).catch(error)
    },

    getDetailInfo() {
      if (!this.showDetailInfo) return

      this.collectingDetailInfo = true

      const error = (r: any) => {
        this.collectingDetailInfo = false;
        this.$emit("toast", r, "Не удалось получить детали интерфейса");
        this.showDetailInfo = false;
      }

      api.get("/device/api/" + this.deviceName + "/interface-info?port=" + this.interface.name)
          .then(
              (value: AxiosResponse<ComplexInterfaceInfo>) => {
                this.complexInfo = value.data;
                this.collectingDetailInfo = false
              },
              error
          ).catch(error)
    },

    intfStatusDesc(status: string): string {
      if (status === "dormant") {
        return "Интерфейс ожидает внешних действий (например, последовательная линия, ожидающая входящего соединения)"
      }
      if (status === "notPresent") {
        return "Интерфейс имеет отсутствующие компоненты (как правило, аппаратные)"
      }
      return ""
    },

    toggleVlansList(event: Event) {
      // @ts-ignore
      this.$refs.vlansList.toggle(event, event.target);
    },

    /** Вычисляем цвет статуса порта */
    statusStyle(status: string): any {
      status = status.toLowerCase()
      let color = () => {
        if (status === "admin down") return "#ffb4bb"
        if (status === "notpresent") return "#c1c1c1"
        if (status === "dormant") return "#ffe389"
        if (status !== "down") return "#22e58b"
      }
      let baseStyle = {
        'width': '150px',
        'text-align': 'center',
        'background-color': color()
      }
      return Object.assign({}, this.dynamicOpacity, baseStyle)
    },


  }
})
</script>

<style>
.mac-line:hover bi {
  visibility: visible;
  color: #558af1;
}

.mac-line:hover span {
  color: #558af1;
}

.mac-line:not(:hover) .bi {
  visibility: hidden;
}

.text-help {
  border-bottom: solid #d1d1d1 1px;
  border-radius: 0;
  font-size: 0.75rem;
  margin: 10px;
  cursor: default;
}
</style>