<template src="./App_traceroute.html"></template>

<script>
import api_request from "./api_request.js";

export default {
  name: 'app',
  data() {
    return {
      macScanIcon: "",
      // Свойство данных, которое используется для хранения состояния сканирования.
      vlanScanStatus: {
        running: false,
        progress: null,
        available: false
      },
      // Свойство данных, которое используется для хранения состояния сканирования.
      macScanStatus: {
        running: false,
        progress: null,
        available: false
      },

      vlanTracerouteStarted: false,
      macTracerouteStarted: false,

      // Установка значения по умолчанию для свойства tracerouteMode.
      tracerouteMode: 'vlan',

      // Пользовательский ввод
      inputVlan: "",
      inputMac: "",

      inputVlanInfo: {
        name: "",
        description: ""
      },

      // Свойство данных, которое используется для хранения состояния флажков.
      vlanTracerouteOptions: {
        adminDownPorts: false,
        showEmptyPorts: false,
        doubleCheckVlan: true,
        graphMinLength: 3,
      },

      // Базовая конфигурация для сети vis.js.
      baseVisOptions: {
          height: '900',
          locale: 'ru',
          configure: {
              enabled: false
          },
          layout: {
              randomSeed: 12345
          },
          edges: {
              smooth: {
                  enabled: true,
                  type: "dynamic"
              },
              arrows: {
                  middle: {
                      enabled: true
                  }
              },
          },
          interaction: {
              dragNodes: true,
              hideEdgesOnDrag: false,
              hideNodesOnDrag: false
          },
          physics: {
              enabled: true,
              repulsion: {
                  centralGravity: 0.2,
                  damping: 0.89,
                  nodeDistance: 130,
                  springConstant: 0.05,
                  springLength: 200
              },
              solver: 'repulsion',
              stabilization: {
                  enabled: true,
                  fit: true,
                  iterations: 1000,
                  onlyDynamicEdges: false,
                  updateInterval: 50
              }
          },
          nodes: {
              size: 14,
              font:{
                  color:'#eeeeee',
                  size: 12
              }
          }
      }
    }
  },

  // Хук жизненного цикла, который вызывается после создания экземпляра.
  created() {
    this.check_vlans_scan_status()
    this.check_mac_scan_status()
  },

  methods: {

    getInputVlanInfo() {
      api_request.get("/tools/ajax/vlan_desc?vlan="+this.inputVlan)
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

    // Проверяем, запущено ли сканирование vlan.
    check_vlans_scan_status() {
      api_request.get("/tools/ajax/vlans-scan/check")
          .then(
              resp => {
                if (!resp.data.status) {
                  this.vlanScanStatus = { available: true, running: false, progress: null }
                } else {
                  this.vlanScanStatus = { available: false, running: true, progress: resp.data.progress }
                }
              }
          )
          .catch(
              () => {
                this.vlanScanStatus = { available: false, running: false, progress: null }
              }
          )

      setTimeout(this.check_vlans_scan_status, 5000);
    },

    // Метод, который отправляет POST-запрос на сервер для запуска сканирования vlan.
    run_vlans_scan() {
      if (!this.vlanScanStatus.available) return;

      api_request.post("/tools/ajax/vlans-scan/run")
          .then(
              () => {
                this.vlanScanStatus.available = false;
                this.vlanScanStatus.running = true;
              }
          )
          .catch(
              () => {
                this.vlanScanStatus.available = false
                this.vlanScanStatus.running = false
              }
          )

    },


    // Проверяем, запущено ли сканирование vlan.
    check_mac_scan_status() {
      api_request.get("/gather/mac-scan/check")
          .then(
              resp => {
                if (!resp.data.status) {
                  this.macScanStatus = { available: true, running: false, progress: null }
                } else {
                  this.macScanStatus = { available: false, running: true, progress: resp.data.progress }
                }
              }
          )
          .catch(() => {this.macScanStatus = { available: false, running: true, progress: null }})

      setTimeout(this.check_mac_scan_status, 5000);
    },

    // Метод, который отправляет POST-запрос на сервер для запуска сканирования mac.
    run_mac_scan() {
      // Проверка доступности macScanStatus.
      if (!this.macScanStatus.available) return;

      api_request.post("/gather/mac-scan/run")
          .then(
              () => {
                this.macScanStatus.available = false
                this.macScanStatus.running = true
              }
          ).catch(
              () => {
                this.macScanStatus.available = false;
                this.macScanStatus.running = false
              }
          )

    },

    /**
     * Метод, возвращающий копию объекта baseVisOptions с изменениями, в зависимости от значения свойства tracerouteMode.
     */
    getVisOptions(...update){
      if (this.tracerouteMode==='vlan'){
        this.baseVisOptions.edges.arrows.middle.enabled = false

      } else if (this.tracerouteMode==='mac') {
        this.baseVisOptions.edges.arrows.middle.enabled = true
      }
      return {...this.baseVisOptions, ...update}
    },

    /**
     * Функция, которая принимает три аргумента: узлы, ребра и element_id. Он создает новый объект vis.Network и передает
     * ему элемент с идентификатором, равным element_id, узлы и ребра, а также параметры.
     * @param nodes {Array}
     * @param edges {Array}
     * @param element_id {String}
     * @param options {null|Object}
     */
    render_visual_data: function (nodes, edges, element_id, options=null) {
      // Создает новый объект vis.Network.
      new vis.Network(
          // Получение элемента с идентификатором `element_id` и передача его конструктору vis.Network.
          document.getElementById(element_id),
          // Создание нового объекта DataSet и передача его конструктору vis.Network.
          {
              nodes: new vis.DataSet(nodes),
              edges: new vis.DataSet(edges)
          },
          // Метод, возвращающий копию объекта baseVisOptions с изменениями в зависимости от значения свойства
          // tracerouteMode.
          this.getVisOptions(options)
      );
    },

    // Проверяет, действителен ли vlan.
    validateVlan(vlan_str) {
      // Это регулярное выражение, которое проверяет, является ли строка числом.
      if (!/^\d+$/.test(vlan_str)) return 0;
      // Он преобразует строку в число.
      let vlan = Number(vlan_str)
      // Это простая проверка, чтобы убедиться, что vlan действителен.
      if (vlan > 0 && vlan <= 4096) return vlan;
      return 0
    },


    /**
     * Отправляем на сервер запрос трассировки указанного в поле для ввода VLAN
     * И создаем в определенном блоке граф для данной трассировки.
     * @returns {Promise<void>}
     */
    async load_vlan_traceroute() {
      // Проверяем, действителен ли vlan.
      let valid_vlan = this.validateVlan(this.inputVlan)
      if (valid_vlan === 0) return;

      this.vlanTracerouteStarted = true

      let url = '/tools/ajax/vlantraceroute?vlan=' + this.inputVlan +
          '&ep=' + this.vlanTracerouteOptions.showEmptyPorts +
          '&ad=' + this.vlanTracerouteOptions.adminDownPorts +
          '&double-check=' + this.vlanTracerouteOptions.doubleCheckVlan +
          '&graph-min-length=' + this.vlanTracerouteOptions.graphMinLength

      api_request.get(url)
          .then(
              resp => {
                this.render_visual_data(resp.data.nodes, resp.data.edges, "vlan-network", resp.data.options.physics);
                this.vlanTracerouteStarted = false;
              }
          ).catch(
              reason => {this.vlanTracerouteStarted = false}
          )

    },

    // Удаляет из MAC адреса все символы, не являющиеся шестнадцатеричными.
    validateMac(mac_str) {
      return String(mac_str).replace(/\W/g, "")
    },


    /**
     * Отправляем на сервер запрос трассировки указанного в поле для ввода MAC.
     * И создаем в определенном блоке граф для данной трассировки.
     * @returns {Promise<void>}
     */
    async load_mac_traceroute() {
      let valid_mac = this.validateMac(this.inputMac)
      if (!valid_mac.length) return

      this.macTracerouteStarted = true
      const url = '/gather/api/traceroute/mac-address/' + valid_mac + "/"

      api_request.get(url)
          .then(
              resp => {
                this.render_visual_data(resp.data.nodes, resp.data.edges, "mac-network");
                this.macTracerouteStarted = false;
              }
          )
          .catch(
              reason => {this.macTracerouteStarted = false}
          )
    },

  }
}
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
.cursor-pointer {
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
