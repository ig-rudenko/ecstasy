<template>
<div id="device">

  <Toast/>

    <div class="row mb-3">
      <div class="col" style="padding: 0">
        <div class="card shadow">
          <div class="card-body text-center">
    <!--    Имя оборудования и его статус-->
            <DeviceStatusName
                    v-if="generalInfo"
                    :status="deviceAvailable"
                    :device-name="deviceName"
                    :device-ip="generalInfo.deviceIP"/>
          </div>
        </div>
      </div>
    </div>

    <div class="row" style="padding-bottom: 5px;">

      <div class="col-md-4">
        <div class="card shadow" style="min-height: 220px">
          <div class="card-body">
      <!--  Время обновления интерфейсов-->
            <InterfacesHelpText
                @update="updateCurrentStatus"
                :time-passed="timePassedFromLastUpdate"
                :device-status="deviceAvailable"
                :auto-update="autoUpdateInterfaces"
                :current-status="currentStatus"
                :last-interface-update="collected"/>

      <!--  Обновление интерфейсов-->
            <div style="padding: 0 10px">
            <div v-if="currentStatus" class="form-check form-switch py-3">
              <input v-model="autoUpdateInterfaces"
                     class="form-check-input" type="checkbox" role="switch" id="auto-update-interfaces">
              <label class="form-check-label" for="auto-update-interfaces">Обновлять автоматически</label>
            </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-6">
        <div v-if="generalInfo" class="card shadow" style="min-height: 220px">
            <div class="card-body button-panel">
    <!--    Кнопка для отображения панели с информацией Zabbix-->
            <div class="col-md-6">
              <ZabbixInfo :zabbix-info="generalInfo.zabbixInfo"/>
            </div>

    <!--    Ссылка на Zabbix-->
            <div class="col-md-6">
                <ToZabbixLink :zabbix-host-id="generalInfo.zabbixHostID" :zabbix-url="generalInfo.zabbixURL"/>
            </div>

    <!--    Ссылка на Elastic Stack-->
            <div class="col-md-6">
                <ElasticStackLink :logs-url="generalInfo.elasticStackLink"/>
            </div>

    <!--    Ссылка на карту-->
            <div class="col-md-6">
                <MapCoordLink :coords="generalInfo.coords"/>
            </div>

    <!--    Показать/Скрыть список конфигураций-->
            <div class="col-md-6">
               <ConfigFilesSwitchButton :config-files="configFiles" />
            </div>

            <div class="col-md-6">
                <DeviceImages :device-name="deviceName"/>
            </div>

            </div>
        </div>
      </div>

      <div class="col-md-2">
        <div class="card shadow" style="min-height: 220px">
            <div class="card-body">
        <!--  Иконки температуры, загрузки ЦП и т.д.-->
              <DeviceStats v-if="deviceStats" :stats="deviceStats"/>
            </div>
        </div>
      </div>

    </div>

<!--    Список конфигураций-->
    <div v-show="configFiles.display">
        <ConfigFiles :device-name="deviceName"/>
    </div>

<!--    Загруженность интерфейсов-->
    <DeviceWorkloadBar v-if="interfacesWorkload" :workload="interfacesWorkload" />

    <UserActionsButton :device-name="deviceName"/>

    <div class="row mb-3">
      <div class="col">
        <div class="card" style="border: none">

