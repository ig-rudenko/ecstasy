<template>

  <Header/>

  <div class="container mx-auto p-6 px-10">
    <div class="flex">
      <div class="text-muted-color ml-10 text-xl cursor-pointer" @click="toggleMode">
        {{ tracerouteMode === 'vlan' ? 'MAC' : 'VLAN' }} Traceroute
      </div>
    </div>

    <div v-show="tracerouteMode === 'vlan'" class="h-full text-gray-200">
      <div>
        <div class="flex items-center">
          <div class="text-gray-200 py-3 m-0 me-2 text-2xl">VLAN Traceroute</div>
          <div class="flex py-2 text-gray-200">

            <!--                RAN WITH PROGRESS-->
            <div class="flex" v-if="vlanScanStatus.running && vlanScanStatus.progress && vlanScanStatus.progress > 0">
              <div class="spinner-border me-2" role="status"></div>
              <div style="display: flex; align-items: center;">Сканирование завершено на
                {{ vlanScanStatus.progress }}%
              </div>
            </div>

            <!--                ALREADY RAN-->
            <div v-else-if="vlanScanStatus.running" class="spinner-border me-2" role="status"></div>

            <!--                RUN VLAN SCAN-->
            <div v-else-if="!vlanScanStatus.running && vlanScanStatus.available">
              <svg style="cursor: pointer" @click="vlanScanStatus.run_vlans_scan" xmlns="http://www.w3.org/2000/svg"
                   width="24" height="24" fill="white" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"></path>
                <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"></path>
              </svg>
            </div>

            <!--                ERROR-->
            <div v-else>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" class="bi bi-x-circle"
                   viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
              </svg>
            </div>

          </div>
        </div>

        <div class="my-3 flex items-center gap-3">
          <div>
            <InputNumber @keyup.enter="load_vlan_traceroute"
                         @input="getInputVlanInfo"
                         input-class="w-24 bg-transparent text-gray-200 text-center rounded-full font-mono text-xl"
                         :min="1" :max="4096"
                         v-model="input.vlan"
                         placeholder="vlan" />
          </div>
          <Button @click="load_vlan_traceroute" text severity="secondary" :loading="vlanTracerouteStarted" >
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-bezier2" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M1 2.5A1.5 1.5 0 0 1 2.5 1h1A1.5 1.5 0 0 1 5 2.5h4.134a1 1 0 1 1 0 1h-2.01c.18.18.34.381.484.605.638.992.892 2.354.892 3.895 0 1.993.257 3.092.713 3.7.356.476.895.721 1.787.784A1.5 1.5 0 0 1 12.5 11h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5H6.866a1 1 0 1 1 0-1h1.711a2.839 2.839 0 0 1-.165-.2C7.743 11.407 7.5 10.007 7.5 8c0-1.46-.246-2.597-.733-3.355-.39-.605-.952-1-1.767-1.112A1.5 1.5 0 0 1 3.5 5h-1A1.5 1.5 0 0 1 1 3.5v-1zM2.5 2a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1zm10 10a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1z"/>
            </svg>
          </Button>
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

      <div class="flex flex-col gap-2">
        <div class="flex items-center gap-3">
          <ToggleSwitch input-id="adminDownPorts" v-model="vlanTracerouteOptions.adminDownPorts"/>
          <label for="adminDownPorts">Указывать выключенные порты</label>
        </div>

        <div class="flex items-center gap-3">
          <ToggleSwitch input-id="showEmptyPorts" v-model="vlanTracerouteOptions.showEmptyPorts"/>
          <label for="showEmptyPorts">Показывать пустые порты</label>
        </div>

        <div class="flex items-center gap-3">
          <ToggleSwitch input-id="doubleCheckVlan" v-model="vlanTracerouteOptions.doubleCheckVlan"/>
          <label for="doubleCheckVlan">Двухстороннее соответствие VLAN на соседних портах</label>
        </div>
      </div>

      <div class="flex gap-3 items-center pt-4">
        <InputGroup unstyled>
          <Button icon="pi pi-minus" text @click="vlanTracerouteOptions.graphMinLength>1?vlanTracerouteOptions.graphMinLength--:null"/>
          <InputNumber v-model="vlanTracerouteOptions.graphMinLength" :min="1" :max="100"
                       input-class="w-10 bg-transparent text-gray-200 text-center border-0 font-mono text-xl"/>
          <Button icon="pi pi-plus" text @click="vlanTracerouteOptions.graphMinLength++" />
        </InputGroup>
        <div>Минимальное количество узлов в одном графе</div>
      </div>

    </div>

    <div v-show="tracerouteMode === 'mac'">
      <div class="row">
        <div class="flex items-center">
          <h4 class="text-gray-200 py-3 m-0 me-2 text-2xl">MAC Traceroute</h4>
          <div class="d-flex py-2 text-light" style="vertical-align: middle">

            <!--                RAN WITH PROGRESS-->
            <div v-if="macScanStatus.running && macScanStatus.progress && macScanStatus.progress > 0" class="d-flex">
              <div class="spinner-border me-2" role="status"></div>
              <div style="display: flex; align-items: center;">Сканирование завершено на {{ macScanStatus.progress }}%
              </div>
            </div>

            <!--                ALREADY RAN-->
            <div v-else-if="macScanStatus.running" class="spinner-border me-2" role="status"></div>

            <!--                RUN MAC SCAN-->
            <div v-else-if="!macScanStatus.running && macScanStatus.available">
              <svg style="cursor: pointer" @click="macScanStatus.run_vlans_scan" xmlns="http://www.w3.org/2000/svg"
                   width="24" height="24" fill="white" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"></path>
                <path
                    d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"></path>
              </svg>
            </div>

            <!--                ERROR-->
            <div v-else>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" class="bi bi-x-circle"
                   viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path
                    d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
              </svg>
            </div>

          </div>
        </div>

        <div class="my-3 flex items-center gap-3">
          <div>
            <InputText @keyup.enter="load_mac_traceroute"
                         class="w-50 bg-transparent text-gray-200 text-center rounded-full font-mono text-xl" :min="1" :max="4096"
                         v-model="input.mac"
                         placeholder="MAC" />
          </div>
          <Button v-if="!macTracerouteStarted" @click="load_mac_traceroute" text>
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-bezier2"
                 viewBox="0 0 16 16">
              <path fill-rule="evenodd"
                    d="M1 2.5A1.5 1.5 0 0 1 2.5 1h1A1.5 1.5 0 0 1 5 2.5h4.134a1 1 0 1 1 0 1h-2.01c.18.18.34.381.484.605.638.992.892 2.354.892 3.895 0 1.993.257 3.092.713 3.7.356.476.895.721 1.787.784A1.5 1.5 0 0 1 12.5 11h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5H6.866a1 1 0 1 1 0-1h1.711a2.839 2.839 0 0 1-.165-.2C7.743 11.407 7.5 10.007 7.5 8c0-1.46-.246-2.597-.733-3.355-.39-.605-.952-1-1.767-1.112A1.5 1.5 0 0 1 3.5 5h-1A1.5 1.5 0 0 1 1 3.5v-1zM2.5 2a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1zm10 10a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1z"/>
            </svg>
          </Button>
        </div>
      </div>
    </div>

    <!--LOAD TRACEROUTE-->
    <div v-if="vlanTracerouteStarted || macTracerouteStarted">
      <div style="text-align: center">
        <div class="me-2 spinner-border text-primary" role="status"
             style="text-align: center;height: 200px;width: 200px;"></div>
      </div>
    </div>

    <div style="background-color: #222222; height: 100%" class="my-4">
      <!--TRACEROUTE-->
      <div v-show="tracerouteMode === 'vlan'">
        <Button v-if="vlanTracerouteOptions.rendered" @click="toggleMaximizeVlanTraceroute"
                icon="pi pi-expand"/>
        <div id="vlan-network" :class="vlanTracerouteOptions.maximized?'maximized':''"></div>
      </div>

      <div v-show="tracerouteMode === 'mac'">
        <Button v-if="macTracerouteOptions.rendered" @click="toggleMaximizeMACTraceroute"
                icon="pi pi-expand"/>
        <div id="mac-network" :class="macTracerouteOptions.maximized?'maximized':''"></div>
      </div>
    </div>

  </div>

  <Button v-if="macTracerouteOptions.maximized" @click="toggleMaximizeMACTraceroute"
          class="!absolute z-10 top-5 left-5" icon="pi pi-expand"/>
  <Button v-if="vlanTracerouteOptions.maximized" @click="toggleMaximizeVlanTraceroute"
          class="!absolute z-10 top-5 left-5" icon="pi pi-expand"/>
