<template>
  <Dialog v-model:visible="macSearch.dialogVisible" @hide="$emit('hide')">

    <!--      HEADER-->
    <template #header>
      <div class="flex items-center gap-2">
        <svg class="bi me-2" width="24" height="24"><use xlink:href="#search-icon"></use></svg>
        <div class="font-mono text-xl">MAC: "<span id="modal-mac-str">{{ macSearch.lastMac }}</span>"</div>
      </div>
    </template>

    <!--      TEXT-->
    <div>
      <div id="modal-mac-content" v-if="macSearch.lastSearch" class="flex gap-2 items-center">
        <div class="flex flex-col gap-1 max-w-[30rem] font-mono">
          <div class="text-xl">Vendor: {{ macSearch.lastSearch.vendor }}</div>
          <div class="text-muted-color">Address: {{ macSearch.lastSearch.address }}</div>
        </div>
      </div>
      <ProgressSpinner v-else />

      <div id="modal-mac-result" class="py-3" style="text-align: center;">
        <div v-if="macSearch.lastMacDetail?.length" v-html="macSearch.lastMacDetail"></div>
      </div>

    </div>

  </Dialog>
</template>


<script lang="ts">
import {defineComponent} from "vue";
import macSearch from "@/services/macSearch";

export default defineComponent({
  data() {
    return {
      macSearch: macSearch
    }
  },
})
</script>