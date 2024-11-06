<template>
  <tr :style="lineStyle(line[1])" :class="lineClasses" class="hover:ring-1 ring-indigo-500">

    <td class="btn-fog">

      <div class="flex items-center gap-2 justify-end">

        <Comment :interface="ontInterface" :device-name="deviceName"/>
        <!--        Название Интерфейса-->
        <div @click="toggleDetailInfo" class="text-xl font-mono text-center px-4">{{ line[0] }}</div>

        <!--        Управление состоянием интерфейсов-->
        <PortControlButtons
            :device-name="deviceName"
            :interface="ontInterface"
            :permission-level="permissionLevel"/>

        <!--        Посмотреть порт -->
        <Button @click="toggleDetailInfo" text>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
            <path d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"></path>
          </svg>
        </Button>

      </div>
    </td>

    <td :style="statusStyles(line[1])" class="px-3 font-mono text-center text-gray-950">{{ line[1] }}</td>

    <!--        Последнее подключение-->
    <td class="px-3 text-sm text-muted-color text-center">{{ verboseDatetime(line[2]) }}</td>
    <!--        Последнее отключение -->
    <td class="px-3 text-sm text-muted-color text-center">{{ verboseDatetime(line[3]) }}</td>

    <!--          Причина -->
    <td class="px-3 text-sm text-center">
      {{ line[4] === "dying-gasp" ? "Предсмертный хрип" : line[4] }}
    </td>
    <!--          Дистанция -->
    <td class="px-3 font-mono text-center">
      {{ line[5] !== "-" ? line[5] + " м" : "-" }}
    </td>
    <!--         Rx/Tx мощность -->
    <td class="px-3 font-mono text-center">{{ line[6] }}</td>

  </tr>

  <tr v-if="showDetailInfo">
    <td colspan="7" v-if="complexInfo">

      <!--      DETAIL PORT INFO  -->
      <div v-if="complexInfo.portDetailInfo" class="p-6 shadow border rounded">
        <div v-if="complexInfo.portDetailInfo.type==='html'" v-html="complexInfo.portDetailInfo.data"></div>
      </div>

      <!--      ANOTHER INFO  -->
      <ComplexInterfaceInfo :complex-info="complexInfo" :interface="interface" :device-name="deviceName"/>

    </td>

    <td v-else colspan="5">
      <div class="flex justify-center">
        <ProgressSpinner/>
      </div>
    </td>
  </tr>
</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import {AxiosResponse} from "axios";

import PortControlButtons from "./PortControlButtons.vue";
import Comment from "@/components/Comment.vue";
import ComplexInterfaceInfo from "@/pages/deviceInfo/components/ComplexInterfaceInfo.vue";

import api from "@/services/api";
import {verboseDatetime} from "@/formats";
import {DeviceInterface} from "@/services/interfaces";
import {ComplexInterfaceInfoType} from "../detailInterfaceInfo";

export default defineComponent({
  components: {
    ComplexInterfaceInfo,
    PortControlButtons,
    Comment,
  },
  props: {
    interface: {required: true, type: Object as PropType<DeviceInterface>},
    deviceName: {required: true, type: String},
    permissionLevel: {required: true, type: Number},
    line: {required: true, type: Object},
  },
  data() {
    return {
      showDetailInfo: false,
      portDetailMenu: "" as '' | 'portErrors' | 'portConfig',
      ontID: this.line[0],
      complexInfo: null as ComplexInterfaceInfoType | null,
    }
  },
  computed: {
    ontInterface(): DeviceInterface {
      return {
        name: this.interface.name + "/" + this.ontID,
        status: this.line[1],
        description: "ONT: " + this.ontID + " " + this.interface.description,
        vlans: this.line[7]
      }
    },
    lineClasses() {
      if (this.showDetailInfo) return ["shadow", "sticky-top"];
      return []
    },

  },
  methods: {
    verboseDatetime,

    statusStyles(status: string): any {
      if (status === "online") return {"background-color": "#22e58b"}
      if (status === "offline") return {"background-color": "#ffcacf"}
    },
    lineStyle(status: string): any {
      if (status.toLowerCase() === "offline") return {"background-color": "rgba(255,138,148,0.5)"}
      if (this.showDetailInfo) return {"background-color": "rgba(129,164,255,0.29)", "top": "56px"}
    },

    toggleDetailInfo() {
      this.showDetailInfo = !this.showDetailInfo

      if (!this.showDetailInfo) return

      this.getDetailInfo()
    },

    getDetailInfo() {
      if (!this.showDetailInfo) return

      api.get("/device/api/" + this.deviceName + "/interface-info?port=" + this.ontInterface.name)
          .then(
              (value: AxiosResponse<ComplexInterfaceInfoType>) => {
                this.complexInfo = value.data;
              },
          )
    },


  }
})
</script>