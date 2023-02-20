<template>
  <tr :style="lineStyle(line[1])" :class="lineClasses">

      <td class="btn-fog" style="text-align: right">

        <div class="btn-group" role="group">

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
                :permission-level="permissionLevel" />

  <!--        Посмотреть порт -->
          <button @click="toggleDetailInfo" class="btn btn-group" style="padding: 6px 6px 2px 6px">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box" viewBox="0 0 16 16">
              <path d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"></path>
            </svg>
          </button>

        </div>
      </td>

      <td :style="statusStyles(line[1])">
         {{ line[1] }}
      </td>

<!--        Последнее подключение-->
      <td>{{ line[2] }}</td>
<!--        Последнее отключение -->
      <td>{{ line[3] }}</td>

<!--          Причина -->
      <td>
        {{line[4] === "dying-gasp"?"Предсмертный хрип":line[4]}}
      </td>
<!--          Дистанция -->
      <td>
        {{line[5]!=="-"?line[5]+" м":"-"}}
      </td>
<!--         Rx/Tx мощность -->
      <td>{{ line[6] }}</td>

  </tr>

  <tr v-if="showDetailInfo">
    <td colspan="7">

<!--      DETAIL PORT INFO  -->
    <div v-if="portDetailInfo" class="container row py-3">
      <div v-if="portDetailInfo.type==='html'" class="card shadow py-3" v-html="portDetailInfo.data"></div>
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
      </div>

<!--      Конфигурация порта -->
      <div v-show="portDetailMenu==='portConfig'" class="col-md">

        <div v-if="portConfig!==null" class="card shadow" style="padding: 2rem; text-align: left">
          <span v-html="format_to_html(portConfig)" style="font-family: monospace"></span>
        </div>

        <div v-else class="d-flex justify-content-center">
          <div class="spinner-border" role="status"></div>
        </div>
      </div>

<!--      Ошибки на порту -->
      <div v-show="portDetailMenu==='portErrors'" class="col-md">

        <div v-if="portErrors!==null" class="card shadow" style="padding: 2rem;">
          <span v-html="format_to_html(portErrors)" style="font-family: monospace"></span>
        </div>

        <div v-else class="d-flex justify-content-center">
          <div class="spinner-border" role="status"></div>
        </div>

      </div>

    </div>


<!--      МАС-->
    <div v-if="MACs && MACs.count > 0" class="container">
      <span>Всего: {{MACs.count}}</span>

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

          <tr v-for="mac in MACs.result">
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
                      class="nowrap" style="cursor: pointer; font-family: monospace;" title="Поиск MAC"
                      data-bs-toggle="modal" data-bs-target="#modal-find-mac">
                      {{mac.mac}}
                      <svg class="bi me-2" width="24" height="24" role="img">
                          <use xlink:href="#search-icon"></use>
                      </svg>
                  </span>
              </td>

              <td>
                <button @click="sessionEvent(mac.mac, ontInterface.Interface)" type="button" class="btn btn-outline-primary"
                        data-bs-toggle="modal" data-bs-target="#bras-session-modal">
                  BRAS
                </button>
              </td>
          </tr>

        </tbody>
      </table>
      </div>

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

export default defineComponent({
  props: {
    interface: {required: true, type: Object},
    line: {required: true, type: Object},
    permissionLevel: {required: true, type: Number},
    registerInterfaceAction: {required: true, type: Function},
  },
  data() {
    return {
      showDetailInfo: false,
      ontID: this.line[0],

      portDetailMenu: null,
      MACs: null,
      portDetailInfo: null,
      portType: null,
      portConfig: null,
      portErrors: null,
    }
  },
  components: {
    PortControlButtons,
  },
  computed: {
    ontInterface() {
      return {
        Interface: this.interface.Interface + "/" + this.ontID,
        Status: this.line[1],
        Description: "ONT: " + this.ontID + " " + this.interface.Description
      }
    },
    lineClasses() {
      if (this.showDetailInfo) return ["shadow", "sticky-top"];
      return []
    },

  },
  methods: {

    findMacEvent: function (mac) {
      this.$emit("find-mac", mac)
    },

    sessionEvent: function (mac, port) {
      this.$emit("session-mac", mac, port)
    },

    statusStyles(status) {
      if (status === "online") return {"background-color": "#22e58b"}
      if (status === "offline") return {"background-color": "#ffcacf"}
    },
    lineStyle(status) {
      if (status === "offline") return {"background-color": "#ffcacf"}
      if (this.showDetailInfo) return {"background-color": "#e8efff", "top": "56px"}
    },

    format_to_html: function (string) {

      let space_re = new RegExp(' ', 'g');
      let n_re = new RegExp('\n', 'g');

      string = string.replace(space_re, '&nbsp;').replace(n_re, '<br>')
      return string
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
            "/device/api/" + document.deviceName + "/macs?port=" + this.ontInterface.Interface,
            {method: "get"}
        )
        this.MACs = await response.json()

        window.tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
        window.tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

      } catch (err) {
        console.log(err)
      }
    },

    getDetailInfo: async function() {
      try {
        const response = await fetch(
            "/device/api/" + document.deviceName + "/interface-info?port=" + this.ontInterface.Interface,
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

  }
})
</script>