<template>
<div>

    <div>
        <h5 class="text-muted back-title" @click="toggleMode">
            {{tracerouteMode==='vlan'?'MAC':'VLAN'}} Traceroute
        </h5>
    </div>

<div v-show="tracerouteMode === 'vlan'">
    <div class="row">
        <div class="d-flex" style="align-items: center;">
            <h4 class="text-light py-3 m-0 me-2">VLAN Traceroute</h4>
            <div class="d-flex py-2 text-light" style="vertical-align: middle">

<!--                RAN WITH PROGRESS-->
                <div class="d-flex" v-if="vlanScanStatus.running && vlanScanStatus.progress && vlanScanStatus.progress > 0">
                    <div class="spinner-border me-2" role="status"></div>
                    <div style="display: flex; align-items: center;">Сканирование завершено на {{vlanScanStatus.progress}}%</div>
                </div>

<!--                ALREADY RAN-->
                <div v-else-if="vlanScanStatus.running" class="spinner-border me-2" role="status"></div>

<!--                RUN VLAN SCAN-->
                <div v-else-if="!vlanScanStatus.running && vlanScanStatus.available">
                    <svg style="cursor: pointer" @click="vlanScanStatus.run_vlans_scan" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
                         <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"></path>
                         <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"></path>
                     </svg>
                </div>

<!--                ERROR-->
                <div v-else>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" class="bi bi-x-circle" viewBox="0 0 16 16">
                      <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                      <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                    </svg>
                </div>

            </div>
        </div>

        <div class="my-3 d-flex align-items-center">
            <div>
              <input @keyup.enter="load_vlan_traceroute"
                     @input="getInputVlanInfo"
                     v-model="input.vlan"
                     style="text-align: center; width: 120px; height: 45px" type="text" class="form-control rounded-5 me-2"
                     autofocus placeholder="vlan">
            </div>
            <button v-if="!vlanTracerouteStarted" @click="load_vlan_traceroute" class="btn text-light">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-bezier2" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M1 2.5A1.5 1.5 0 0 1 2.5 1h1A1.5 1.5 0 0 1 5 2.5h4.134a1 1 0 1 1 0 1h-2.01c.18.18.34.381.484.605.638.992.892 2.354.892 3.895 0 1.993.257 3.092.713 3.7.356.476.895.721 1.787.784A1.5 1.5 0 0 1 12.5 11h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5H6.866a1 1 0 1 1 0-1h1.711a2.839 2.839 0 0 1-.165-.2C7.743 11.407 7.5 10.007 7.5 8c0-1.46-.246-2.597-.733-3.355-.39-.605-.952-1-1.767-1.112A1.5 1.5 0 0 1 3.5 5h-1A1.5 1.5 0 0 1 1 3.5v-1zM2.5 2a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1zm10 10a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1z"/>
                </svg>
            </button>
            <div v-if="inputVlanInfo.name" class="text-light fs-4">
                {{ inputVlanInfo.name }} ({{ inputVlanInfo.description }})
            </div>
        </div>
        <div class="col-md-auto">
            <h3>
                <span class="text-light badge bg-secondary" id="vlan_desc"></span>
            </h3>
        </div>
    </div>

    <div class="form-check form-switch">
      <input v-model="vlanTracerouteOptions.adminDownPorts"
             class="form-check-input" type="checkbox" role="switch" id="only-admin-up">
      <label class="form-check-label text-light" for="only-admin-up">
          Указывать выключенные порты
      </label>
    </div>

    <div class="form-check form-switch py-1">
      <input v-model="vlanTracerouteOptions.showEmptyPorts"
             class="form-check-input" type="checkbox" role="switch" id="empty-ports">
      <label class="form-check-label text-light" for="empty-ports">
          Показывать пустые порты
      </label>
    </div>

    <div class="form-check form-switch py-1">
      <input v-model="vlanTracerouteOptions.doubleCheckVlan"
             class="form-check-input" type="checkbox" role="switch" id="double-check-vlan">
      <label class="form-check-label text-light" for="double-check-vlan">
          Двухстороннее соответствие VLAN на соседних портах
      </label>
    </div>

    <div class="py-1 text-center d-flex align-items-center">
        <div style="width: 130px" class="me-2">
            <div class="input-group py-3">
              <span @click="vlanTracerouteOptions.graphMinLength>1?vlanTracerouteOptions.graphMinLength--:null"
                    class="input-group-text noselect cursor-pointer">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-dash-lg" viewBox="0 0 16 16">
                      <path fill-rule="evenodd" d="M2 8a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11A.5.5 0 0 1 2 8Z"/>
                    </svg>
              </span>
              <input disabled :value="vlanTracerouteOptions.graphMinLength" id="min-graph-length"
                     type="text" class="form-control text-center">
              <span @click="vlanTracerouteOptions.graphMinLength++" class="input-group-text noselect cursor-pointer">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus-lg" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2Z"/>
                  </svg>
              </span>
            </div>
        </div>
        <div class="form-label text-light col-3 noselect">
            Минимальное количество узлов в одном графе
        </div>
    </div>

