<template>

  <!--Оповещение-->
  <div v-if="notification.type" :class="notificationClasses">
    <div class="w-full" style="text-align: center;">{{ notification.text }}</div>
    <button class="btn-close" @click="notification.type=''"></button>
  </div>

  <div id="drag-drop-area" :class="areaClasses">
    <div class="flex flex-wrap justify-center gap-4">

      <div class="flex flex-wrap items-center gap-4">
        <button @click="uploadAllFiles" v-if="files.length" class="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor"
               class="bi bi-cloud-arrow-up me-2" viewBox="0 0 16 16">
            <path fill-rule="evenodd"
                  d="M7.646 5.146a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1-.708.708L8.5 6.707V10.5a.5.5 0 0 1-1 0V6.707L6.354 7.854a.5.5 0 1 1-.708-.708l2-2z"></path>
            <path
                d="M4.406 3.342A5.53 5.53 0 0 1 8 2c2.69 0 4.923 2 5.166 4.579C14.758 6.804 16 8.137 16 9.773 16 11.569 14.502 13 12.687 13H3.781C1.708 13 0 11.366 0 9.318c0-1.763 1.266-3.223 2.942-3.593.143-.863.698-1.723 1.464-2.383zm.653.757c-.757.653-1.153 1.44-1.153 2.056v.448l-.445.049C2.064 6.805 1 7.952 1 9.318 1 10.785 2.23 12 3.781 12h8.906C13.98 12 15 10.988 15 9.773c0-1.216-1.02-2.228-2.313-2.228h-.5v-.5C12.188 4.825 10.328 3 8 3a4.53 4.53 0 0 0-2.941 1.1z"></path>
          </svg>
          Загрузить ({{ files.length }})
        </button>

        <label class="py-3 flex h-full" for="file-input">
            <span v-if="files.length" class="flex items-center gap-2 cursor-pointer">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 6.5a.5.5 0 0 1 .5.5v1.5H10a.5.5 0 0 1 0 1H8.5V11a.5.5 0 0 1-1 0V9.5H6a.5.5 0 0 1 0-1h1.5V7a.5.5 0 0 1 .5-.5z"/>
                <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
              </svg>
              <span>Добавить файл</span>
            </span>

          <span v-else class="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" class="cursor-pointer"
                   fill="currentColor" viewBox="0 0 16 16">
                <path
                    d="M8 6.5a.5.5 0 0 1 .5.5v1.5H10a.5.5 0 0 1 0 1H8.5V11a.5.5 0 0 1-1 0V9.5H6a.5.5 0 0 1 0-1h1.5V7a.5.5 0 0 1 .5-.5z"/>
                <path
                    d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
              </svg>
            </span>

        </label>
        <input hidden id="file-input" multiple type="file" @change="handleFileChange"/>
      </div>
      <div v-if="loadingBar.active" class="py-3 w-full">
        <div class="w-full flex flex-row">
          <div v-for="part in loadingBar.progress" :class="part.className"
               class="py-2 bg-indigo-500 w-full first:rounded-l-xl last:rounded-r-xl"
               :style="{width: `${loadingBar.partWidth}%`}"></div>
        </div>
      </div>

      <div v-if="files.length">

        <div class="flex flex-col gap-6">

          <div v-for="file_obj in files" class="shadow relative">
            <!--Кнопка удаления-->
            <div class="p-3 absolute right-0 top-0">
              <Button icon="pi pi-times" rounded severity="danger" @click="deleteFile(file_obj)"></Button>
            </div>

            <!--Ошибки при загрузке-->
            <div v-if="file_obj.errors.length" class="px-3">
              <Message v-for="err in file_obj.errors" severity="error" class="w-fit">{{ err }}</Message>
            </div>

            <div class="grid grid-cols-2">
              <div class="p-3">
                <MediaPreview :item="file_obj"></MediaPreview>
              </div>

              <div class="flex flex-col self-center gap-3">
                <div class="form-label">Описание</div>
                <textarea v-model.trim="file_obj.description" cols="50" rows="8" class="border rounded p-4"></textarea>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>


  </div>

</template>

