<template>

<button type="button" class="btn" data-bs-toggle="modal" data-bs-target="#device-media-modal"
  style="width: 100%; text-align: left">
  <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" :fill="mediaToggleButtonColor" class="me-2" viewBox="0 0 16 16">
    <path d="M4.502 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/>
    <path d="M14.002 13a2 2 0 0 1-2 2h-10a2 2 0 0 1-2-2V5A2 2 0 0 1 2 3a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v8a2 2 0 0 1-1.998 2zM14 2H4a1 1 0 0 0-1 1h9.002a2 2 0 0 1 2 2v7A1 1 0 0 0 15 11V3a1 1 0 0 0-1-1zM2.002 4a1 1 0 0 0-1 1v8l2.646-2.354a.5.5 0 0 1 .63-.062l2.66 1.773 3.71-3.71a.5.5 0 0 1 .577-.094l1.777 1.947V5a1 1 0 0 0-1-1h-10z"/>
  </svg>
  <span>Медиафайлы <span v-if="items.length" class="badge bg-success">{{items.length}}</span></span>
</button>

<div class="modal fade" id="device-media-modal" tabindex="-1" aria-labelledby="device-media-modal" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered modal-fullscreen modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header">
        <h1 class="modal-title fs-5" id="exampleModalLabel">Медиафайлы оборудования {{deviceName}}</h1>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body d-flex flex-nowrap">
        <div class="d-flex flex-column align-items-stretch flex-shrink-0 bg-white" style="border-right: 1px solid #dfdfdf; width: 380px;">
          <div class="py-2 d-flex justify-content-around">

<!--            Кнопка добавить новый медиа-->
            <button @click="currentItem=null" class="btn w-100">
              Добавить
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-plus-circle" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
                <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"></path>
              </svg>
            </button>

          </div>

          <div v-if="items.length" class="list-group list-group-flush border-bottom scrollarea">
            <template v-for="(item, index) in items">

              <div @click="currentItem = item" :class="itemClasses(item)" aria-current="true">
                <div class="d-flex w-100 align-items-center justify-content-between">

                  <div class="py-3">
  <!--                Картинка-->
                    <img v-if="item.isImage" :src="item.url" height="80" alt="image">
  <!--                Другой файл-->
                    <i v-else :class="['bi', fileEarmarkClass(item.name)]" style="font-size: 80px"></i>
                  </div>

                  <small>{{ parseDateTimeString(item.modTime) }}</small>

                  <span @click="showDeleteFrom" class="btn delete-item">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5ZM11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H2.506a.58.58 0 0 0-.01 0H1.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 4.885 16h6.23a2 2 0 0 0 1.994-1.84l.853-10.66h.538a.5.5 0 0 0 0-1h-.995a.59.59 0 0 0-.01 0H11Zm1.958 1-.846 10.58a1 1 0 0 1-.997.92h-6.23a1 1 0 0 1-.997-.92L3.042 3.5h9.916Zm-7.487 1a.5.5 0 0 1 .528.47l.5 8.5a.5.5 0 0 1-.998.06L5 5.03a.5.5 0 0 1 .47-.53Zm5.058 0a.5.5 0 0 1 .47.53l-.5 8.5a.5.5 0 1 1-.998-.06l.5-8.5a.5.5 0 0 1 .528-.47ZM8 4.5a.5.5 0 0 1 .5.5v8.5a.5.5 0 0 1-1 0V5a.5.5 0 0 1 .5-.5Z"></path>
                    </svg>
                  </span>

                  <span @click="showEditForm(index);" class="btn edit-item">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-pencil" viewBox="0 0 16 16">
                      <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                    </svg>
                  </span>

                </div>
                <div class="col-10 mb-1 small">{{ item.description }}</div>
              </div>

            </template>

           </div>
        </div>



        <div class="container">

