<template>

  <tr :style="interfaceStyles" :class="interfaceClasses">

    <td style="text-align: right">

      <div class="btn-group">
        <!--       COMMENTS-->
        <Comment :interface="interface" :register-comment-action="registerCommentAction"/>

        <!-- Ссылка на графики в Zabbix -->
        <GraphsLink :interface="interface"/>
      </div>

    </td>

<!--       ПОРТ-->
    <td class="btn-fog" style="text-align: right">

      <div class="btn-group" role="group">

<!--        Название Интерфейса-->
        <div @click="toggleDetailInfo" class="col-auto blockquote" style="margin: 5px 10px; cursor:pointer;">
          <span class="position-absolute top-50 start-0 translate-middle badge rounded-pill"
                :style="portTypeStyles">
            <span v-if="complexInfo">{{complexInfo.portType}}</span>
          </span>
          <span class="position-relative" style="padding-left: 30px;">
                {{ interface.name }}
          </span>

        </div>

<!--        Управление состоянием интерфейсов-->
        <PortControlButtons
              :port-action="registerInterfaceAction"
              :interface="interface"
              :permission-level="permissionLevel" />

<!--        Посмотреть порт -->
        <button @click="toggleDetailInfo" class="btn btn-group" style="padding: 6px 6px 2px 6px">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box" viewBox="0 0 16 16">
            <path d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"></path>
          </svg>
        </button>

      </div>
    </td>

<!--          Статус порта-->
    <td data-bs-toggle="tooltip" data-bs-placement="top"
        :style="statusStyle(interface.status)"
        :data-bs-title="intfStatusDesc(interface.status)">
        <span>{{formatStatus(interface.status)}}</span>
    </td>

<!--          Описание порта-->
    <td>
        <ChangeDescription :device-name="deviceName" :interface="interface" />
    </td>

<!--          VLANS-->
    <td v-if="interface.vlans.length">{{ compressVlanRange(interface.vlans) }}</td>
    <td v-else></td>

  </tr>

  <tr v-if="showDetailInfo">

    <td v-if="complexInfo" colspan="5">

<!--      DETAIL PORT INFO  -->
    <div v-if="complexInfo.portDetailInfo" class="container row py-3">

      <div class="text-end">
          <span v-if="collectingDetailInfo" class="text-muted text-help" style="cursor: default">Обновляю...</span>
          <span v-else @click="getDetailInfo" class="text-muted text-help" style="cursor: pointer">Обновить</span>
      </div>

      <div v-if="complexInfo.portDetailInfo.type==='html'" class="card shadow py-3" v-html="complexInfo.portDetailInfo.data"></div>
      <div v-else-if="complexInfo.portDetailInfo.type==='text'" class="card shadow py-3" v-html="formatToHtml(complexInfo.portDetailInfo.data)"></div>

<!--      MIKROTIK -->
      <div v-else-if="complexInfo.portDetailInfo.type==='mikrotik'" class="card shadow py-3">
        <MikrotikInterfaceInfo :device-name="deviceName" :data="complexInfo.portDetailInfo.data" :interface="interface"/>
      </div>

<!--      ADSL -->
      <div v-else-if="complexInfo.portDetailInfo.type==='adsl'" class="card shadow py-3">
        <ADSLInterfaceInfo :device-name="deviceName" :data="complexInfo.portDetailInfo.data" :interface="interface"/>
      </div>

<!--      GPON -->
      <div v-else-if="complexInfo.portDetailInfo.type==='gpon'" class="card shadow py-3">
        <GPONInterfaceInfo
            @find-mac="findMacEvent"
            @session-mac="sessionEvent"
            :device-name="deviceName"
            :gpon-data="complexInfo.portDetailInfo.data"
            :permission-level="permissionLevel"
            :register-comment-action="registerCommentAction"
            :register-interface-action="registerInterfaceAction"
            :interface="interface" />
      </div>

<!--      ELTEX OLT -->
      <div v-else-if="complexInfo.portDetailInfo.type==='eltex-gpon'" class="card shadow py-3">
        <OLTInterfaceInfo
            @find-mac="findMacEvent"
            @session-mac="sessionEvent"
            :device-name="deviceName"
            :data="complexInfo.portDetailInfo.data"
            :permission-level="permissionLevel"
            :register-comment-action="registerCommentAction"
            :register-interface-action="registerInterfaceAction"
            :interface="interface" />
      </div>

    </div>