</div>

<div v-show="tracerouteMode === 'mac'">
    <div class="row">
        <div class="d-flex" style="align-items: center;">
            <h4 class="text-light py-3 m-0 me-2">MAC Traceroute</h4>
            <div class="d-flex py-2 text-light" style="vertical-align: middle">

<!--                RAN WITH PROGRESS-->
                <div v-if="macScanStatus.running && macScanStatus.progress && macScanStatus.progress > 0" class="d-flex">
                    <div class="spinner-border me-2" role="status"></div>
                    <div style="display: flex; align-items: center;">Сканирование завершено на {{macScanStatus.progress}}%</div>
                </div>

<!--                ALREADY RAN-->
                <div v-else-if="macScanStatus.running" class="spinner-border me-2" role="status"></div>

<!--                RUN MAC SCAN-->
                <div v-else-if="!macScanStatus.running && macScanStatus.available">
                    <svg style="cursor: pointer" @click="macScanStatus.run_vlans_scan" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
                         <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"></path>
                         <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"></path>
                     </svg>
                </div>

<!--                ERROR-->
                <div v-else>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" class="bi bi-x-circle" viewBox="0 0 16 16">
                      <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                      <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                    </svg>
                </div>

            </div>
        </div>

        <div class="my-3 d-flex align-items-center">
            <div>
              <input @keyup.enter="load_mac_traceroute" v-model="input.mac"
                     style="text-align: center; width: 200px; height: 45px;" type="text"
                     class="form-control rounded-5" autofocus placeholder="mac">
            </div>
            <button v-if="!macTracerouteStarted" @click="load_mac_traceroute" class="btn text-light">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-bezier2" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M1 2.5A1.5 1.5 0 0 1 2.5 1h1A1.5 1.5 0 0 1 5 2.5h4.134a1 1 0 1 1 0 1h-2.01c.18.18.34.381.484.605.638.992.892 2.354.892 3.895 0 1.993.257 3.092.713 3.7.356.476.895.721 1.787.784A1.5 1.5 0 0 1 12.5 11h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5H6.866a1 1 0 1 1 0-1h1.711a2.839 2.839 0 0 1-.165-.2C7.743 11.407 7.5 10.007 7.5 8c0-1.46-.246-2.597-.733-3.355-.39-.605-.952-1-1.767-1.112A1.5 1.5 0 0 1 3.5 5h-1A1.5 1.5 0 0 1 1 3.5v-1zM2.5 2a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1zm10 10a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1z"/>
                </svg>
            </button>
        </div>
    </div>
</div>


<!--FULL SCREEN-->
    <div id="fullScreen" class="fullScreenButton" title="На весь экран">
        <button id="fullScreenButton" type="button" class="btn btn-secondary">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="24" fill="currentColor" class="bi bi-arrows-angle-expand" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M5.828 10.172a.5.5 0 0 0-.707 0l-4.096 4.096V11.5a.5.5 0 0 0-1 0v3.975a.5.5 0 0 0 .5.5H4.5a.5.5 0 0 0 0-1H1.732l4.096-4.096a.5.5 0 0 0 0-.707zm4.344-4.344a.5.5 0 0 0 .707 0l4.096-4.096V4.5a.5.5 0 1 0 1 0V.525a.5.5 0 0 0-.5-.5H11.5a.5.5 0 0 0 0 1h2.768l-4.096 4.096a.5.5 0 0 0 0 .707z"></path>
            </svg>
        </button>
    </div>

