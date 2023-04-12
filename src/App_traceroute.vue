<template src="./App_traceroute.html"></template>

<script>
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

      // Токен Django CSRF.
      CSRF_TOKEN: $('input[name=csrfmiddlewaretoken]')[0].value,

      // Установка значения по умолчанию для свойства tracerouteMode.
      tracerouteMode: 'vlan',

      // Пользовательский ввод
      inputVlan: "",
      inputMac: "",

      // Свойство данных, которое используется для хранения состояния флажков.
      vlanTracerouteOptions: {
        adminDownPorts: false,
        showEmptyPorts: false,
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
    async check_vlans_scan_status() {

      try {
        let resp = await fetch(
            '/tools/ajax/vlans-scan/check',
            {
              method: "GET",
              headers: {"X-CSRFToken": this.CSRF_TOKEN}
            }
        )
        let data = await resp.json()
        if (!data.status) {
          this.vlanScanStatus = { available: true, running: false, progress: null }

        } else {
          this.vlanScanStatus = { available: false, running: true, progress: data.progress }
        }

      } catch (error) {
        console.log(error)
        this.vlanScanStatus = { available: false, running: false, progress: null }
      }

      setTimeout(this.check_vlans_scan_status, 5000);
    },

    // Метод, который отправляет POST-запрос на сервер для запуска сканирования vlan.
    async run_vlans_scan() {
      if (!this.vlanScanStatus.available) return;

      try {
        let resp = await fetch(
            '/tools/ajax/vlans-scan/run',
            {
              method: "POST",
              headers: {"X-CSRFToken": this.CSRF_TOKEN}
            }
        )
        if (resp.status === 200) {
          this.vlanScanStatus.available = false
          this.vlanScanStatus.running = true
        } else {
          this.vlanScanStatus.available = false
          this.vlanScanStatus.running = false
        }

      } catch (error) {
        console.log(error)
        this.vlanScanStatus.available = false
        this.vlanScanStatus.running = false
      }
    },


    // Проверяем, запущено ли сканирование vlan.
    async check_mac_scan_status() {

      try {
        let resp = await fetch(
            '/gather/mac-scan/check',
            {
              method: "GET",
              headers: {"X-CSRFToken": this.CSRF_TOKEN}
            }
        )
        let data = await resp.json()
        if (!data.status) {
          this.macScanStatus = { available: true, running: false, progress: null }

        } else {
          this.macScanStatus = { available: false, running: true, progress: data.progress }
        }

      } catch (error) {
        console.log(error)
        this.macScanStatus = { available: false, running: true, progress: null }
      }

      setTimeout(this.check_mac_scan_status, 5000);
    },

    // Метод, который отправляет POST-запрос на сервер для запуска сканирования mac.
    async run_mac_scan() {
      // Проверка доступности macScanStatus.
      if (!this.macScanStatus.available) return;
      try {
        let resp = await fetch(
            '/gather/mac-scan/run',
            {
              method: "POST",
              headers: {"X-CSRFToken": this.CSRF_TOKEN}
            }
        )
        if (resp.status === 200) {
          this.macScanStatus.available = false
          this.macScanStatus.running = true
        } else {
          this.macScanStatus.available = false
          this.macScanStatus.running = false
        }

      } catch (error) {
        console.log(error)
        this.macScanStatus.available = false
        this.macScanStatus.running = false
      }
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
      try {
        let url = '/tools/ajax/vlantraceroute?vlan=' + this.inputVlan +
            '&ep=' + this.vlanTracerouteOptions.showEmptyPorts +
            '&ad=' + this.vlanTracerouteOptions.adminDownPorts
        let resp = await fetch(
          url,
          {
            method: "GET",
            headers: {"X-CSRFToken": this.CSRF_TOKEN}
          }
        )
        let data = await resp.json()

        // Отрисовка данных в div `vlan-network`.
        this.render_visual_data(data.nodes, data.edges, "vlan-network", data.options.physics)

      } catch (error) { console.log(error) }
      this.vlanTracerouteStarted = false
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
      try {
        // Отправка запроса GET на сервер с MAC-адресом, введенным пользователем.
        let resp = await fetch(
          '/gather/api/traceroute/mac-address/' + valid_mac + "/",
          {
            method: "GET",
            headers: {"X-CSRFToken": this.CSRF_TOKEN}
          }
        )
        // Преобразование ответа в JSON.
        let data = await resp.json()

        // Рендеринг данных в div `mac-network`.
        this.render_visual_data(data.nodes, data.edges, "mac-network")

      } catch (error) { console.log(error) }
      this.macTracerouteStarted = false
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
</style>
