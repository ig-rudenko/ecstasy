<template>
  <div>
    <Button v-tooltip.bottom="'Подробная информация'" outlined icon="pi pi-info-circle" @click="visible = true" />
  </div>

  <Drawer v-model:visible="visible" header="Информация с Zabbix" class="w-full md:!w-80 lg:!w-[30rem]">
    <div v-if="zabbixInfo">

      <div v-if="!zabbixInfo.monitoringAvailable" class="alert alert-danger mb-2">Снято с мониторинга</div>

      <div class="border flex flex-wrap mb-4 p-3 rounded-xl">
        <div v-for="(imageURL, i) in images" class="p-3">
          <Image :src="imageURL" :alt="'image'+i" width="120" preview/>
        </div>
      </div>

      <div v-if="zabbixInfo.description" class="p-3 border rounded-xl">{{ zabbixInfo.description }}</div>

      <div class="grid grid-cols-3 gap-4 font-mono">
        <template v-for="(value, key) in zabbixInfo.inventory">
          <div >{{ key }}:</div>
          <div class="whitespace-break-spaces col-span-2">{{ value }}</div>
        </template>
      </div>
    </div>
  </Drawer>

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import Image from "primevue/image";

import {AxiosResponse} from "axios";
import api from "@/services/api";
import {ZabbixInfo} from "../GeneralInfo";

export default defineComponent({
  props: {
    zabbixInfo: {required: true, type: Object as PropType<ZabbixInfo>}
  },
  components: {Image},
  data() {
    return {
      images: [] as string[],
      visible: false,
    }
  },
  async mounted() {
    await this.getImages();
  },
  methods: {
    async getImages() {
      if (!this.zabbixInfo.inventory?.vendor || !this.zabbixInfo.inventory?.model) return;

      for (let i = 1; i < 10; i++) {
        const url = "/img/devices/" +
            this.zabbixInfo.inventory.vendor.toLowerCase() + "/" + this.zabbixInfo.inventory.model.toUpperCase().replace("/", "-")
            + "_" + i + ".png"
        try {
          const resp = await api.head(url)
          console.log(url, resp.status)
          if (resp.status !== 200) break;
          this.images.push(url)
        } catch (e) {
          break;
        }
      }
    },
  }
})
</script>