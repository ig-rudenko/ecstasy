<template>


  <tr :style="interfaceStyles" :class="interfaceClasses">

<!--       COMMENTS-->
    <td style="text-align: right">
        <Comment :interface="interface" :register-comment-action="registerCommentAction" />
    </td>

<!--       ПОРТ-->
    <td class="btn-fog" style="text-align: right">

      <div class="btn-group" role="group">

<!--        Название Интерфейса-->
        <div @click="toggleDetailInfo" class="col-auto blockquote" style="margin: 5px 10px; cursor:pointer;">
          <span class="position-absolute top-50 start-0 translate-middle badge rounded-pill"
                :style="portTypeStyles">
            {{portType}}
          </span>
          <span class="position-relative" style="padding-left: 30px;">
                {{ interface.Interface }}
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
        :style="statusStyle(interface.Status)"
        :data-bs-title="intfStatusDesc(interface.Status)">
        <span>{{formatStatus(interface.Status)}}</span>
    </td>

<!--          Описание порта-->
    <td>
        <ChangeDescription :device_name="deviceName" :interface="interface" />
    </td>

<!--          VLANS-->
    <td v-if="interface['VLAN\'s']">{{ interface["VLAN's"].join(", ") }}</td>
    <td v-else></td>

  </tr>

  <tr v-if="showDetailInfo">

  <td colspan="5">

<!--      DETAIL PORT INFO  -->
    <div v-if="portDetailInfo" class="container row py-3">
      <div class="card shadow py-3" v-html="portDetailInfo"></div>
    </div>

<!--      ANOTHER INFO  -->
    <div class="container row py-3">

      <div class="col-auto">

<!--        BUTTON-->
<!--        Конфигурация порта-->
        <div v-if="portConfig && portConfig.length">
          <button type="button"
                  @click="portDetailMenu='portConfig'"
                  :class="portDetailMenu==='portConfig'?['btn', 'active']:['btn']">
            <svg class="bi me-2" width="16" height="16" role="img"><use xlink:href="#gear-icon"></use></svg>
            Конфигурация порта
          </button>
        </div>

<!--        BUTTON-->
<!--        Ошибки на порту-->
        <div v-if="portErrors && portErrors.length">
          <button type="button"
                  @click="portDetailMenu='portErrors'"
                  :class="portDetailMenu==='portErrors'?['btn', 'active']:['btn']">
            <svg class="bi me-2" width="16" height="16" role="img"><use xlink:href="#warning-icon"></use></svg>
            Ошибки на порту
          </button>
        </div>

<!--        BUTTON-->
<!--        Диагностика кабеля-->
        <div>
          <button type="button"
                  @click="portDetailMenu='cableDiag'"
                  :class="portDetailMenu==='cableDiag'?['btn', 'active']:['btn']">
            <svg class="bi me-2" width="16" height="16" role="img"><use xlink:href="#cable-diag-icon"></use></svg>
            Диагностика кабеля
          </button>
        </div>
      </div>


<!--      Конфигурация порта -->
      <div v-if="portDetailMenu==='portConfig'" class="col-md">

        <div v-if="portConfig!==null" class="card shadow" style="padding: 2rem;">
          <span v-html="format_to_html(portConfig)" style="font-family: monospace"></span>
        </div>

        <div v-else class="d-flex justify-content-center">
          <div class="spinner-border" role="status"></div>
        </div>
      </div>

<!--      Ошибки на порту -->
      <div v-if="portDetailMenu==='portErrors'" class="col-md">

        <div v-if="portErrors!==null" class="card shadow" style="padding: 2rem;">
          <span v-html="format_to_html(portErrors)" style="font-family: monospace"></span>
        </div>

        <div v-else class="d-flex justify-content-center">
          <div class="spinner-border" role="status"></div>
        </div>

      </div>

<!--      Диагностика кабеля -->
      <div v-if="portDetailMenu==='cableDiag'" class="col-md">

        <div v-if="cableDiag!==null">
        </div>

        <div v-else class="d-flex justify-content-center">
          <div class="spinner-border" role="status"></div>
        </div>

      </div>
    </div>


<!--      МАС-->
    <div v-if="MACs && MACs.count > 0" class="container">
      <span>Всего: {{MACs.count}}</span>

      <Pagination v-bind:p-object="pagination"/>

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

          <tr v-for="mac in macsPage">
              <td></td>

              <td style="font-family: monospace; font-size: x-large;">
                  <span data-bs-toggle="tooltip" data-bs-placement="right" :data-bs-title="mac.vlanName"
                        style="cursor: help; font-family: monospace;">
                      {{mac.vlanID}}
                  </span>
              </td>

              <td class="mac-line" style="font-family: monospace; font-size: x-large;">
                  <span
                      @click="findMacEvent(mac.mac)"
                      class="nowrap" style="cursor: pointer; font-family: monospace;" title="Поиск MAC" data-bs-toggle="modal" data-bs-target="#modal-find-mac">
                      {{mac.mac}}
                      <svg class="bi me-2" width="24" height="24" role="img">
                          <use xlink:href="#search-icon"></use>
                      </svg>
                  </span>
              </td>

              <td>
                <a class="btn btn-outline-primary" href="/device/session?device=SVSL-012-Balt14p2-ASW1&amp;port=Eth1/0/2&amp;desc=NOMON_4531413_Asso5800&amp;mac=60e3-27d6-bff1">
                  BRAS
                </a>
              </td>
          </tr>

        </tbody>
      </table>
      </div>

      <Pagination v-bind:p-object="pagination"/>

    </div>

    <div v-else-if="MACs && MACs.count === 0" class="container">
      <h3 class="text-center" style="padding-bottom: 40px;">Нет MAC</h3>
    </div>

    <div v-else class="d-flex justify-content-center" style="padding: 2.2rem;">
      <div class="spinner-border" role="status"></div>
    </div>

    </td>
  </tr>