<!--Добавить новый медиа-->
          <template v-if="!currentItem">
            <LoadMedia @loadedmedia="addNewMedia" :device-name="deviceName" />
          </template>

          <div v-else class="m-4" style="height: 100%;">

    <!--Форма удаления-->
            <template v-if="deleteForm.show">
              <div class="modal-body">
                <p>Вы уверены, что хотите удалить данный медиафайл?</p>
                <p v-if="deleteForm.notification.error" class="alert alert-danger">
                  {{deleteForm.notification.error}}
                </p>
              </div>
              <div class="modal-footer">
                <button @click="deleteForm.show = false" type="button" class="btn btn-secondary">Нет</button>
                <button @click="deleteCurrentItem" type="button" class="btn btn-danger">Удалить</button>
              </div>
            </template>

    <!--Форма редактирования-->
            <template v-else-if="editForm.show">
              <EditMedia :item="items[editForm.itemIndex]"
                         :device-name="deviceName"
                         @close="editForm.show=false;currentItem=items[editForm.itemIndex]"
                         @reloadedmedia="updateMedia">
              </EditMedia>
            </template>

    <!--Просмотр изображения-->
            <a v-if="!editForm.show && currentItem.isImage" :href="currentItem.url" target="_blank">
              <img class="media-image" :src="currentItem.url" alt="image">
            </a>

    <!--Другие файлы-->
            <div v-else-if="!editForm.show" class="align-content-center justify-content-md-center row h-100">
              <div class="col-md-auto">
                <div class="file-link">
                  <a :href="currentItem.url" target="_blank">
                    <i :class="['bi', fileEarmarkClass(currentItem.name)]" style="font-size: 150px"></i>
                  </a>
                  <span>{{ currentItem.name }}</span>
                </div>
              </div>
            </div>


          </div>
        </div>

      </div>
      <div class="modal-footer">
      </div>
    </div>
  </div>
</div>
</template>

<script lang="ts">
import {defineComponent} from "vue";

import LoadMedia from "./LoadMedia.vue";
import EditMedia from "./EditMedia.vue";
import api_request from "../../../api_request";
import getFileEarmarkClass from "../fileFormat";
import {MediaFileInfo, newMediaFileInfoList} from "../files";

export default defineComponent({
  components: {EditMedia, LoadMedia},
  props: {
    deviceName: {required: true, type: String}
  },

  data() {
    return {
      items: [] as Array<MediaFileInfo>,
      currentItem: null as (MediaFileInfo | null),
      editForm: {
        show: false,
        itemIndex: 0,
      },
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
    if (this.items.length){
      this.currentItem = this.items[0]
    }
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

    showDeleteFrom(): void {
      this.editForm.show = false
      this.deleteForm.show = true
    },

    showEditForm(itemIndex: number): void {
      this.deleteForm.show = false
      this.editForm.show = true
      this.editForm.itemIndex = itemIndex
    },

    fileEarmarkClass(filename: string): string {
      return getFileEarmarkClass(filename)
    },

    itemClasses(item: MediaFileInfo): Array<string> {
      let defaultClasses = ["list-group-item", "list-group-item-action", "py-3", "lh-sm", "rounded-3"]
      if (item === this.currentItem) {
        defaultClasses.push("active")
      }
      return defaultClasses
    },

    loadMedia(): void {
      api_request.get(`/device/api/${this.deviceName}/media`)
          .then(
              (value: any) => this.items = newMediaFileInfoList(value.data),
              (reason: any) => {console.log(reason)}
          )
          .catch((reason: any) => {console.log(reason)})
    },

    addNewMedia(media: MediaFileInfo): void {
      this.items.push(media)
    },

    updateMedia(newMedia: MediaFileInfo): void {
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
      api_request.delete(`/device/api/${this.deviceName}/media/${this.currentItem.id}`)
          .then(
              () => {
                this.removeElement(this.items, this.currentItem)
                this.currentItem = null
                this.deleteForm.show = false
              },
              (reason: any) => {this.deleteForm.notification.error = reason.response}
          )
          .catch(
              (reason: any) => {this.deleteForm.notification.error = reason.response}
          )
    },

    removeElement(array: Array<MediaFileInfo>, element: MediaFileInfo) {
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
  object-fit: contain;
  width: 100%;
  height: 100%;
}
.file-link {
  display: flex!important;
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