<template>

  <tr :id="'interface-'+interface.name" :style="interfaceStyles" :class="interfaceClasses"
      class="hover:bg-gray-100 dark:hover:bg-gray-800">

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

      <div class="flex items-center justify-between">

        <!--Название Интерфейса-->
        <div @click="toggleDetailInfo" class="flex items-center cursor-pointer">
          <span class="md:text-lg break-keep w-full font-mono">{{ interface.name }}</span>
        </div>

        <div>
          <div class="hidden sm:flex items-center">
            <span v-if="complexInfo" class="mx-2 px-1 rounded text-gray-200 font-mono" :style="portTypeStyles">
              {{ complexInfo.portType }}
            </span>

            <!--Управление состоянием интерфейсов-->
            <PortControlButtons
                :interface="interface"
                :device-name="deviceName"
                :permission-level="permissionLevel"/>

            <!--Посмотреть порт -->
            <Button @click="toggleDetailInfo" text>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                <path
                    d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"></path>
              </svg>
            </Button>
          </div>

          <Button icon="pi pi-info-circle" size="small" class="sm:hidden mx-1" outlined
                  @click="showPortControlsPopover"/>

        </div>
        <Popover ref="portControls">
          <div class="flex items-center max-sm:scale-90">
            <!--Управление состоянием интерфейсов-->
            <PortControlButtons
                :interface="interface"
                :device-name="deviceName"
                :permission-level="permissionLevel"/>

            <!--Посмотреть порт -->
            <Button @click="toggleDetailInfo" text>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                <path
                    d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"></path>
              </svg>
            </Button>

            <span v-if="complexInfo" class="mx-2 px-1 rounded text-gray-200 font-mono" :style="portTypeStyles">
              {{ complexInfo.portType }}
            </span>
          </div>
        </Popover>

      </div>
    </td>

    <!--Статус порта-->
    <td :style="statusStyle(interface.status)" v-tooltip="intfStatusDesc(interface.status)"
        :class="interface.status.toLowerCase()==='down'?'dark:!text-white':''"
        class="text-gray-950 dark:!opacity-70 text-nowrap text-sm text-center sm:min-w-[6rem] px-3 font-mono">
      <span>{{ formatStatus(interface.status) }}</span>
    </td>

    <!--Описание порта-->
    <td>
      <ChangeDescription :device-name="deviceName" :interface="interface"
                         @change-device="dev => $emit('changeDevice', dev)"/>
    </td>

    <!--VLANS-->
    <td v-if="showVlans && interface.vlans.length" @click="toggleVlansList"
        class="cursor-pointer text-nowrap overflow-x-visible max-w-20 px-3 font-mono">
      {{ compressVlanRange }}
    </td>
    <td v-else></td>

  </tr>

  <tr v-if="showDetailInfo">

    <td v-if="complexInfo" colspan="5" class="border dark:bg-transparent bg-zinc-50 dark:border-gray-600 shadow p-3">

      <!--      DETAIL PORT INFO  -->
      <div v-if="complexInfo.portDetailInfo" class="container py-3">

        <div class="flex justify-end">
          <UpdateCommonButton :condition="collectingDetailInfo" @update="getDetailInfo"/>
        </div>

        <div v-if="complexInfo.portDetailInfo.type==='html'" class="p-3 "
             v-html="complexInfo.portDetailInfo.data"></div>

        <div v-else-if="complexInfo.portDetailInfo.type==='text'" class="px-3 max-sm:text-xs font-mono whitespace-pre">
          {{ complexInfo.portDetailInfo.data }}
        </div>

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
    <div class="font-mono">{{ compressVlanRange }}</div>
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
import UpdateCommonButton from "@/components/UpdateCommonButton.vue";

export default defineComponent({
  components: {
    UpdateCommonButton,
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
    showVlans: {required: false, type: Boolean, default: true},
  },

  emits: ["changeDevice"],

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

  mounted() {
    let selectedPorts = this.getSelectedPorts();

    if (selectedPorts.includes(this.interface.name)) {
      this.showDetailInfo = true;
      this.getDetailInfo();
      setTimeout(() => {
        window.scrollTo({
          top: (document.getElementById("interface-" + this.interface.name)?.offsetTop ?? 0) + (window.innerHeight / 2),
          behavior: "smooth"
        })
      }, 100)
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

    getSelectedPorts(): string[] {
      // Преобразуем currentQuery.port в массив строк
      let selectedPorts: string[] = [];

      const currentQuery = {...this.$route.query};
      const portQuery = currentQuery.port;

      if (Array.isArray(portQuery)) {
        selectedPorts = portQuery.filter((p): p is string => typeof p === 'string');
      } else if (typeof portQuery === 'string') {
        selectedPorts = [portQuery];
      }
      return selectedPorts
    },

    toggleDetailInfo() {
      this.showDetailInfo = !this.showDetailInfo;

      let selectedPorts = this.getSelectedPorts();

      const portName = this.interface.name;

      if (this.showDetailInfo) {
        if (!selectedPorts.includes(portName)) {
          selectedPorts.push(portName);
        }
      } else {
        selectedPorts = selectedPorts.filter(p => p !== portName);
      }

      // Обновляем query
      const newQuery = {...this.$route.query};
      if (selectedPorts.length > 0) {
        newQuery.port = selectedPorts;
      } else {
        delete newQuery.port;
      }

      this.$router.push({query: newQuery});

      if (this.showDetailInfo) {
        this.getDetailInfo();
      }
    },

    getDetailInfo() {
      if (!this.showDetailInfo) return

      this.collectingDetailInfo = true

      const error = (e: any) => {
        this.collectingDetailInfo = false;
        errorToast("Не удалось получить информацию об интерфейсе", errorFmt(e))
        this.showDetailInfo = false;
      }

      api.get<ComplexInterfaceInfoType>("/api/v1/devices/" + this.deviceName + "/interface-info?port=" + this.interface.name)
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
      if (this.compressVlanRange.length < 5) return;
      // @ts-ignore
      this.$refs.vlansList.toggle(event, event.target);
    },

    showPortControlsPopover(event: Event) {
      // @ts-ignore
      this.$refs.portControls.toggle(event, event.target);
    },

    /** Вычисляем цвет статуса порта */
    statusStyle(status: string): any {
      status = status.toLowerCase()
      let baseStyle: any = {};

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
.text-help {
  border-bottom: solid #d1d1d1 1px;
  border-radius: 0;
  font-size: 0.75rem;
  margin: 10px;
  cursor: default;
}
</style>