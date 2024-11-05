<template>
  <Button v-tooltip.bottom="'Карты узла сети'" text @click="toggleOverlay" style="color: #f200ff;">
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="me-1" viewBox="0 0 16 16">
      <path fill-rule="evenodd"
            d="M15.817.113A.5.5 0 0 1 16 .5v14a.5.5 0 0 1-.402.49l-5 1a.5.5 0 0 1-.196 0L5.5 15.01l-4.902.98A.5.5 0 0 1 0 15.5v-14a.5.5 0 0 1 .402-.49l5-1a.5.5 0 0 1 .196 0L10.5.99l4.902-.98a.5.5 0 0 1 .415.103M10 1.91l-4-.8v12.98l4 .8zm1 12.98 4-.8V1.11l-4 .8zm-6-.8V1.11l-4 .8v12.98z"/>
    </svg>
    <span v-if="mapsData.length > 1">{{ mapsData.length }}</span>
  </Button>

  <Popover ref="zabbixMapsOverlayPanel">
    <div>
      <div class="border-b mb-3">Карты Zabbix где имеется данное оборудование</div>
      <div v-for="map in mapsData">
        <a :href="getMapLink(map.sysmapid)" target="_blank" class="hover:text-primary">{{ map.name }}</a>
      </div>
    </div>
  </Popover>

</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';

import {ZabbixMapInfo} from "./../GeneralInfo";

export default defineComponent({
  name: "ZabbixMapsDropdown",
  props: {
    mapsData: {required: true, type: Object as PropType<ZabbixMapInfo[]>},
    zabbixUrl: {required: true, type: String},
  },

  methods: {
    getMapLink(mapid: number): string {
      return this.zabbixUrl + "/zabbix.php?action=map.view&sysmapid=" + String(mapid);
    },
    toggleOverlay(event: Event) {
      // @ts-ignore
      this.$refs.zabbixMapsOverlayPanel.toggle(event);
    }
  }

})
</script>
