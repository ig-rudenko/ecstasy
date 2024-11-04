<template>

  <div id="edit-drag-drop-area" class="align-content-center justify-content-md-center row">
    <div class="col-md-auto">
      <div class="file-upload">

        <div class="py-2">
          <button @click="updateItem" class="btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor"
                 class="bi bi-cloud-arrow-up me-2" viewBox="0 0 16 16">
              <path fill-rule="evenodd"
                    d="M7.646 5.146a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1-.708.708L8.5 6.707V10.5a.5.5 0 0 1-1 0V6.707L6.354 7.854a.5.5 0 1 1-.708-.708l2-2z"></path>
              <path
                  d="M4.406 3.342A5.53 5.53 0 0 1 8 2c2.69 0 4.923 2 5.166 4.579C14.758 6.804 16 8.137 16 9.773 16 11.569 14.502 13 12.687 13H3.781C1.708 13 0 11.366 0 9.318c0-1.763 1.266-3.223 2.942-3.593.143-.863.698-1.723 1.464-2.383zm.653.757c-.757.653-1.153 1.44-1.153 2.056v.448l-.445.049C2.064 6.805 1 7.952 1 9.318 1 10.785 2.23 12 3.781 12h8.906C13.98 12 15 10.988 15 9.773c0-1.216-1.02-2.228-2.313-2.228h-.5v-.5C12.188 4.825 10.328 3 8 3a4.53 4.53 0 0 0-2.941 1.1z"></path>
            </svg>
            Обновить
          </button>

          <!--Кнопка выхода из формы редактирования-->
          <button @click="closeForm" class="btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" class="bi bi-x"
                 viewBox="0 0 16 16">
              <path
                  d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
            </svg>
            Отмена
          </button>
        </div>

        <div class="mb-3">

          <div class="g-0 row">

            <!--Ошибки при загрузке-->
            <div v-if="errors.length" class="px-3">
              <div v-for="err in errors" class="alert alert-danger m-0">
                <div>{{ err }}</div>
              </div>
            </div>

            <div class="col-md-6 m-3">
              <MediaPreview :item="getCurrentItem"></MediaPreview>
              <label for="edit-file-input" class="d-block text-center" style="cursor: pointer">
                <span class="text-center">Заменить</span>
              </label>
              <input hidden id="edit-file-input" multiple type="file" @change="handleFileChange"/>
            </div>

            <div class="card-body col-md-5">
              <label for="desc" class="form-label">Описание</label>
              <textarea v-model.trim="item.description" id="desc" cols="50" rows="8" class="form-control"></textarea>
            </div>
          </div>

        </div>

      </div>
    </div>
  </div>


</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";

import getFileEarmarkClass from "../fileFormat";
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
      newItem: null as (MediaFile | null),
      errors: [] as string[]
    }
  },

  mounted() {
    this.addDragAndDropListeners()
  },

  computed: {
    getCurrentItem(): MediaFile {
      if (this.newItem) {
        return this.newItem
      } else {
        return <MediaFile>{
          file: {name: this.item.name},
          isImage: this.item.isImage,
          imageSrc: this.item.url,
          description: this.item.description
        }
      }
    }
  },


  methods: {
    addDragAndDropListeners() {
      let container: Element | null = document.querySelector("#edit-drag-drop-area");
      if (!container) return;
      container.addEventListener("dragover", e => e.preventDefault());
      container.addEventListener("drop", (e) => this.addItemByDragAndDrop(<DragEvent>e));
    },

    fileIconClass(fileName: string): string {
      return getFileEarmarkClass(fileName)
    },

    addItemByDragAndDrop(e: DragEvent) {
      e.preventDefault();
      if (e.dataTransfer?.files) {
        this.addNewFile(e.dataTransfer.files)
      }
    },

    handleFileChange(e: Event) {
      this.addNewFile((<HTMLInputElement>e.target)?.files)
    },

    addNewFile(files: FileList | null) {
      if (files) {
        this.newItem = new MediaFile(files[0])
      }
    },

    handleError(error: { description?: string }): string[] {
      if (error.description) {
        return [`Ошибка при указании описания: "${error.description}"`]
      } else {
        return [String(error)]
      }
    },

    updateItem() {
      // Создать объект FormData для отправки файла
      let formData = new FormData();
      if (this.newItem) {
        formData.append("file", this.newItem.file)
      }
      formData.append("description", this.item.description)

      api.patch(`/device/api/${this.deviceName}/media/${this.item.id}`, formData)
          .then(
              (value: AxiosResponse) => {
                // Обновляем старую информацию на новую
                this.$emit("reloadedmedia", newMediaFileInfo(value.data))
                this.$emit("close")
              },
              (reason: any) => this.errors.push(...this.handleError(reason.response.data))
          )
          .catch(
              (reason: any) => this.errors.push(...this.handleError(reason.response.data))
          )
    },

    closeForm() {
      this.$emit("close")
    },

  }
});
</script>
