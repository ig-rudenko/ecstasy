<template>
  <div class="flex flex-col gap-4 h-full">
    <Message v-if="notification.type" :severity="notification.type" class="rounded-2xl">
      {{ notification.text }}
    </Message>

    <div id="drag-drop-area" class="flex flex-col gap-4 rounded-3xl border border-dashed border-gray-300/80 bg-gray-50/70 p-5 dark:border-gray-700/80 dark:bg-gray-800/40 h-full">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between h-full">
        <div>
          <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Загрузка медиа</div>
          <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Перетащите файлы сюда или выберите их вручную.</div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <Button v-if="files.length" @click="uploadAllFiles" label="Загрузить" icon="pi pi-cloud-upload" class="!rounded-2xl" />
          <label for="file-input" class="inline-flex cursor-pointer items-center gap-2 rounded-2xl border border-gray-200/80 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-sky-300 hover:text-sky-600 dark:border-gray-700/80 dark:bg-gray-900/60 dark:text-gray-200 dark:hover:border-sky-500 dark:hover:text-sky-300">
            <i class="pi pi-plus-circle" />
            <span>{{ files.length ? "Добавить файлы" : "Выбрать файлы" }}</span>
          </label>
          <input hidden id="file-input" multiple type="file" @change="handleFileChange" />
        </div>
      </div>

      <ProgressBar v-if="loadingBar.active" :value="uploadProgress" :show-value="false" class="h-2 overflow-hidden rounded-full" />

      <div v-if="files.length" class="grid gap-4 xl:grid-cols-2">
        <article
            v-for="fileObj in files"
            :key="fileObj.file.name + fileObj.file.size"
            class="relative rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55"
        >
          <Button icon="pi pi-times" rounded severity="danger" size="small" class="!absolute right-3 top-3" @click="deleteFile(fileObj)" />

          <div class="grid gap-4 lg:grid-cols-[minmax(0,0.9fr),minmax(0,1.1fr)]">
            <MediaPreview :item="fileObj" />

            <div class="flex flex-col gap-3">
              <div>
                <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ fileObj.file.name }}</div>
                <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">Добавьте описание перед загрузкой.</div>
              </div>

              <Message v-for="err in fileObj.errors" :key="err" severity="error" class="rounded-2xl">
                {{ err }}
              </Message>

              <FloatLabel variant="on">
                <Textarea v-model.trim="fileObj.description" input-id="media-description" rows="7" fluid class="min-h-[10rem]" />
                <label for="media-description">Описание</label>
              </FloatLabel>
            </div>
          </div>
        </article>
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
  emits: ["loadedmedia"],
  data() {
    return {
      files: [] as Array<MediaFile>,
      notification: {
        type: "",
        text: "",
      },
      loadingBar: {
        active: false,
        progress: [] as { className: string }[],
      },
    };
  },
  computed: {
    uploadProgress(): number {
      if (!this.loadingBar.active || !this.files.length) return 0;
      return Math.round((this.loadingBar.progress.length / this.files.length) * 100);
    }
  },
  mounted() {
    this.addDragAndDropListeners();
  },
  methods: {
    addDragAndDropListeners(): void {
      const container = document.querySelector("#drag-drop-area");
      if (!container) return;
      container.addEventListener("dragover", (e) => e.preventDefault());
      container.addEventListener("drop", (e) => this.addByDragAndDrop(e as DragEvent));
    },
    addByDragAndDrop(e: DragEvent): void {
      e.preventDefault();
      this.addFiles(e.dataTransfer?.files);
    },
    handleFileChange(event: Event): void {
      this.addFiles((event.target as HTMLInputElement).files);
    },
    addFiles(files?: FileList | null): void {
      if (!files) return;
      this.loadingBar.active = false;
      this.loadingBar.progress = [];
      for (const file of Array.from(files)) {
        this.files.unshift(new MediaFile(file));
      }
    },
    deleteFile(fileObj: MediaFile): void {
      const index = this.files.indexOf(fileObj);
      if (index !== -1) {
        this.files.splice(index, 1);
      }
    },
    async uploadAllFiles() {
      if (!this.files.length) return;

      const files = [...this.files];
      this.loadingBar.active = true;
      this.loadingBar.progress = [];

      for (const file of files) {
        await this.uploadFile(file);
        this.loadingBar.progress.push({
          className: file.errors.length > 0 ? "bg-red-500" : "bg-indigo-500"
        });
      }

      const uploaded = files.length - this.files.length;
      this.notification.type = uploaded ? "success" : "error";
      this.notification.text = `Успешно загружено ${uploaded} из ${files.length}`;

      if (uploaded) {
        setTimeout(() => {
          this.notification.type = "";
        }, 2500);
        this.loadingBar.active = false;
      }
    },
    uploadFile(mediaFile: MediaFile): Promise<number | void> | undefined {
      if (!mediaFile.file) return;

      const formData = new FormData();
      formData.append("file", mediaFile.file);
      formData.append("description", mediaFile.description);

      return api.post(`/api/v1/devices/${this.deviceName}/media`, formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      }).then(
          (value: AxiosResponse<any>) => {
            this.deleteFile(mediaFile);
            this.$emit("loadedmedia", newMediaFileInfo(value.data));
          },
          (reason: any) => mediaFile.errors.push(errorFmt(reason))
      ).catch(
          (reason: any) => mediaFile.errors.push(errorFmt(reason))
      );
    },
  }
});
</script>
