<template>
  <div class="flex flex-wrap justify-center items-center gap-4 pt-10 md:pt-5">

    <!--  Оборудование Недоступно-->
    <span v-if="status === 0" class="text-red-500">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-x-circle-fill"
             viewBox="0 0 16 16">
          <path
              d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"></path>
        </svg>
    </span>

    <!--  Неизвестное состояние-->
    <span v-else-if="status !== 1" class="text-gray-500">
      <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-question-circle"
           viewBox="0 0 16 16">
        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
        <path
            d="M5.255 5.786a.237.237 0 0 0 .241.247h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-.977 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286zm1.557 5.763c0 .533.425.927 1.01.927.609 0 1.028-.394 1.028-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94z"/>
      </svg>
    </span>

    <div class="flex">
      <i class="pi pi-wrench text-gray-400 hover:text-primary cursor-pointer" @click="toggleStatus"/>
    </div>

    <!--  Название оборудования-->
    <div class="flex flex-wrap flex-row sm:flex-row font-mono justify-center items-center gap-4">
      <div class="text-2xl sm:text-3xl">{{ device.name }}</div>
      <div class="flex items-center gap-2">
        <div v-show="device.ip" class="bg-primary rounded-xl px-3 py-1 text-white sm:text-xl">{{ device.ip }}</div>
        <div class="relative">
          <i class="pi pi-clone cursor-pointer" @click="copyIP"/>
          <span v-if="copied" class="z-10 absolute text-xs rounded-xl p-2 bg-white dark:bg-surface-800 shadow">Скопировано!</span>
        </div>
      </div>
      <PinDevice :device="device"/>
    </div>

  </div>

  <Popover ref="deviceStatus">
    <div v-if="poolStatus" class="text-sm">
      <div>Лимит одновременных подключений:
        <Badge class="font-mono" :value="poolStatus.connectionPoolSize"/>
      </div>
      <template v-if="poolStatus.statuses.length">
        <div class="pb-2">
          Переподключиться
          <Button :disabled="resetPoolLoading" :loading="resetPoolLoading" icon="pi pi-sync" severity="warn" outlined
                  rounded size="small" @click="resetPool"/>
        </div>
        <div class="flex gap-1 flex-col">
          <div v-for="(isActive, index) in poolStatus.statuses" :key="index" class="flex gap-2 items-center">
          <span v-if="isActive" class="relative flex size-3">
            <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-teal-400 opacity-75"></span>
            <span class="relative inline-flex size-3 rounded-full bg-teal-500"></span>
          </span>
            <span v-else class="relative inline-flex size-3 rounded-full bg-red-500"></span>
            Подключение {{ index + 1 }} {{ isActive ? 'активно' : 'неактивно' }}
          </div>
        </div>
      </template>
      <div v-else>Нет подключений</div>
    </div>
    <div v-else-if="poolStatusLoading">
      Загрузка...
    </div>
  </Popover>

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";

import api from "@/services/api";
import pinnedDevices from "@/services/pinnedDevices";
import {Device} from "@/services/devices";
import PinDevice from "@/components/PinDevice.vue";


interface PoolStatus {
  connectionPoolSize: number
  statuses: boolean[]
}


export default defineComponent({
  components: {PinDevice},
  props: {
    status: {required: true, type: Number},
    device: {required: true, type: Object as PropType<Device>},
    consoleUrl: {required: true, type: String},
  },
  data() {
    return {
      copied: false,
      copiedStatus: "",
      poolStatus: null as null | PoolStatus,
      poolStatusLoading: false,
      resetPoolLoading: false,
      poolStatusTimer: null as null | number,
    }
  },
  mounted(): any {
    this.poolStatusTimer = window.setInterval(
        async () => {
          if ((<any>this.$refs.deviceStatus).visible) {
            // console.log("getPoolStatus", this.device.name);
            await this.getPoolStatus()
          }
        },
        1000)
  },
  unmounted(): any {
    if (this.poolStatusTimer) {
      clearInterval(this.poolStatusTimer)
      this.poolStatusTimer = null;
    }
  },
  computed: {
    pinnedDevices() {
      return pinnedDevices
    },
  },
  methods: {
    copyIP() {
      this.copied = true;
      navigator.clipboard.writeText(this.device.ip)
          .then(() => this.copiedStatus = "Скопировано!")
          .catch((err) => {
            this.copiedStatus = "Ошибка!";
            console.error('Could not copy text: ', err);
          });
      setTimeout(() => this.copied = false, 1000)
    },

    toggleStatus(event: Event) {
      this.getPoolStatus();
      {
        (<any>this.$refs.deviceStatus).toggle(event);
      }
    },

    async getPoolStatus() {
      this.poolStatusLoading = true;
      try {
        const resp = await api.get<PoolStatus>(`/api/v1/devices/${this.device.name}/pool`)
        this.poolStatus = resp.data;
      } catch (e) {
      }
      this.poolStatusLoading = false;
    },

    async resetPool() {
      if (this.resetPoolLoading) return;

      this.resetPoolLoading = true;
      try {
        await api.delete(`/api/v1/devices/${this.device.name}/pool`)
      } catch (e) {
      }
      setTimeout(() => {
        this.resetPoolLoading = false;
      }, 3000)
    },

  }
})
</script>

<style scoped>
.copy-tooltip {
  font-size: 0.8rem;
  display: inline;
  position: absolute;
  top: 3px;
}
</style>