<script lang="ts">
import {defineComponent} from "vue";

import MediaPreview from "./MediaPreview.vue";
import {MediaFile, newMediaFileInfo} from "../files";
import api from "@/services/api";
import {AxiosResponse} from "axios";
import errorFmt from "@/errorFmt.ts";

export default defineComponent({
  name: "LoadMedia",
  components: {MediaPreview},
  props: {
    deviceName: {required: true, type: String}
  },
  data() {
    return {
      files: [] as Array<MediaFile>,

      notification: {
        type: "",
        text: "",
      },
      loadingBar: {
        active: false,
        partWidth: 0,
        progress: [] as { className: string }[],
      },
    }
  },

  emits: ["loadedmedia"],

  mounted() {
    this.addDragAndDropListeners()
  },

  computed: {
    areaClasses(): Array<string> {
      let classes = ["content-center", "justify-center", "flex-row"]
      if (!this.files.length) {
        classes.push("h-full")
      }
      return classes
    },
    notificationClasses(): Array<string> {
      let classes = ["alert", "modal-header", "rounded-3"]
      classes.push(`alert-${this.notification.type}`)
      return classes
    },
  },

  methods: {

    addDragAndDropListeners(): void {
      let container: Element | null = document.querySelector("#drag-drop-area");
      if (!container) return;
      container.addEventListener("dragover", e => e.preventDefault());
      container.addEventListener("drop", (e) => this.addByDragAndDrop(<DragEvent>e));
    },

    addByDragAndDrop(e: DragEvent): void {
      e.preventDefault();
      this.addFiles(e.dataTransfer?.files)
    },

    handleFileChange(event: Event): void {
      this.addFiles((<HTMLInputElement>event.target).files)
    },

    addFiles(files?: FileList | null): void {
      if (!files) return;
      // Если после загрузки добавляются еще файлы, то обнуляем статус загрузки
      this.loadingBar.active = false
      for (const file of Array.from(files)) {
        this.files.unshift(new MediaFile(file))
      }
    },

    handleUploadFileError(error: any): string {
      if (error.description) {
        return `Ошибка при указании описания: "${error.description}"`
      } else {
        return String(error)
      }
    },

    deleteFile(fileObj: MediaFile): void {
      const index = this.files.indexOf(fileObj)
      if (index !== -1) {
        this.files.splice(index, 1)
      }
    },

    async uploadAllFiles() {
      if (!this.files.length) return;

      // Создаем временные список файлов для загрузки
      const files: Array<MediaFile> = new Array(...this.files)

      // Показываем статус загрузки и обнуляем прогресс
      this.loadingBar.active = true
      this.loadingBar.progress = []
      this.loadingBar.partWidth = 100 / files.length

      for (let i = 0; i < files.length; i++) {
        await this.uploadFile(files[i])
        // Добавляем статус загрузки файла (смотрим, нет ли ошибок)
        this.loadingBar.progress.push({
          className: files[i].errors.length > 0 ? "bg-red-500" : "bg-indigo-500"
        })
      }

      // Смотрим кол-во успешно загруженных файлов
      const uploaded = files.length - this.files.length
      if (uploaded) {
        this.notification.type = "success"
      } else {
        this.notification.type = "danger"
      }
      this.notification.text = `(${uploaded} из ${files.length}) медиафайла(ов) успешно загружены`
    },

    uploadFile(mediaFile: MediaFile): Promise<number | void> | undefined {
      if (!mediaFile.file) return;

      // Создать объект FormData для отправки файла
      let formData = new FormData();
      formData.append("file", mediaFile.file);
      formData.append("description", mediaFile.description)
      return api.post(`/api/v1/devices/${this.deviceName}/media`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
          .then(
              (value: AxiosResponse<any>) => {
                this.deleteFile(mediaFile)
                this.$emit("loadedmedia", newMediaFileInfo(value.data))
              },
              (reason: any) => mediaFile.errors.push(errorFmt(reason))
          )
          .catch(
              (reason: any) => mediaFile.errors.push(errorFmt(reason))
          )
    },
  }
});
</script>

<style scoped>
</style>