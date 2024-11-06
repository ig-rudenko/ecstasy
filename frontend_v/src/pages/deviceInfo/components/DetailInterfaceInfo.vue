<template>

  <tr :style="interfaceStyles" :class="interfaceClasses" class="hover:bg-gray-100 dark:hover:bg-gray-800">

    <td>

      <div class="flex gap-1 px-2">
        <!--       COMMENTS-->
        <Comment :interface="interface" :device-name="deviceName" :allow-edit="true"/>

        <!-- Ссылка на графики в Zabbix -->
        <GraphsLink :interface="interface"/>
      </div>

    </td>

    <!--ПОРТ-->
    <td class="btn-fog" style="text-align: right">

      <div class="flex items-center">

        <!--Название Интерфейса-->
        <div @click="toggleDetailInfo" class="flex items-center cursor-pointer">
          <span class="pl-8 pr-4 text-xl">{{ interface.name }}</span>
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
            <path
                d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"></path>
          </svg>
        </Button>

        <span v-if="complexInfo" class="mx-2 px-1 rounded text-gray-200 font-mono" :style="portTypeStyles">
          {{ complexInfo.portType }}
        </span>

      </div>
    </td>

    <!--Статус порта-->
    <td :style="statusStyle(interface.status)" v-tooltip="intfStatusDesc(interface.status)"
        :class="interface.status.toLowerCase()==='down'?'dark:!text-white':''"
        class="text-gray-950 text-nowrap text-center min-w-[6rem] px-3 font-mono">
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

    <td v-if="complexInfo" colspan="5" class="border dark:bg-transparent bg-zinc-50 dark:border-gray-600 shadow p-3">

      <!--      DETAIL PORT INFO  -->
      <div v-if="complexInfo.portDetailInfo" class="container py-3">

        <div class="text-end">
          <span v-if="collectingDetailInfo" class="text-muted-color text-help"
                style="cursor: default">Обновляю...</span>
          <span v-else @click="getDetailInfo" class="text-muted-color text-help" style="cursor: pointer">Обновить</span>
        </div>

        <div v-if="complexInfo.portDetailInfo.type==='html'" class="p-3 "
             v-html="complexInfo.portDetailInfo.data"></div>

        <div v-else-if="complexInfo.portDetailInfo.type==='text'" class="px-3 font-mono"
             v-html="textToHtml(complexInfo.portDetailInfo.data)"></div>

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
              :device-name="deviceName"
              :gpon-data="complexInfo.portDetailInfo.data"
              :permission-level="permissionLevel"
              :interface="interface"/>
        </div>

        <!--      ELTEX OLT -->
        <div v-else-if="complexInfo.portDetailInfo.type==='eltex-gpon'" class="p-3 border rounded shadow py-3">
          <OLTInterfaceInfo
              :device-name="deviceName"
              :data="complexInfo.portDetailInfo.data"
              :permission-level="permissionLevel"
              :interface="interface"/>
        </div>

      </div>

      <!--      ANOTHER INFO  -->
      <ComplexInterfaceInfo :complex-info="complexInfo" :interface="interface" :device-name="deviceName"/>

    </td>

    <td v-else colspan="5">
      <div class="flex justify-center">
        <ProgressSpinner/>
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
import {DeviceInterface} from "@/services/interfaces";
import MacInfo from "@/pages/deviceInfo/mac";
import {errorToast} from "@/services/my.toast";
import errorFmt from "@/errorFmt";
import ComplexInterfaceInfo from "@/pages/deviceInfo/components/ComplexInterfaceInfo.vue";
import {textToHtml} from "@/formats";
import {ComplexInterfaceInfoType} from "@/pages/deviceInfo/detailInterfaceInfo";

export default defineComponent({
  components: {
    ComplexInterfaceInfo,
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

      complexInfo: null as ComplexInterfaceInfoType | null,
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
    textToHtml,

    formatStatus(status: string): string {
      if (status === "dormant") return "activating..."
      return status
    },

    toggleDetailInfo() {
      this.showDetailInfo = !this.showDetailInfo
      if (!this.showDetailInfo) return
      this.getDetailInfo()
    },

    getDetailInfo() {
      if (!this.showDetailInfo) return

      this.collectingDetailInfo = true

      const error = (e: any) => {
        this.collectingDetailInfo = false;
        errorToast("Не удалось получить информацию об интерфейсе", errorFmt(e))
        this.showDetailInfo = false;
      }

      api.get<ComplexInterfaceInfo>("/device/api/" + this.deviceName + "/interface-info?port=" + this.interface.name)
          .then(
              value => {
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
      let baseStyle = {};

      if (status === "admin down") baseStyle["background-color"] = "#ffb4bb";
      if (status === "notpresent") baseStyle["background-color"] = "#c1c1c1";
      if (status === "dormant") baseStyle["background-color"] = "#ffe389";
      if (status === "up") baseStyle["background-color"] = "#22e58b";

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