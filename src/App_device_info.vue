<template src="./App_device_info.html"></template>

<script>
import DeviceStatusName from "./components/DeviceStatus&Name.vue";
import ElasticStackLink from "./components/ElasticStackLink.vue";
import MapCoordLink from "./components/MapCoordLink.vue";
import ToZabbixLink from "./components/ToZabbixLink.vue";
import ZabbixInfoPanel from "./components/ZabbixInfoPanel.vue";
import ZabbixInfoPanelButton from "./components/ZabbixInfoPanelButton.vue";
import InterfacesHelpText from "./components/InterfacesHelpText.vue";
import ModalPortControl from "./components/ModalPortControl.vue";
import InfoToast from "./components/InfoToast.vue";
import DeviceStats from "./components/DeviceStats.vue";

export default {
  name: 'device',
  data() {
    return {
      deviceStats: {},

      timePassedFromLastUpdate: null,
      collected: "new", // Дата и время сбора интерфейсов

      errorStatus: "", // Ошибка сбора интерфейсов
      deviceAvailable: -1, // Оборудование доступно?
      permissionLevel: 0, // Уровень привилегий пользователя
      withVlans: false, // Собирать VLAN?
      autoUpdateInterfaces: true, // Автоматически обновлять интерфейсы
      deviceIP: "",
      currentStatus: true, // Собирать интерфейсы в реальном времени?
      zabbixHostID: null,
      interfaces: [],
      elasticStackLink: "", // Ссылка на логи
      deviceCoords: [],
      zabbixInfo: {},

      csrf_token: null,

      portAction: {
        name: "",
        action: "",
        submit: null,
        port: "",
        desc: ""
      },

      toastObject: null,
      toastInfo: {
        title: "",
        message: "",
        color: "#ffffff"
      }
    }
  },
  computed: {
    deviceName: function () {
      return window.location.pathname.split('/').slice(-1).join("")
    }
  },

  mounted() {
    this.csrf_token = $('input[name=csrfmiddlewaretoken]')[0].value
    this.getInfo()
    this.getInterfaces()
    this.getStats()
    this.toastObject = $('.toast')
  },

  methods: {
    async getStats() {
      try {
        let url = "/device/api/" + this.deviceName + "/stats"
        let response = await fetch(url, {method: "GET", credentials: "same-origin"});

        this.deviceStats = await response.json()

      } catch (error) {
        console.log(error)
      }

      setTimeout(this.getStats, 60000)
    },

    /** Смотрим информацию про оборудование */
    async getInfo() {
      try {
        let url = "/device/api/" + this.deviceName + "/info"

        let response = await fetch(url, {method: "GET", credentials: "same-origin"});
        let data = await response.json()

        this.deviceName = data.deviceName
        this.deviceIP = data.deviceIP
        this.elasticStackLink = data.elasticStackLink
        this.zabbixHostID = data.zabbixHostID
        this.permissionLevel = data.permission
        this.deviceCoords = data.coords
        this.zabbixInfo = data.zabbixInfo

      } catch (error) {
        console.log(error)
      }
    },
    /** Смотрим интерфейсы оборудования */
    async getInterfaces() {

      // Если автообновление интерфейсов отключено, то ожидаем 2сек и запускаем метод снова
      if (!this.autoUpdateInterfaces) {
        setTimeout(this.getInterfaces, 2000)
        return
      }

      try {
        let url = "/device/api/" + this.deviceName + "/interfaces?"
        if (this.withVlans) {
          url += "vlans=1"
        } else {
          url += "vlans=0"
        }
        if (this.currentStatus) {
          url += "&current_status=1"
        }

        let response = await fetch(url, {method: "GET", credentials: "same-origin"});
        let data = await response.json()

        this.interfaces = data.interfaces
        this.collected = new Date(data.collected)
        this.deviceAvailable = data.deviceAvailable ? 1 : 0

        // Если оборудование доступно, то смотрим интерфейсы в реальном времени
        this.currentStatus = this.deviceAvailable

        // Если оборудование недоступно, то автообновление тоже недоступно
        this.autoUpdateInterfaces = Boolean(this.autoUpdateInterfaces && this.deviceAvailable)

        this.timer()

      } catch (error) {
        console.log(error)
      }

      // Через 4 сек запускаем метод снова
      setTimeout(this.getInterfaces, 4000)
    },

    intfStatusDesc: function (status) {
      if (status === "dormant") {
        return "Интерфейс ожидает внешних действий (например, последовательная линия, ожидающая входящего соединения)"
      }
      if (status === "notPresent") {
        return "Интерфейс имеет отсутствующие компоненты (как правило, аппаратные)"
      }
    },

    registerAction: function (action, port, description) {

      if (["up", "down", "reload"].indexOf(action) < 0) {
        // Если неверное действие
        this.portAction = {
          name: "",
          action: null,
          port: "",
          desc: ""
        }
      }

      let actionName
      if (action === "up") {
        actionName = "включить"
      }
      if (action === "down") {
        actionName = "выключить"
      }
      if (action === "reload") {
        actionName = "перезагрузить"
      }

      this.portAction = {
        name: actionName,
        port: port,
        desc: description,
        action: action,
        submit: this.submitPortAction
      }
    },

    submitPortAction: function (action, save_config, port, desc) {
      let toastInfo = this.toastInfo
      let toast = this.toastObject

      let data = {
        port: port,                 // Сам порт
        device: this.deviceName,    // Имя оборудования
        desc: desc,                 // Описание порта
        status: action,             // Что сделать с портом
        save: save_config,          // Сохранить конфигурацию после действия?
        csrfmiddlewaretoken: this.csrf_token
      }
      $.ajax({
          url: "/device/port/reload",
          type: 'POST',
          data: data,
          success: function( data ) {
            toastInfo.title= data.status
            toastInfo.message = data.message
            toastInfo.color = data.color
            toast.toast('show')
          },
          error: function (data) {
            console.log("error", data)
            toastInfo.title= "ERROR"
            toastInfo.message = data
            toastInfo.color = "#cb0707"
            toast.toast('show')
          }
      });
    },

    statusStyleObj: function (status) {
      status = status.toLowerCase()
      let color = function () {
        if (status === "admin down") return "#ffb4bb"
        if (status === "notpresent") return "#c1c1c1"
        if (status === "dormant") return "#ffe389"
        if (status !== "down") return "#22e58b"
      }
      return {
        'width': '150px',
        'text-align': 'center',
        'background-color': color()
      }
    },

    updateCurrentStatus: function () {
      this.currentStatus = true
      this.autoUpdateInterfaces = true
    },

    timer: function () {
      let seconds_pass = Math.round((Date.now() - this.collected) / 1000)

      let min_ = Math.floor(seconds_pass / 60);
      let sec = (seconds_pass - (min_ * 60)).toString()
      let min = min_.toString()

      let sec_str = ''
      let min_str = ''

      if (min_ !== 0) {  // Если есть минуты
          if (/1$/.test(min)) { min_str = ' минуту ' }
          if (/[2-4]$/.test(min)) { min_str = ' минуты '}
          if (/[05-9]$/.test(min)) { min_str = ' минут ' }
      } else { min = '' }

      if (/1$/.test(sec)) { sec_str = ' секунду ' }
      if (/[2-4]$/.test(sec)) { sec_str = ' секунды '}
      if (/[05-9]$/.test(sec)) { sec_str = ' секунд ' }
      if (/1\d$/.test(sec)) { sec_str = ' секунд ' }

      this.timePassedFromLastUpdate = min+min_str+sec+sec_str

      setTimeout(this.timer, 1000)
    }
  },
  components: {
    "device-status-name": DeviceStatusName,
    "elastic-link": ElasticStackLink,
    "interfaces-help": InterfacesHelpText,
    "map-link": MapCoordLink,
    "zabbix-link": ToZabbixLink,
    "zabbix-info": ZabbixInfoPanel,
    "zabbix-info-button": ZabbixInfoPanelButton,
    "modal-port-control": ModalPortControl,
    "info-toast": InfoToast,
    "device-stats": DeviceStats,
  }
}
</script>

<style>
  #control:hover svg {
      fill: currentColor;
  }
  #control:not(:hover) svg {
      fill: lightgrey;
  }
</style>