<!--    Таблица интерфейсов-->
        <div v-if="interfaces.length" class="table-responsive-lg">
          <table class="table head-padding">
            <thead>
              <tr>
                <th scope="col"></th>
                <th scope="col" style="text-align: center">Порт</th>
                <th scope="col" style="text-align: center">Статус</th>
                <th scope="col">Описание</th>
                <th scope="col">
                    <a style="cursor: pointer" class="text-decoration-none"
                       @click="toggleInterfacesWithVlans">
                        <span v-if="withVlans">NO VLAN's</span>
                        <span v-else>+ VLAN's</span>
                    </a>
                </th>
              </tr>
            </thead>
            <tbody style="vertical-align: middle">

            <template v-for="_interface in interfaces">
                <DetailInterfaceInfo
                        @find-mac="findMacEvent"
                        @session-mac="sessionEvent"
                        @toast="showToastError"
                        :device-name="deviceName"
                        :dynamic-opacity="dynamicOpacity"
                        :interface="_interface"
                        :permission-level="generalInfo.permission"
                        :register-comment-action="registerCommentAction"
                        :register-interface-action="registerAction"
                />
            </template>

            </tbody>
          </table>
        </div>

        <!--Собираем интерфейсы-->
        <h1 v-else class="py-5" style="text-align: center;">
            <span>Собираем интерфейсы</span>
        </h1>
        </div>
      </div>
    </div>


    <ModalPortControl :port-action="portAction" />

    <CommentControl :comment="commentObject" />

    <FindMac :mac="find_mac_address"/>

    <BrasSession
        @closed="sessionControl.display = false"
        :device-name="generalInfo.deviceName"
        :mac="sessionControl.mac"
        :port="sessionControl.port" />

    <svg xmlns="http://www.w3.org/2000/svg" style="display: none;">
      <symbol id="search-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-search" viewBox="0 0 16 16">
          <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"></path>
        </svg>
      </symbol>
      <symbol id="gear-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-gear" viewBox="0 0 16 16">
          <path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z"></path>
          <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115l.094-.319z"></path>
        </svg>
      </symbol>
      <symbol id="warning-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-exclamation-triangle" viewBox="0 0 16 16">
          <path d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.146.146 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.163.163 0 0 1-.054.06.116.116 0 0 1-.066.017H1.146a.115.115 0 0 1-.066-.017.163.163 0 0 1-.054-.06.176.176 0 0 1 .002-.183L7.884 2.073a.147.147 0 0 1 .054-.057zm1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566z"></path>
          <path d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995z"></path>
        </svg>
      </symbol>
      <symbol id="cable-diag-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-ethernet" viewBox="0 0 16 16">
          <path d="M14 13.5v-7a.5.5 0 0 0-.5-.5H12V4.5a.5.5 0 0 0-.5-.5h-1v-.5A.5.5 0 0 0 10 3H6a.5.5 0 0 0-.5.5V4h-1a.5.5 0 0 0-.5.5V6H2.5a.5.5 0 0 0-.5.5v7a.5.5 0 0 0 .5.5h11a.5.5 0 0 0 .5-.5ZM3.75 11h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm2 0h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm1.75.25a.25.25 0 0 1 .25-.25h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5ZM9.75 11h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5a.25.25 0 0 1 .25-.25Zm1.75.25a.25.25 0 0 1 .25-.25h.5a.25.25 0 0 1 .25.25v1.5a.25.25 0 0 1-.25.25h-.5a.25.25 0 0 1-.25-.25v-1.5Z"></path>
          <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2ZM1 2a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2Z"></path>
        </svg>
      </symbol>
      <symbol id="state-open-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-circle" viewBox="0 0 16 16">
          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
        </svg>
      </symbol>
      <symbol id="state-short-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-slash-circle" viewBox="0 0 16 16">
          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
          <path d="M11.354 4.646a.5.5 0 0 0-.708 0l-6 6a.5.5 0 0 0 .708.708l6-6a.5.5 0 0 0 0-.708z"></path>
        </svg>
      </symbol>
    </svg>

</div>

<ScrollTop/>

</template>

<script lang="ts">
import {defineComponent} from "vue";
import ScrollTop from "primevue/scrolltop";
import Toast from "primevue/toast";

import DeviceStatusName from "./components/DeviceStatus&Name.vue";
import ElasticStackLink from "./components/ElasticStackLink.vue";
import MapCoordLink from "./components/MapCoordLink.vue";
import ToZabbixLink from "./components/ToZabbixLink.vue";
import ZabbixInfo from "./components/ZabbixInfo.vue";
import InterfacesHelpText from "./components/InterfacesHelpText.vue";
import ModalPortControl from "../../components/ModalPortControl.vue";
import DeviceStats from "./components/DeviceStats.vue";
import CommentControl from "../../components/CommentControl.vue";
import DeviceWorkloadBar from "../../components/DeviceWorkloadBar.vue";
import DetailInterfaceInfo from "./components/DetailInterfaceInfo.vue";
import FindMac from "../../components/FindMac.vue";
import BrasSession from "../../components/BrasSession.vue";
import ConfigFiles from "../../components/ConfigFiles.vue";
import ConfigFilesSwitchButton from "../../components/ConfigFilesSwitchButton.vue";
import DeviceImages from "./components/DeviceImages.vue";
import UserActionsButton from "./components/UserActionsButton.vue";
import {Interface, newInterfacesList, InterfacesCount, newInterfacesCount} from "../../types/interfaces";
import api_request from "../../api_request";

import {HardwareStats, newHardwareStats} from "./hardwareStats";
import {GeneralInfo, newGeneralInfo} from "./GeneralInfo";
import InterfaceComment from "../../types/comments";