<!--COLLAPSE SCREEN-->
    <div id="collapseScreen" title="Свернуть"
         style="z-index: 10; display: none; right: 0; top: 0; position: absolute; margin: 10px 10px 0 0;">
        <button id="collapseScreenButton" type="button" class="btn btn-secondary">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="24" fill="currentColor" class="bi bi-arrows-angle-contract" viewBox="0 0 16 16">
          <path fill-rule="evenodd" d="M.172 15.828a.5.5 0 0 0 .707 0l4.096-4.096V14.5a.5.5 0 1 0 1 0v-3.975a.5.5 0 0 0-.5-.5H1.5a.5.5 0 0 0 0 1h2.768L.172 15.121a.5.5 0 0 0 0 .707zM15.828.172a.5.5 0 0 0-.707 0l-4.096 4.096V1.5a.5.5 0 1 0-1 0v3.975a.5.5 0 0 0 .5.5H14.5a.5.5 0 0 0 0-1h-2.768L15.828.879a.5.5 0 0 0 0-.707z"></path>
        </svg>
        </button>
    </div>

    <!--LOAD TRACEROUTE-->
    <div v-if="vlanTracerouteStarted || macTracerouteStarted">
      <div style="text-align: center">
        <div class="me-2 spinner-border text-primary" role="status" style="text-align: center;height: 200px;width: 200px;"></div>
      </div>
    </div>

    <div style="background-color: #222222; height: 100%">
    <!--TRACEROUTE-->
        <div id="vlan-network" v-show="tracerouteMode === 'vlan'"></div>
        <div id="mac-network" v-show="tracerouteMode === 'mac'"></div>
    </div>

</div>
</template>

<script lang="ts">
import {defineComponent} from "vue";

import api_request from "../../api_request";
import ScanStatus from "./scan";
import TracerouteNetwork from "./net";

