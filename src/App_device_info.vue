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
import CommentControl from "./components/CommentControl.vue";
import Comment from "./components/Comment.vue";
import PortControlButtons from "./components/PortControlButtons.vue";

export default {
  name: 'device',
  data() {
    return {
      deviceStats: {},

      timePassedFromLastUpdate: null,
      collected: "new", // Дата и время сбора интерфейсов
      seconds_pass: 0,

      errorStatus: "", // Ошибка сбора интерфейсов
      deviceAvailable: -1, // Оборудование доступно?
      permissionLevel: 0, // Уровень привилегий пользователя
      withVlans: false, // Собирать VLAN?
      autoUpdateInterfaces: true, // Автоматически обновлять интерфейсы

      deviceName: window.location.pathname.split('/').slice(-1).join(""),
      deviceIP: "",

      currentStatus: false, // Собирать интерфейсы в реальном времени?
      zabbixHostID: null,
      interfaces: [],
      elasticStackLink: "", // Ссылка на логи
      deviceCoords: [],
      zabbixInfo: {},

      commentObject: {
        id: -1,
        text: "",
        user: "",
        action: "",
        interface: ""
      },

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
    dynamicOpacity: function () {
      if (this.deviceAvailable === -1 || this.seconds_pass >= 60) {
        return {'opacity': 0.6}
      }
    },
  },

  async mounted() {
    this.csrf_token = $("input[name=csrfmiddlewaretoken]")[0].value
    await this.getInfo()

    // Сначала смотрим предыдущие интерфейсы
    let response = await fetch(
        "/device/api/" + this.deviceName + "/interfaces?vlans=1",
        {method: "GET", credentials: "same-origin"}
    );
    let data = await response.json()
    this.interfaces = data.interfaces
    this.collected = new Date(data.collected)

    // Далее опрашиваем текущий статус интерфейсов
    this.currentStatus = true

    this.timer()

    await this.getInterfaces()
    await this.getStats()
    this.toastObject = $(".toast")
  },

  methods: {
    /** Собираем информацию о CPU, RAM, flash, temp */
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
        // this.currentStatus = this.deviceAvailable

        // Если оборудование недоступно, то автообновление тоже недоступно
        this.autoUpdateInterfaces = Boolean(this.autoUpdateInterfaces && this.deviceAvailable)

      } catch (error) {
        console.log(error)
      }

      // Через 4 сек запускаем метод снова
      setTimeout(this.getInterfaces, 4000)
    },

    /**
     * Регистрируем новое действие над комментариями.
     * Обновляем объект `commentObject`
     *
     * @param action Действие: ('add', 'update' или 'delete')
     * @param comment Объект комментария из БД ('id', 'text', 'username')
     * @param interface_name Название интерфейса
     */
    registerCommentAction: function (action, comment, interface_name) {
      if (action === "add") {
        this.commentObject = {
          text: '',
          user: '',
          action: action,
          interface: interface_name,
          submit: this.submitCommentAction
        }
      } else if (comment && (action === "update" || action === "delete")) {
        this.commentObject = {
          id: comment.id,
          text: comment.text,
          user: comment.user,
          action: action,
          interface: interface_name,
          submit: this.submitCommentAction
        }
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
     * Регистрируем действие над состоянием порта.
     *
     * @param action Действие: ("up", "down", "reload")
     * @param port Название порта
     * @param description Описание порта
     */
    registerAction: function (action, port, description) {

      if (["up", "down", "reload"].indexOf(action) < 0) {
        // Если неверное действие
        this.portAction = {
          name: "",
          action: null,
          port: "",
          desc: "",
          submit: null
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

    /**
     * Подтверждаем действие над выбранным портом
     *
     * @param save_config Сохранять конфигурацию?
     */
    submitPortAction: function (save_config) {
      let toastInfo = this.toastInfo
      let toast = this.toastObject

      let data = {
        port: this.portAction.port,       // Сам порт
        device: this.deviceName,          // Имя оборудования
        desc: this.portAction.desc,       // Описание порта
        status: this.portAction.action,   // Что сделать с портом
        save: save_config,                // Сохранить конфигурацию после действия?
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

    /**
     * Подтверждаем действие над выбранным комментарием
     */
    submitCommentAction: function () {
      let new_comment = this.commentObject.text

      // Добавляем новый комментарий
      if (this.commentObject.action === "add" && new_comment.length) {
        $.ajax({
            url: "/device/api/" + this.deviceName + '/add-comment',
            type: 'POST',
            data: {
              csrfmiddlewaretoken: this.csrf_token,
              device: this.deviceName,
              comment: new_comment,
              interface: this.commentObject.interface
            },
            success: function( data ) {
              console.log(data)
            },
            error: function (data) {
              console.log(data)
            }
        });
      }

      // Обновление комментария на порту
      if (this.commentObject.action === "update" && new_comment.length) {
        $.ajax({
            url: "/device/api/comment/" + this.commentObject.id + "/update",
            type: 'POST',
            data: {
              csrfmiddlewaretoken: this.csrf_token,
              comment: new_comment
            },
            success: function( data ) {
              console.log(data)
            },
            error: function (data) {
              console.log(data)
            }
        });
      }

      // Удаление комментария на порту
      if (this.commentObject.action === "delete") {
        $.ajax({
            url: "/device/api/comment/" + this.commentObject.id + "/delete",
            type: 'POST',
            data: {
              csrfmiddlewaretoken: this.csrf_token,
            },
            success: function( data ) {
              console.log(data)
            },
            error: function (data) {
              console.log(data)
            }
        });
      }
    },

    /**
     * Вычисляем цвет статуса порта
     *
     * @param status Статус порта
     * @returns {{"background-color": string, width: string, "text-align": string, "opacity": number}}
     */
    statusStyleObj: function (status) {
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

    /**
     * Переводит режим обновления интерфейсов в обнаружение в реальном времени
     * и включает автоматическое обновление
     */
    updateCurrentStatus: function () {
      this.currentStatus = true
      this.autoUpdateInterfaces = true
    },

    /**
     * Таймер для вычисления времени прошедшего с момента последнего обнаружения интерфейсов.
     */
    timer: function () {
      this.seconds_pass = Math.round((Date.now() - this.collected) / 1000)

      let min_ = Math.floor(this.seconds_pass / 60);
      let sec = (this.seconds_pass - (min_ * 60)).toString()
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
    },

    addDeviceLink(interface_) {
      if (!interface_.Link) return interface_.Description || "";
      return interface_.Description.replace(
          new RegExp(interface_.Link.device_name, 'ig'),
          s => `<mark><a class="text-dark text-decoration-none" href="${interface_.Link.url}">${s}</a></mark>`)
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
    "modal-comment-control": CommentControl,
    "comment": Comment,
    "port-control-buttons": PortControlButtons,
  }
}
</script>

<style>
.btn-fog:hover svg {
    fill: currentColor;
}
.btn-fog:not(:hover) svg {
    fill: lightgrey;
}

.comment-active:hover {
    fill: #fd7e14;
}
.comment-active:not(:hover) {
    fill: #ffc107;
}

.head-padding th {
  padding: 15px;
}

.shadow {
    box-shadow: 0.4em 0.4em 5px rgb(122 122 122 / 50%);
}
</style>