export default defineComponent({
  name: 'device',

  components: {
    UserActionsButton,
    DeviceImages,
    DeviceWorkloadBar,
    DetailInterfaceInfo,
    ConfigFiles,
    ConfigFilesSwitchButton,
    FindMac,
    DeviceStatusName,
    ElasticStackLink,
    InterfacesHelpText,
    MapCoordLink,
    ToZabbixLink,
    ZabbixInfo,
    ModalPortControl,
    DeviceStats,
    CommentControl,
    BrasSession,
    ScrollTop,
    Toast,
  },

  data() {
    return {
      deviceStats: {} as HardwareStats,
      interfacesWorkload: {} as InterfacesCount,
      generalInfo: {} as GeneralInfo,
      interfaces: [] as Array<Interface>,

      timePassedFromLastUpdate: "",
      collected: new Date(Date.now()) as Date, // Дата и время сбора интерфейсов
      seconds_pass: 0,

      deviceAvailable: -1, // Оборудование доступно?
      withVlans: false, // Собирать VLAN?
      currentStatus: false, // Собирать интерфейсы в реальном времени?
      autoUpdateInterfaces: true, // Автоматически обновлять интерфейсы

      deviceName: decodeURI(window.location.pathname).split('/').slice(-1).join(""),

      commentObject: {
        id: -1,
        text: "",
        user: "",
        action: "" as ("add" | "update" | "delete"),
        interface: "",
        submit: null as any
      },

      find_mac_address: "",
      sessionControl: {
        mac: "",
        port: "",
        display: false,
      },

      portAction: {
        name: "",
        action: "" as (string | null),
        submit: null as any,
        port: "",
        desc: ""
      },

      configFiles: {
        display: false
      },

    }
  },

  computed: {
    dynamicOpacity(): {opacity: number} {
      if (this.deviceAvailable === -1 || this.seconds_pass >= 60) {
        return {'opacity': 0.6}
      }
      return {'opacity': 1}
    },
  },

  mounted() {
    this.getInfo()

    // Смотрим предыдущую загруженность интерфейсов оборудования
    this.getInterfacesWorkload()

    // Сначала смотрим предыдущие интерфейсы
    this.getInterfaces()?.then(
    () => {
        // Далее опрашиваем текущий статус интерфейсов
        this.currentStatus = true

        this.timer()

        // Смотрим информацию оборудования
        this.getStats()

        // Смотрим текущую загруженность интерфейсов оборудования
        this.getInterfacesWorkload()
      }
    )

  },

  methods: {

    findMacEvent(mac: string) {
      this.find_mac_address = mac
    },

    sessionEvent(mac: string, port: string) {
      this.sessionControl = {mac: mac, port: port, display: true}
    },

    /** Собираем информацию о CPU, RAM, flash, temp */
    getStats(): void {
      let url = "/device/api/" + this.deviceName + "/stats"
      api_request.get(url).then(
          (value: any) => {this.deviceStats = newHardwareStats(value.data)},
          (reason: any) => this.showToastError(reason)
      ).catch(
          (reason: any) => this.showToastError(reason)
      )
    },

    getInterfacesWorkload() {
      let url = "/device/api/workload/interfaces/" + this.deviceName
      api_request.get(url).then(
          (value: any) => {this.interfacesWorkload = newInterfacesCount(value.data)},
          (reason: any) => this.showToastError(reason)
      ).catch(
          (reason: any) => this.showToastError(reason)
      )
    },

    /** Смотрим информацию про оборудование */
    getInfo() {
      let url = "/device/api/" + this.deviceName + "/info"
      api_request.get(url).then(
          (value: any) => {this.generalInfo = newGeneralInfo(value.data); this.deviceName=this.generalInfo.deviceName},
          (reason: any) => this.showToastError(reason)
      ).catch(
          (reason: any) => this.showToastError(reason)
      )
    },

    /** Смотрим интерфейсы оборудования */
    getInterfaces(infinity = true): Promise<void> | undefined {

      // Если автообновление интерфейсов отключено, то ожидаем 2сек и запускаем метод снова
      if (!this.autoUpdateInterfaces) {
        setTimeout(this.getInterfaces, 2000)
        return
      }

      let url = "/device/api/" + this.deviceName + "/interfaces?"
      if (this.withVlans) { url += "vlans=1" } else { url += "vlans=0" }
      if (this.currentStatus) { url += "&current_status=1" }

      return api_request.get(url).then(
          (value: any) => {
            this.interfaces = newInterfacesList(value.data.interfaces);
            this.collected = new Date(value.data.collected);
            this.deviceAvailable = value.data.deviceAvailable?1:0;
            // Если оборудование недоступно, то автообновление тоже недоступно
            this.autoUpdateInterfaces = Boolean(this.autoUpdateInterfaces && this.deviceAvailable);

            // Через 4 сек запускаем метод снова
            if (infinity) setTimeout(this.getInterfaces, 4000);
          },
          (reason: any) => this.showToastError(reason)
      ).catch(
          (reason: any) => this.showToastError(reason)
      )

    },

    toggleInterfacesWithVlans() {
      this.withVlans = !this.withVlans;
      if (this.withVlans) {
        this.currentStatus = false;
        this.getInterfaces(false);
        this.currentStatus = true;
      }
    },

    /**
     * Регистрируем новое действие над комментариями.
     * Обновляем объект `commentObject`
     *
     * @param action Действие: ('add', 'update' или 'delete')
     * @param comment Объект комментария из БД ('id', 'text', 'username')
     * @param interfaceName Название интерфейса
     */
    registerCommentAction(action: "add" | "update" | "delete", comment: InterfaceComment, interfaceName: string) {
      if (action === "add") {
        this.commentObject = {
          id: -1,
          text: '',
          user: '',
          action: action,
          interface: interfaceName,
          submit: this.submitCommentAction
        }
      } else if (comment.id && (action === "update" || action === "delete")) {
        this.commentObject = {
          id: comment.id,
          text: comment.text,
          user: comment.user,
          action: action,
          interface: interfaceName,
          submit: this.submitCommentAction
        }
      }
    },

    /**
     * Регистрируем действие над состоянием порта.
     * @param action Действие: ("up", "down", "reload")
     * @param port Название порта
     * @param description Описание порта
     */
    registerAction (action: "up" | "down" | "reload", port: string, description: string): void {
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

      let actionName: string
      if (action === "up") {
        actionName = "включить"
      } else if (action === "down") {
        actionName = "выключить"
      } else {
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
     * @param saveConfig Сохранять конфигурацию?
     */
    submitPortAction(saveConfig: boolean): void {
      let data = {
        port: this.portAction.port,       // Сам порт
        desc: this.portAction.desc,       // Описание порта
        status: this.portAction.action,   // Что сделать с портом
        save: saveConfig,                 // Сохранить конфигурацию после действия?
      }

      api_request.post("/device/api/" + this.deviceName + "/port-status", data)
          .then(
              value => {
                if (value.data.detail) {
                    this.$toast.add({ severity: "error", summary: "ERROR", detail: value.data.detail, life: 5000 })
                } else {
                    this.$toast.add({
                      severity: value.data.save?"success":"info",
                      summary: `Порт: ${value.data.port}`,
                      detail: `Состояние: ${value.data.status.toUpperCase()}<br> Конфигурация была сохранена!`,
                      life: 5000
                    })
                }
              },
              (reason: any) => this.showToastError(reason)
          )
          .catch(
              (reason: any) => this.showToastError(reason)
          )
    },

    /**
     * Подтверждаем действие над выбранным комментарием
     */
    submitCommentAction () {
      let new_comment = this.commentObject.text
      let method: "post" | "patch" | "delete"
      let data: any
      let url: string = "/device/api/comments"

      // Добавляем новый комментарий
      if (this.commentObject.action === "add" && new_comment.length) {
        method = "post"
        data = {
          device: this.deviceName,
          comment: new_comment,
          interface: this.commentObject.interface
        }
      } else if (this.commentObject.action === "update" && new_comment.length) {
        // Обновление комментария на порту
        url = "/device/api/comments/" + this.commentObject.id
        method = "patch"
        data = { comment: new_comment }
      } else {
        // Удаление комментария на порту
        url = "/device/api/comments/" + this.commentObject.id
        method = "delete"
        data = {}
      }

      api_request[method](url, data)
          .then(
              () => {
                let message: string = method==="patch"?"обновлен":method==="post"?"создан":"удален"
                this.$toast.add({ severity: "success", summary: "ОК", detail: "Комментарий был "+message, life: 5000 })
              },
              (reason: any) => this.showToastError(reason)
          )
          .catch((reason: any) => this.showToastError(reason))
    },

    /**
     * Переводит режим обновления интерфейсов в обнаружение в реальном времени
     * и включает автоматическое обновление
     */
    updateCurrentStatus () {
      this.currentStatus = true
      this.autoUpdateInterfaces = true
    },

    /**
     * Таймер для вычисления времени прошедшего с момента последнего обнаружения интерфейсов.
     */
    timer() {
      this.seconds_pass = Math.round((Date.now() - this.collected.getTime()) / 1000)

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


    showToastError(reason: any, text: string = "") {
      this.$toast.add({ severity: "error", summary: "ERROR! status:" + reason.response.status,
        detail: text + ". Причина: " + reason.response.data?.detail, life: 5000 })
    }

  },
});
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

.button-panel {
  display: flex!important;
  flex-wrap: wrap;
  flex-direction: row;
  align-items: center;
}
</style>