<template>

  <Button text v-tooltip.bottom="'Медиафайлы'" class="flex items-center"
          :severity="items.length?'success':'secondary'" @click="dialogVisible=true">
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" :fill="mediaToggleButtonColor" viewBox="0 0 16 16">
      <path d="M4.502 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/>
      <path
          d="M14.002 13a2 2 0 0 1-2 2h-10a2 2 0 0 1-2-2V5A2 2 0 0 1 2 3a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v8a2 2 0 0 1-1.998 2zM14 2H4a1 1 0 0 0-1 1h9.002a2 2 0 0 1 2 2v7A1 1 0 0 0 15 11V3a1 1 0 0 0-1-1zM2.002 4a1 1 0 0 0-1 1v8l2.646-2.354a.5.5 0 0 1 .63-.062l2.66 1.773 3.71-3.71a.5.5 0 0 1 .577-.094l1.777 1.947V5a1 1 0 0 0-1-1h-10z"/>
    </svg>
    <div v-if="items.length" class="rounded-full font-mono text-white px-2"
         :style="{backgroundColor: mediaToggleButtonColor}">
      {{ items.length }}
    </div>
  </Button>

  <Dialog maximizable :header="'Медиафайлы оборудования '+deviceName" v-model:visible="dialogVisible" modal
          class="w-full h-screen">

    <div class="flex flex-col-reverse md:flex-row">
      <div class="flex flex-col items-stretch flex-shrink-0 w-[350px] overflow-auto h-[75vh]">
        <div class="py-2 flex justify-center">

          <!--Кнопка добавить новый медиа-->
          <Button @click="() => setCurrentItem()" icon="pi pi-plus" rounded outlined label="Добавить"/>

        </div>

        <div v-if="items.length" class="flex flex-wrap">
          <div v-for="(item, index) in items" @click="() => setCurrentItem(item)" :class="itemClasses(item)"
               class="cursor-pointer border-b-2">
            <div class="flex w-full items-center justify-between relative p-2">

              <div class="p-3">
                <img v-if="item.isImage" :src="item.url" height="80" alt="image">
                <!--Другой файл-->
                <div v-else class="flex flex-col items-center justify-center gap-3">
                  <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" fill="currentColor"
                       viewBox="0 0 16 16">
                    <path
                        d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5z"/>
                  </svg>
                  <div>{{ item.name }}</div>
                </div>
              </div>

              <div class="flex flex-wrap gap-2">
                <Button @click="showDeleteFrom" severity="danger" icon="pi pi-trash" rounded outlined/>
                <Button @click="showEditForm(index);" severity="warn" icon="pi pi-pencil" rounded outlined/>
              </div>

            </div>
            <div class="text-sm flex items-center gap-2"><i class="pi pi-clock"/>{{ parseDateTimeString(item.modTime) }}
            </div>
            <div>{{ item.description }}</div>
          </div>

        </div>
      </div>


      <div class="mx-auto overflow-auto h-[75vh] p-4">

        <!--Добавить новый медиа-->
        <template v-if="!currentItem">
          <LoadMedia @loadedmedia="addNewMedia" :device-name="deviceName"/>
        </template>

        <div v-else class="m-4">

          <!--Форма удаления-->
          <div v-if="deleteForm.show" class="text-center p-4">
            <div class="py-2">
              <div class="text-xl">Вы уверены, что хотите удалить данный медиафайл?</div>
              <div v-if="deleteForm.notification.error" class="alert alert-danger">
                {{ deleteForm.notification.error }}
              </div>
            </div>
            <div class="flex gap-2 justify-center">
              <Button icon="pi pi-times" @click="deleteForm.show = false" label="Нет" severity=""/>
              <Button icon="pi pi-trash" @click="deleteCurrentItem" label="Удалить" severity="danger"/>
            </div>
          </div>

          <!--Форма редактирования-->
          <template v-else-if="editForm.show">
            <EditMedia :item="items[editForm.itemIndex]"
                       :device-name="deviceName"
                       @close="editForm.show=false;currentItem=items[editForm.itemIndex]"
                       @reloadedmedia="updateMedia">
            </EditMedia>
          </template>

          <!--Просмотр изображения-->
          <a v-if="!editForm.show && currentItem?.isImage" :href="currentItem.url" target="_blank"
             class="flex justify-center items-center">
            <img class="max-w-full max-h-fit" :src="currentItem.url" alt="image">
          </a>

          <!--Другие файлы-->
          <div v-else-if="!editForm.show && currentItem" class="content-center justify-center h-full">
            <div>
              <div class="file-link">
                <div>
                  <svg xmlns="http://www.w3.org/2000/svg" width="150" height="150" fill="currentColor"
                       viewBox="0 0 16 16">
                    <path
                        d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5z"/>
                  </svg>
                </div>

                <div class="text-xl flex gap-2 items-center p-2">
                  <i v-if="!downloadInProgress" class="pi pi-download cursor-pointer hover:text-indigo-500 text-xl"
                     @click="downloadFile(currentItem.url)"/>
                  <div>{{ currentItem.name }}</div>
                </div>

                <div v-if="downloadInProgress" class="flex justify-center">
                  <ProgressSpinner style="width: 50px; height: 50px" strokeWidth="8" fill="transparent"
                                   animationDuration=".5s" aria-label="downloading"/>
                </div>
              </div>
            </div>
          </div>


        </div>
      </div>
    </div>

  </Dialog>
