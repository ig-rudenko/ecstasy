<template>
  <div>
    <Button v-tooltip.right="'Подробная информация'" outlined @click="visible = true">
      <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 16 16">
        <path
            d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2"/>
      </svg>
    </Button>
  </div>

  <Drawer v-model:visible="visible" header="Детальная информация" class="w-full md:!w-80 lg:!w-[30rem]">
    <div v-if="generalInfo.zabbixInfo">

      <div v-if="!generalInfo.zabbixInfo.monitoringAvailable" class="alert alert-danger text-right text-red-400 mb-2">
        Не мониторится в Zabbix
      </div>

      <div v-if="generalInfo" class="font-mono p-2 space-y-1">
        <div v-if="generalInfo.vendor">Vendor: {{ generalInfo.vendor }}</div>
        <div v-if="generalInfo.model">Model: {{ generalInfo.model }}</div>
        <div v-if="generalInfo.serialNumber">Серийный номер: {{ generalInfo.serialNumber }}</div>
        <div v-if="generalInfo.osVersion"> Версия ОС: {{ generalInfo.osVersion }}</div>
      </div>

      <div class="border flex flex-wrap mb-4 p-3 rounded-xl">
        <div v-for="(imageURL, i) in images" class="p-3">
          <Image :src="imageURL" :alt="'image'+i" width="120" preview/>
        </div>
      </div>

      <div v-if="generalInfo.zabbixInfo.description" class="p-3 border rounded-xl">
        {{ generalInfo.zabbixInfo.description }}
      </div>

      <div class="grid grid-cols-3 gap-4 font-mono">
        <template v-for="(value, key) in generalInfo.zabbixInfo.inventory">
          <div>{{ key }}:</div>
          <div class="whitespace-break-spaces col-span-2">{{ value }}</div>
        </template>
      </div>
    </div>
  </Drawer>

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import Image from "primevue/image";

import api from "@/services/api";
import {GeneralInfo} from "../GeneralInfo";

export default defineComponent({
  props: {
    generalInfo: {required: true, type: Object as PropType<GeneralInfo>}
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
      if (!this.generalInfo.vendor || !this.generalInfo.model) return;

      for (let i = 1; i < 10; i++) {
        const url = "/img/devices/" +
            this.generalInfo.vendor.toLowerCase() + "/" + this.generalInfo.model.toUpperCase().replace("/", "-")
            + "_" + i + ".png"
        try {
          const resp = await api.head(url)
          if (resp.status !== 200 || resp.headers["content-type"] == "text/html") break;
          this.images.push(url)
        } catch (e) { break;}
      }
    },
  }
})
</script>