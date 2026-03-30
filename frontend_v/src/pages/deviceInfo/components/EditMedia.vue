<template>
  <div id="edit-drag-drop-area" class="flex flex-col gap-4">
    <div class="flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/80 dark:bg-gray-800/40">
      <div>
        <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Редактирование файла</div>
        <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Можно заменить файл или обновить описание.</div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Button @click="updateItem" label="Сохранить" icon="pi pi-check" class="!rounded-2xl" />
        <Button @click="closeForm" label="Отмена" icon="pi pi-times" severity="secondary" outlined class="!rounded-2xl" />
      </div>
    </div>

    <Message v-for="err in errors" :key="err" severity="error" class="rounded-2xl">
      {{ err }}
    </Message>

    <div class="grid gap-4 xl:grid-cols-[minmax(0,0.95fr),minmax(0,1.05fr)]">
      <div class="flex flex-col gap-4 rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
        <MediaPreview :item="getCurrentItem" />
        <label for="edit-file-input" class="inline-flex w-fit cursor-pointer items-center gap-2 rounded-2xl border border-gray-200/80 bg-gray-50 px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-sky-300 hover:text-sky-600 dark:border-gray-700/80 dark:bg-gray-800/70 dark:text-gray-200 dark:hover:border-sky-500 dark:hover:text-sky-300">
          <i class="pi pi-refresh" />
          <span>Заменить файл</span>
        </label>
        <input hidden id="edit-file-input" type="file" @change="handleFileChange" />
      </div>

      <div class="rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
        <FloatLabel variant="on">
          <Textarea v-model.trim="item.description" input-id="edit-media-description" rows="12" fluid class="min-h-[18rem]" />
          <label for="edit-media-description">Описание</label>
        </FloatLabel>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";

import MediaPreview from "./MediaPreview.vue";
import {MediaFile, MediaFileInfo, newMediaFileInfo} from "../files";
import api from "@/services/api";
import {AxiosResponse} from "axios";

export default defineComponent({
  name: "EditMedia",
  components: {MediaPreview},
  props: {
    deviceName: {required: true, type: String},
    item: {
      required: true,
      type: Object as PropType<MediaFileInfo>
    }
  },
  emits: ["reloadedmedia", "close"],
  data() {
    return {
      newItem: null as MediaFile | null,
      errors: [] as string[]
    };
  },
  computed: {
    getCurrentItem(): MediaFile {
      if (this.newItem) {
        return this.newItem;
      }
      return {
        file: {name: this.item.name},
        isImage: this.item.isImage,
        imageSrc: this.item.url,
        description: this.item.description
      } as MediaFile;
    }
  },
  mounted() {
    this.addDragAndDropListeners();
  },
  methods: {
    addDragAndDropListeners() {
      const container = document.querySelector("#edit-drag-drop-area");
      if (!container) return;
      container.addEventListener("dragover", (e) => e.preventDefault());
      container.addEventListener("drop", (e) => this.addItemByDragAndDrop(e as DragEvent));
    },
    addItemByDragAndDrop(e: DragEvent) {
      e.preventDefault();
      if (e.dataTransfer?.files) {
        this.addNewFile(e.dataTransfer.files);
      }
    },
    handleFileChange(e: Event) {
      this.addNewFile((e.target as HTMLInputElement)?.files);
    },
    addNewFile(files: FileList | null) {
      if (files) {
        this.newItem = new MediaFile(files[0]);
      }
    },
    handleError(error: { description?: string }): string[] {
      if (error.description) {
        return [`Ошибка в описании: "${error.description}"`];
      }
      return [String(error)];
    },
    updateItem() {
      this.errors = [];
      const formData = new FormData();
      if (this.newItem) {
        formData.append("file", this.newItem.file);
      }
      formData.append("description", this.item.description);

      api.patch(`/api/v1/devices/${this.deviceName}/media/${this.item.id}`, formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      }).then(
          (value: AxiosResponse) => {
            this.$emit("reloadedmedia", newMediaFileInfo(value.data));
            this.$emit("close");
          },
          (reason: any) => this.errors.push(...this.handleError(reason.response.data))
      ).catch(
          (reason: any) => this.errors.push(...this.handleError(reason.response.data))
      );
    },
    closeForm() {
      this.$emit("close");
    },
  }
});
</script>
