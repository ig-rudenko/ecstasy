<template>
<!--Предпросмотр изображения-->
<img v-if="item.isImage" class="rounded-3" :src="item.imageSrc" alt="Предпросмотр изображения"/>

<!--Отображение иконки файла-->
<div v-else class="align-items-md-center d-flex flex-column py-4">
  <i :class="['bi', fileIconClass(item.file.name)]" style="font-size: 150px"></i>
  {{item.file.name}}
</div>
</template>

<script>
import getFileEarmarkClass from "../../helpers/fileFormat";
export default {
  name: "MediaPreview",
  props: {
    item: {
      required: true,
      type: {
        file: {name: String},
        isImage: Boolean,
        imageSrc: String,
        description: String,
      }
    }
  },

  methods: {
    fileIconClass(fileName) {
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