export default defineComponent({
  name: 'app',
  data() {
    return {
      macScanIcon: "" as string,

      vlanScanStatus: new ScanStatus("/tools/api/vlans-scan/check", "/tools/api/vlans-scan/run"),
      macScanStatus: new ScanStatus("/gather/mac-scan/check", "/gather/mac-scan/run"),

      vlanTracerouteStarted: false,
      macTracerouteStarted: false,

      // Установка значения по умолчанию для свойства tracerouteMode.
      tracerouteMode: 'vlan' as ("vlan" | "mac"),

      // Пользовательский ввод
      input: {
        vlan: "",
        mac: "",
      },

      inputVlanInfo: {
        name: "" as string,
        description: "" as string
      },

      // Свойство данных, которое используется для хранения состояния флажков.
      vlanTracerouteOptions: {
        adminDownPorts: false,
        showEmptyPorts: false,
        doubleCheckVlan: true,
        graphMinLength: 3,
      },

      vlanNetwork: new TracerouteNetwork("vlan-network"),
      macNetwork: new TracerouteNetwork("mac-network")

    }
  },

  // Хук жизненного цикла, который вызывается после создания экземпляра.
  created() {
    this.vlanScanStatus.checkScanStatus()
    this.macScanStatus.checkScanStatus()
  },

  methods: {

    getInputVlanInfo() {
      if (this.validateVlan(this.input.vlan) === 0) return;
      api_request.get("/tools/api/vlan-desc?vlan="+this.input.vlan)
          .then(resp => {this.inputVlanInfo = resp.data})
    },

    // Метод, который переключает значение свойства `tracerouteMode` между `vlan` и `mac`.
    toggleMode() {
      if (this.tracerouteMode === 'vlan') {
        this.tracerouteMode = 'mac';
      }
      else if (this.tracerouteMode === 'mac') {
        this.tracerouteMode = 'vlan';
      }
    },

    /**
     * Метод, возвращающий копию объекта baseVisOptions с изменениями, в зависимости от значения свойства tracerouteMode.
     */
    getVisOptions(...update: any): any {
      if (!update) update = {};

      if (this.tracerouteMode==='vlan'){
        this.vlanNetwork.options.edges.arrows.middle.enabled = false;
        return {...this.vlanNetwork.options, ...update};

      } else {
        this.macNetwork.options.edges.arrows.middle.enabled = true;
        return {...this.macNetwork.options, ...update};
      }

    },

    // Проверяет, действителен ли vlan.
    validateVlan(vlan: string): number {
      // Это регулярное выражение, которое проверяет, является ли строка числом.
      if (!/^\d+$/.test(vlan)) return 0;
      // Он преобразует строку в число.
      let vlanNumber = Number(vlan)
      // Это простая проверка, чтобы убедиться, что vlan действителен.
      if (vlanNumber > 0 && vlanNumber <= 4096) return vlanNumber;
      return 0
    },


    /**
     * Отправляем на сервер запрос трассировки указанного в поле для ввода VLAN
     * И создаем в определенном блоке граф для данной трассировки.
     */
    load_vlan_traceroute() {
      // Проверяем, действителен ли vlan.
      let valid_vlan = this.validateVlan(this.input.vlan)
      if (valid_vlan === 0) return;

      this.vlanTracerouteStarted = true

      let url = '/tools/api/vlan-traceroute?vlan=' + this.input.vlan +
          '&ep=' + this.vlanTracerouteOptions.showEmptyPorts +
          '&ad=' + this.vlanTracerouteOptions.adminDownPorts +
          '&double_check=' + this.vlanTracerouteOptions.doubleCheckVlan +
          '&graph_min_length=' + this.vlanTracerouteOptions.graphMinLength

      api_request.get(url)
          .then(
              (resp) => {
                let options: any = resp.data?resp.data.options:null
                this.vlanNetwork.renderVisualData(resp.data.nodes, resp.data.edges, this.getVisOptions(options));
                this.vlanTracerouteStarted = false;
              }
          ).catch(
              () => this.vlanTracerouteStarted = false
          )

    },

    // Удаляет из MAC адреса все символы, не являющиеся шестнадцатеричными.
    validateMac(mac: string): string {
      return String(mac).replace(/\W/g, "")
    },


    /**
     * Отправляем на сервер запрос трассировки указанного в поле для ввода MAC.
     * И создаем в определенном блоке граф для данной трассировки.
     */
    load_mac_traceroute() {
      let valid_mac = this.validateMac(this.input.mac)
      if (!valid_mac.length) return

      this.macTracerouteStarted = true
      const url = '/gather/api/traceroute/mac-address/' + valid_mac + "/"

      api_request.get(url)
          .then(
              resp => {
                this.macNetwork.renderVisualData(resp.data.nodes, resp.data.edges, this.getVisOptions());
                this.macTracerouteStarted = false;
              }
          )
          .catch(
              () => this.macTracerouteStarted = false
          )
    },

  }
});
</script>

<style>
.fullScreen {
    z-index: 9;
    position: absolute;
    top: -8px;
    left: 0;
    width: 100%;
    height: 100%;
}
.fullScreenButton {
    display: none;
    text-align: right;
    position: relative;
    z-index: 1;
    top: 57px;
    right: 10px;
}
.back-title {
  margin-left: 40px;
  border-bottom: 1px solid;
  width: fit-content;
  cursor: pointer;
}
.noselect {
  -webkit-touch-callout: none!important; /* iOS Safari */
    -webkit-user-select: none!important; /* Safari */
     -khtml-user-select: none!important; /* Konqueror HTML */
       -moz-user-select: none!important; /* Old versions of Firefox */
        -ms-user-select: none!important; /* Internet Explorer/Edge */
            user-select: none!important; /* Non-prefixed version, currently
                                  supported by Chrome, Edge, Opera and Firefox */
}
</style>
