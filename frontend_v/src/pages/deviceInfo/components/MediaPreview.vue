<template>
  <div class="flex h-full min-h-[12rem] w-full items-center justify-center overflow-hidden rounded-3xl border border-dashed border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/80 dark:bg-gray-800/50">
    <Image
        v-if="item.isImage && item.imageSrc"
        class="max-h-[26rem] max-w-full overflow-hidden rounded-2xl"
        :src="item.imageSrc"
        preview
        alt="Предпросмотр изображения"
    />

    <div v-else class="flex flex-col items-center gap-3 text-center text-gray-500 dark:text-gray-300">
      <i :class="['bi', fileIconClass(item.file.name), 'text-7xl']"></i>
      <div class="max-w-xs break-all text-sm font-medium">{{ item.file.name }}</div>
    </div>
  </div>
</template>

<script lang="ts">
import {PropType} from "vue";

import getFileEarmarkClass from "../fileFormat";
import {MediaFile} from "../files";

export default {
  name: "MediaPreview",
  props: {
    item: {required: true, type: Object as PropType<MediaFile>}
  },
  methods: {
    fileIconClass(fileName: string): string {
      return getFileEarmarkClass(fileName);
    }
  }
};
</script>