<!--      ANOTHER INFO  -->
    <div v-if="complexInfo" class="container row py-3">

      <div class="col-auto">

<!--        BUTTON-->
<!--        Конфигурация порта-->
        <div v-if="complexInfo.portConfig.length">
          <button type="button"
                  @click="portDetailMenu=portDetailMenu=='portConfig'?'':'portConfig'"
                  :class="portDetailMenu==='portConfig'?['btn', 'active']:['btn']">
            <svg class="bi me-2" width="16" height="16" role="img"><use xlink:href="#gear-icon"></use></svg>
            Конфигурация порта
          </button>
        </div>

<!--        BUTTON-->
<!--        Ошибки на порту-->
        <div v-if="complexInfo.portErrors.length">
          <button type="button"
                  @click="portDetailMenu=portDetailMenu=='portErrors'?'':'portErrors'"
                  :class="portDetailMenu==='portErrors'?['btn', 'active']:['btn']">
            <svg class="bi me-2" width="16" height="16" role="img"><use xlink:href="#warning-icon"></use></svg>
            Ошибки на порту
          </button>
        </div>

<!--        BUTTON-->
<!--        Диагностика кабеля-->
        <div v-if="complexInfo.hasCableDiag">
          <button type="button"
                  @click="portDetailMenu=portDetailMenu=='cableDiag'?'':'cableDiag'"
                  :class="portDetailMenu==='cableDiag'?['btn', 'active']:['btn']">
            <svg class="bi me-2" width="16" height="16" role="img"><use xlink:href="#cable-diag-icon"></use></svg>
            Диагностика кабеля
          </button>
        </div>
      </div>


<!--      Конфигурация порта -->
      <div v-show="portDetailMenu==='portConfig'" class="col-md">

        <div v-if="complexInfo.portConfig.length>0" class="card shadow" style="padding: 2rem;">
          <span v-html="formatToHtml(complexInfo.portConfig)" style="font-family: monospace"></span>
        </div>

        <div v-else class="d-flex justify-content-center">
          <div class="spinner-border" role="status"></div>
        </div>
      </div>

<!--      Ошибки на порту -->
      <div v-show="portDetailMenu==='portErrors'" class="col-md">

        <div v-if="complexInfo.portErrors.length>0" class="card shadow" style="padding: 2rem;">
          <span v-html="formatToHtml(complexInfo.portErrors)" style="font-family: monospace"></span>
        </div>

        <div v-else class="d-flex justify-content-center">
          <div class="spinner-border" role="status"></div>
        </div>

      </div>

<!--      Диагностика кабеля -->
      <div v-show="portDetailMenu==='cableDiag'" class="col-md">

        <div v-if="complexInfo.hasCableDiag" class="card shadow" style="padding: 2rem;">
          <CableDiag :device-name="deviceName" :port="interface.name"/>
        </div>

      </div>
    </div>


<!--      МАС-->
    <div v-if="MACs.length > 0" class="container">
      <span>Всего: {{MACs.length}}</span>

      <Pagination :p-object="pagination"/>

      <div class="table-responsive-lg">
        <div class="text-end">
            <span v-if="collectingMACs" class="text-muted text-help" style="cursor: default">Обновляю...</span>
            <span v-else @click="getMacs" class="text-muted text-help" style="cursor: pointer">Обновить</span>
        </div>

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

            <tr v-for="mac in macsPage">
                <td></td>

                <td style="font-family: monospace; font-size: x-large;">
                    <span :id="mac.mac" :title="mac.vlanName" style="cursor: help; font-family: monospace;">{{mac.vlanID}}</span>
                </td>

                <td class="mac-line" style="font-family: monospace; font-size: x-large;">
                    <span @click="findMacEvent(mac.mac)" class="nowrap" style="cursor: pointer; font-family: monospace;" title="Поиск MAC" data-bs-toggle="modal" data-bs-target="#modal-find-mac">
                        {{mac.mac}}
                        <svg class="bi me-2" width="24" height="24" role="img"><use xlink:href="#search-icon"></use></svg>
                    </span>
                </td>

                <td>
                  <button @click="sessionEvent(mac.mac, interface.name)" type="button" class="btn btn-outline-primary" data-bs-toggle="modal" data-bs-target="#bras-session-modal">
                    BRAS
                  </button>
                </td>
            </tr>

          </tbody>
        </table>
      </div>

      <Pagination :p-object="pagination"/>

    </div>

    <div v-else-if="MACs.length === 0" class="container">
      <div class="text-end">
          <span v-if="collectingMACs" class="text-muted text-help">Обновляю...</span>
          <span v-else @click="getMacs" class="text-muted text-help" style="cursor: pointer">Обновить</span>
      </div>
      <h3 class="text-center" style="padding-bottom: 40px;">Нет MAC</h3>
    </div>

    <div v-else class="d-flex justify-content-center" style="padding: 2.2rem;">
      <div class="spinner-border" role="status"></div>
    </div>

    </td>

    <td v-else class="d-flex justify-content-center" colspan="5">
      <div><div class="spinner-border" role="status"></div></div>
    </td>
  </tr>