</template>

<script lang="ts">
import {defineComponent} from "vue";

import api from "@/services/api";
import TracerouteNetwork from "./net";
import Header from "@/components/Header.vue";
import ScanStatus, {getInputVlanInfo} from "@/services/traceroute";
import {InputNumberInputEvent} from "primevue";

export default defineComponent({
  name: 'Traceroute',
  components: {Header},
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
        vlan: null,
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
        maximized: false,
        rendered: false,
      },

      macTracerouteOptions: {
        maximized: false,
        rendered: false,
      },

      vlanNetwork: new TracerouteNetwork("vlan-network"),
      macNetwork: new TracerouteNetwork("mac-network")

    }
  },

  created() {
    this.vlanScanStatus.checkScanStatus();
    this.macScanStatus.checkScanStatus();
    document.body.classList.add('traceroute-back')
  },

  unmounted() {
    document.body.classList.remove("traceroute-back")
  },

  methods: {

    getInputVlanInfo(event: InputNumberInputEvent) {
      const vid = parseInt(event.value?.toString() || "")
      getInputVlanInfo(vid).then(value => this.inputVlanInfo = value);
    },

    // Метод, который переключает значение свойства `tracerouteMode` между `vlan` и `mac`.
    toggleMode() {
      if (this.tracerouteMode === 'vlan') {
        this.tracerouteMode = 'mac';
      } else if (this.tracerouteMode === 'mac') {
        this.tracerouteMode = 'vlan';
      }
    },

    /**
     * Метод, возвращающий копию объекта baseVisOptions с изменениями, в зависимости от значения свойства tracerouteMode.
     */
    getVisOptions(...update: any): any {
      if (!update) update = {};

      if (this.tracerouteMode === 'vlan') {
        this.vlanNetwork.options.edges.arrows.middle.enabled = false;
        return {...this.vlanNetwork.options, ...update};

      } else {
        this.macNetwork.options.edges.arrows.middle.enabled = true;
        return {...this.macNetwork.options, ...update};
      }

    },

    /**
     * Отправляем на сервер запрос трассировки указанного в поле для ввода VLAN
     * И создаем в определенном блоке граф для данной трассировки.
     */
    load_vlan_traceroute() {
      if (!this.input.vlan) return;

      this.vlanTracerouteStarted = true

      let url = '/tools/api/vlan-traceroute?vlan=' + this.input.vlan +
          '&ep=' + this.vlanTracerouteOptions.showEmptyPorts +
          '&ad=' + this.vlanTracerouteOptions.adminDownPorts +
          '&double_check=' + this.vlanTracerouteOptions.doubleCheckVlan +
          '&graph_min_length=' + this.vlanTracerouteOptions.graphMinLength

      api.get(url)
          .then(
              (resp) => {
                this.vlanNetwork.renderVisualData(resp.data.nodes, resp.data.edges);
                this.vlanTracerouteStarted = false;
                this.vlanTracerouteOptions.rendered = true;
              }
          ).catch(
          () => this.vlanTracerouteStarted = false
      )

    },

    toggleMaximizeVlanTraceroute() {
      this.vlanTracerouteOptions.maximized = !this.vlanTracerouteOptions.maximized;
      if (this.vlanTracerouteOptions.maximized) {
        setTimeout(() => document.getElementById("vlan-network")!.scrollIntoView({behavior: "instant", block: "end"}))
      }
    },
    toggleMaximizeMACTraceroute() {
      this.macTracerouteOptions.maximized = !this.macTracerouteOptions.maximized;
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

      api.get(url)
          .then(
              resp => {
                this.macNetwork.renderVisualData(resp.data.nodes, resp.data.edges);
                this.macTracerouteStarted = false;
                this.macTracerouteOptions.rendered = true;
              }
          )
          .catch(
              () => this.macTracerouteStarted = false
          )
    },

  }
});
</script>

<style scoped>
.maximized {
  position: absolute;
  top: 0;
  left: 0;
  background-color: #121212;
  height: 100vh;
  width: 100vw;
  max-height: 100%;
  max-width: 100%;
}
</style>