</template>


<script>
import {defineComponent} from "vue";
import PortControlButtons from "./PortControlButtons.vue";
import ChangeDescription from "./ChangeDescription.vue";
import Comment from "./Comment.vue";
import Pagination from "./Pagination.vue";

export default defineComponent({
  data() {
    return {
      showDetailInfo: false,
      portDetailMenu: null,
      MACs: null,
      portDetailInfo: null,
      portType: null,
      portConfig: null,
      portErrors: null,
      cableDiag: null,

      pagination: {
        count: 0,
        page: 0,
        rows_per_page: 20,
        next_page: null,
      },
    }
  },
  props: {
    interface: {required: true},
    deviceName: {required: true},
    permissionLevel: {required: true, type: Number},
    commentObject: {required: true},
    registerCommentAction: {required: true, type: Function},
    portAction: {required: true},
    registerInterfaceAction: {required: true, type: Function},
  },
  components: {
    Pagination,
    ChangeDescription,
    PortControlButtons,
    Comment
  },

  computed: {
    interfaceStyles: function () {
      if (this.showDetailInfo) return {"background-color": "#e8efff"};
      return {}
    },
    interfaceClasses: function () {
      if (this.showDetailInfo) return ["shadow", "sticky-top"];
      return []
    },
    portTypeStyles: function () {
      let styles = {"font-size": "0.6rem"}

      if (!this.portType) return styles;

      if (this.portType === "COPPER") {
        styles["background-color"] = "#b87333"
      } else if (this.portType === "SFP") {
        styles["background-color"] = "#3e6cff"
      } else if (this.portType.includes("COMBO")) {
        styles["background-color"] = "#8133b8"
      }
      return styles
    },

    macsPage: function () {
        // Обрезаем по размеру страницы
        return this.MACs.result.slice(
            this.pagination.page * this.pagination.rows_per_page,
            (this.pagination.page + 1) * this.pagination.rows_per_page
        )
    }

  },

  methods: {

    findMacEvent: function (mac) {
      this.$emit("find-mac", mac)
    },

    /**
     * Превращаем строку в html, для корректного отображения
     *
     * @param string Строка, для форматирования
     * Заменяем перенос строки на `<br>` пробелы на `&nbsp;`
     */
    format_to_html: function (string) {

      let space_re = new RegExp(' ', 'g');
      let n_re = new RegExp('\n', 'g');

      string = string.replace(space_re, '&nbsp;').replace(n_re, '<br>')
      return string
    },

    formatStatus: function (status) {
      if (status === "dormant") return "activating..."
      return status
    },

    toggleDetailInfo: async function() {
      this.showDetailInfo = !this.showDetailInfo

      if (!this.showDetailInfo) return

      await this.getDetailInfo()
      await this.getMacs()
    },

    getMacs: async function() {
      try {
        const response = await fetch(
            "/device/api/" + this.deviceName + "/macs?port=" + this.interface.Interface,
            {method: "get"}
        )
        this.MACs = await response.json()

        this.pagination.count = this.MACs.count

        window.tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
        window.tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

      } catch (err) {
        console.log(err)
      }
    },

    getDetailInfo: async function() {
      try {
        const response = await fetch(
            "/device/api/" + this.deviceName + "/interface-info?port=" + this.interface.Interface,
            {method: "get"}
        )
        let data = await response.json()
        console.log(data)

        this.portErrors = data.portErrors
        this.portConfig = data.portConfig
        this.portType = data.portType
        this.portDetailInfo = data.portDetailInfo

      } catch (err) {
        console.log(err)
      }
    },


    intfStatusDesc: function (status) {
      if (status === "dormant") {
        return "Интерфейс ожидает внешних действий (например, последовательная линия, ожидающая входящего соединения)"
      }
      if (status === "notPresent") {
        return "Интерфейс имеет отсутствующие компоненты (как правило, аппаратные)"
      }
    },

    /**
     * Вычисляем цвет статуса порта
     *
     * @param status Статус порта
     * @returns {{"background-color": string, width: string, "text-align": string, "opacity": number}}
     */
    statusStyle: function (status) {
      status = status.toLowerCase()
      let color = function () {
        if (status === "admin down") return "#ffb4bb"
        if (status === "notpresent") return "#c1c1c1"
        if (status === "dormant") return "#ffe389"
        if (status !== "down") return "#22e58b"
      }
      let base_style = {
        'width': '150px',
        'text-align': 'center',
        'background-color': color()
      }
      return Object.assign({}, this.dynamicOpacity, base_style)
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
</style>