</template>


<script lang="ts">
import {defineComponent, PropType} from "vue";
import {AxiosResponse} from "axios";

import PortControlButtons from "./PortControlButtons.vue";
import ChangeDescription from "./ChangeDescription.vue";
import Comment from "../../../components/Comment.vue";
import Pagination from "../../../components/Pagination.vue";
import CableDiag from "./CableDiag.vue";
import ADSLInterfaceInfo from "./xDSLInterfaceInfo.vue";
import GPONInterfaceInfo from "./GPONInterfaceInfo.vue";
import OLTInterfaceInfo from "./OLTInterfaceInfo.vue";
import MikrotikInterfaceInfo from "./MikrotikInterfaceInfo.vue";
import GraphsLink from "./GraphsLink.vue";
import Interface from "../../../types/interfaces";
import InterfaceComment from "../../../types/comments";
import Paginator from "../../../types/paginator";
import {ComplexInterfaceInfo} from "../detailInterfaceInfo";
import api_request from "../../../api_request";
import MacInfo from "../../../types/mac";

export default defineComponent({
  components: {
    GraphsLink,
    Pagination,
    ChangeDescription,
    PortControlButtons,
    Comment,
    CableDiag,
    ADSLInterfaceInfo,
    GPONInterfaceInfo,
    OLTInterfaceInfo,
    MikrotikInterfaceInfo,
  },

  emits: ["toast", "find-mac", "session-mac"],

  props: {
    deviceName: {required: true, type: String},
    interface: {required: true, type: Object as PropType<Interface>},
    permissionLevel: {required: true, type: Number},
    registerCommentAction: {
      required: true,
      type: Function as PropType<(action: "add"|"update"|"delete", comment: InterfaceComment, interfaceName: string) => void>
    },
    registerInterfaceAction: {
      required: true,
      type: Function as PropType<(action: "up"|"down"|"reload", port: string, description: string) => void>
    },
    dynamicOpacity: {required: true, type: Object as PropType<{opacity: Number}>},
  },

  data() {
    return {
      showDetailInfo: false,
      portDetailMenu: "" as (""|"portConfig"|"portErrors"|"cableDiag"),
      MACs: [] as MacInfo[],
      collectingMACs: false,

      complexInfo: null as ComplexInterfaceInfo|null,
      collectingDetailInfo: false,

      pagination: new Paginator(0, 0, 20),
    }
  },

  computed: {
    interfaceStyles(): any {
      if (this.showDetailInfo) return {"background-color": "#e8efff"};
      return this.dynamicOpacity
    },
    interfaceClasses(): string[] {
      if (this.showDetailInfo) return ["shadow", "sticky-top"];
      return []
    },
    portTypeStyles() {
      let styles = {"font-size": "0.6rem"}

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

    macsPage() {
        // Обрезаем по размеру страницы
        return this.MACs.slice(
            this.pagination.page * this.pagination.rowsPerPage,
            (this.pagination.page + 1) * this.pagination.rowsPerPage
        )
    }

  },

  methods: {

    findMacEvent(mac: string) {
      this.$emit("find-mac", mac)
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

      api_request.get("/device/api/" + this.deviceName + "/macs?port=" + this.interface.name)
          .then(
              (value: AxiosResponse<{result: MacInfo[], count: number }>) => {
                this.MACs = value.data.result;
                this.pagination.count = value.data.count
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

      api_request.get("/device/api/" + this.deviceName + "/interface-info?port=" + this.interface.name)
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

    compressVlanRange(list: number[]): string {
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

  }
})
</script>

<style>
tr:hover {
    background: #e8efff;
}
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