</template>

<script lang="ts">
import {defineComponent} from "vue";

import LoadMedia from "./LoadMedia.vue";
import EditMedia from "./EditMedia.vue";

import api from "@/services/api";
import errorFmt from "@/errorFmt";
import {downloadFile} from "@/services/files";
import {errorToast} from "@/services/my.toast";
import {getProtectedImage} from "@/helpers/images";
import {MediaFileInfo, newMediaFileInfoList} from "../files";

export default defineComponent({
  components: {EditMedia, LoadMedia},
  props: {
    deviceName: {required: true, type: String}
  },

  data() {
    return {
      dialogVisible: false,
      items: [] as MediaFileInfo[],
      currentItem: null as (MediaFileInfo | null),
      editForm: {
        show: false,
        itemIndex: 0,
      },
      downloadInProgress: false,
      deleteForm: {
        show: false,
        notification: {
          error: "",
        }
      }
    }
  },
  mounted() {
    this.loadMedia()
  },
  computed: {
    mediaToggleButtonColor(): string {
      if (this.items.length) {
        return "#198754"
      }
      return "currentColor"
    }
  },
  methods: {
    downloadFile(url: string) {
      this.downloadInProgress = true
      downloadFile(url, () => this.downloadInProgress = false)
    },

    setCurrentItem(item?: MediaFileInfo): void {
      if (item) {
        this.currentItem = item
      } else {
        this.currentItem = null
      }
    },

    showDeleteFrom(): void {
      this.editForm.show = false
      this.deleteForm.show = true
    },

    showEditForm(itemIndex: number): void {
      this.deleteForm.show = false
      this.editForm.show = true
      this.editForm.itemIndex = itemIndex
    },

    itemClasses(item: MediaFileInfo): Array<string> {
      let defaultClasses = ["list-group-item", "list-group-item-action", "py-3", "lh-sm", "rounded-3"]
      if (item === this.currentItem) {
        defaultClasses.push("active")
      }
      return defaultClasses
    },

    async loadMedia() {
      try {
        const resp = await api.get(`/api/v1/devices/${this.deviceName}/media`)
        this.items = await newMediaFileInfoList(resp.data);
        if (this.items.length) {
          this.setCurrentItem(this.items[0])
        }
      } catch (error: any) {
        errorToast("Не удалось загрузить список медиафайлов", errorFmt(error))
      }
    },

    async addNewMedia(media: MediaFileInfo) {
      if (media.isImage) media.url = await getProtectedImage(media.url)
      this.items.push(media)
    },

    async updateMedia(newMedia: MediaFileInfo) {
      if (newMedia.isImage) newMedia.url = await getProtectedImage(newMedia.url)
      this.items.splice(this.editForm.itemIndex, 1, newMedia)
    },

    // Функция для парсинга строки даты времени в формате ISO 8601
    parseDateTimeString(str: string): string {
      // Создаем объект Date из строки
      let date = new Date(str);
      // Проверяем, является ли объект Date валидным
      if (isNaN(date.getTime())) {
        // Если нет, возвращаем ошибку
        return "Неверный формат даты времени";
      }

      // Извлекаем часы, минуты, день, месяц и год из объекта Date
      let hours = date.getHours();
      let minutes = date.getMinutes();
      let day = date.getDate();
      let month = date.getMonth() + 1; // Месяцы в JS начинаются с 0
      let year = date.getFullYear();

      // Добавляем нули перед однозначными числами для красоты
      let hoursStr = hours < 10 ? "0" + hours : String(hours);
      let minutesStr = minutes < 10 ? "0" + minutes : String(minutes);
      let dayStr = day < 10 ? "0" + day : String(day);
      let monthStr = month < 10 ? "0" + month : String(month);

      // Формируем и возвращаем новую строку даты времени в желаемом формате
      return `${hoursStr}:${minutesStr} - ${dayStr}.${monthStr}.${year}`;
    },

    deleteCurrentItem() {
      if (!this.currentItem) return;
      api.delete(`/api/v1/devices/${this.deviceName}/media/${this.currentItem.id}`)
          .then(
              () => {
                this.removeElement(this.items, this.currentItem)
                this.currentItem = null
                this.deleteForm.show = false
              },
              (reason: any) => {
                this.deleteForm.notification.error = reason.response
              }
          )
          .catch(
              (reason: any) => {
                this.deleteForm.notification.error = reason.response
              }
          )
    },

    removeElement(array: Array<MediaFileInfo>, element: MediaFileInfo | null) {
      if (!element) return array;
      // Находим индекс элемента в массиве
      let index = array.indexOf(element);
      // Если элемент найден, удаляем его из массива
      if (index !== -1) {
        array.splice(index, 1);
      }
      // Возвращаем измененный массив
      return array;
    }
  }
})
</script>

<style scoped>
.scrollarea {
  overflow-y: auto;
}

.media-image {
  object-fit: cover;
  width: 100%;
  height: 100%;
}

.file-link {
  display: flex !important;
  align-items: center;
  flex-direction: column;
}

.delete-item {
  position: absolute;
  top: 0;
  right: 0;
}

.edit-item {
  position: absolute;
  top: 0;
  right: 50px;
}
</style>