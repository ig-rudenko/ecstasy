<template>
  <!--Предпросмотр изображения-->
  <img v-if="item.isImage" class="rounded-3" :src="item.imageSrc" alt="Предпросмотр изображения"/>

  <!--Отображение иконки файла-->
  <div v-else class="align-items-md-center d-flex flex-column py-4">
    <i :class="['bi', fileIconClass(item.file.name)]" style="font-size: 150px"></i>
    {{item.file.name}}
  </div>
</template>

<script lang="ts">
import {PropType} from "vue";

import getFileEarmarkClass from "../fileFormat";
import {MediaFile} from "../files";

export default {
  name: "MediaPreview",
  props: {
    item: { required: true, type: Object as PropType<MediaFile>}
  },
  methods: {
    fileIconClass(fileName: string): string {
      return getFileEarmarkClass(fileName)
    },
  }
}
</script>

<style scoped>
img {
  max-width: 100%;
}
</style>