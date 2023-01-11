<template src="./App_device_info.html"></template>

<script>
import DeviceStatusName from "./components/DeviceStatus&Name.vue";
import ElasticStackLink from "./components/ElasticStackLink.vue";
import MapCoordLink from "./components/MapCoordLink.vue";
import ToZabbixLink from "./components/ToZabbixLink.vue";
import ZabbixInfoPanel from "./components/ZabbixInfoPanel.vue";
import ZabbixInfoPanelButton from "./components/ZabbixInfoPanelButton.vue";
import InterfacesHelpText from "./components/InterfacesHelpText.vue";

export default {
  name: 'device',
  data() {
    return {
      collected: "", // Дата и время сбора интерфейсов
      errorStatus: "", // Ошибка сбора интерфейсов
      deviceAvailable: -1, // Оборудование доступно?
      permissionLevel: 0, // Уровень привилегий пользователя
      withVlans: false, // Собирать VLAN?
      autoUpdateInterfaces: true, // Автоматически обновлять интерфейсы
      deviceIP: "",
      currentStatus: true, // Собирать интерфейсы в реальном времени?
      zabbixHostID: null,
      interfaces: function () { return [] },
      elasticStackLink: "", // Ссылка на логи
      deviceCoords: function () { return [] },
      zabbixInfo: function () { return {} },
    }
  },
  computed: {
    deviceName: function () {
      return window.location.pathname.split('/').slice(-1).join("")
    }
  },

  created() {
    this.getInfo()
    this.getInterfaces()
  },

  methods: {
    intfStatusDesc: function (status) {
      if (status === "dormant") {
        return "Интерфейс ожидает внешних действий (например, последовательная линия, ожидающая входящего соединения)"
      }
      if (status === "notPresent") {
        return "Интерфейс имеет отсутствующие компоненты (как правило, аппаратные)"
      }
    },
    statusStyleObj: function (status) {
      let color = function () {
        if (status === "admin down") return "#ffb4bb"
        if (status === "notPresent") return "#c1c1c1"
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
        if (this.withVlans) { url += "vlans=1" } else { url += "vlans=0" }
        if (this.currentStatus) { url += "&current_status=1" }

        let response = await fetch(url, {method: "GET", credentials: "same-origin"});
        let data = await response.json()

        this.interfaces = data.interfaces
        this.collected = data.collected
        this.deviceAvailable = data.deviceAvailable?1:0

        // Если оборудование доступно, то смотрим интерфейсы в реальном времени
        this.currentStatus = this.deviceAvailable

        // Если оборудование недоступно, то автообновление тоже недоступно
        this.autoUpdateInterfaces = Boolean(this.autoUpdateInterfaces && this.deviceAvailable)

      } catch (error) {
          console.log(error)
      }

      // Через 4 сек запускаем метод снова
      setTimeout(this.getInterfaces, 4000)
    }
  },
  components: {
    "device-status-name": DeviceStatusName,
    "elastic-link": ElasticStackLink,
    "interfaces-help": InterfacesHelpText,
    "map-link": MapCoordLink,
    "zabbix-link": ToZabbixLink,
    "zabbix-info": ZabbixInfoPanel,
    "zabbix-info-button": ZabbixInfoPanelButton
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