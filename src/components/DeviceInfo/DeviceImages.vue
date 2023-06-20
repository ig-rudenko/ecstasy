<template>

<button type="button" class="btn" data-bs-toggle="modal" data-bs-target="#device-media-modal"
  style="width: 100%; text-align: left">
  <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="me-2" viewBox="0 0 16 16">
    <path d="M4.502 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/>
    <path d="M14.002 13a2 2 0 0 1-2 2h-10a2 2 0 0 1-2-2V5A2 2 0 0 1 2 3a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v8a2 2 0 0 1-1.998 2zM14 2H4a1 1 0 0 0-1 1h9.002a2 2 0 0 1 2 2v7A1 1 0 0 0 15 11V3a1 1 0 0 0-1-1zM2.002 4a1 1 0 0 0-1 1v8l2.646-2.354a.5.5 0 0 1 .63-.062l2.66 1.773 3.71-3.71a.5.5 0 0 1 .577-.094l1.777 1.947V5a1 1 0 0 0-1-1h-10z"/>
  </svg>
  <span>Медиафайлы</span>
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

          <div v-if="items" class="list-group list-group-flush border-bottom scrollarea">
            <template v-for="item in items">

              <div @click="currentItem = item" :class="itemClasses(item)" aria-current="true">
                <div class="d-flex w-100 align-items-center justify-content-between">

                  <div class="py-3">
  <!--                Картинка-->
                    <img v-if="item.is_image" :src="item.url" height="80" alt="image">
  <!--                PDF файл-->
                    <svg v-else-if="item.file_type === 'pdf'" xmlns="http://www.w3.org/2000/svg" width="80" height="80" fill="#fb6464" viewBox="0 0 16 16">
                     <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                     <path d="M4.603 14.087a.81.81 0 0 1-.438-.42c-.195-.388-.13-.776.08-1.102.198-.307.526-.568.897-.787a7.68 7.68 0 0 1 1.482-.645 19.697 19.697 0 0 0 1.062-2.227 7.269 7.269 0 0 1-.43-1.295c-.086-.4-.119-.796-.046-1.136.075-.354.274-.672.65-.823.192-.077.4-.12.602-.077a.7.7 0 0 1 .477.365c.088.164.12.356.127.538.007.188-.012.396-.047.614-.084.51-.27 1.134-.52 1.794a10.954 10.954 0 0 0 .98 1.686 5.753 5.753 0 0 1 1.334.05c.364.066.734.195.96.465.12.144.193.32.2.518.007.192-.047.382-.138.563a1.04 1.04 0 0 1-.354.416.856.856 0 0 1-.51.138c-.331-.014-.654-.196-.933-.417a5.712 5.712 0 0 1-.911-.95 11.651 11.651 0 0 0-1.997.406 11.307 11.307 0 0 1-1.02 1.51c-.292.35-.609.656-.927.787a.793.793 0 0 1-.58.029zm1.379-1.901c-.166.076-.32.156-.459.238-.328.194-.541.383-.647.547-.094.145-.096.25-.04.361.01.022.02.036.026.044a.266.266 0 0 0 .035-.012c.137-.056.355-.235.635-.572a8.18 8.18 0 0 0 .45-.606zm1.64-1.33a12.71 12.71 0 0 1 1.01-.193 11.744 11.744 0 0 1-.51-.858 20.801 20.801 0 0 1-.5 1.05zm2.446.45c.15.163.296.3.435.41.24.19.407.253.498.256a.107.107 0 0 0 .07-.015.307.307 0 0 0 .094-.125.436.436 0 0 0 .059-.2.095.095 0 0 0-.026-.063c-.052-.062-.2-.152-.518-.209a3.876 3.876 0 0 0-.612-.053zM8.078 7.8a6.7 6.7 0 0 0 .2-.828c.031-.188.043-.343.038-.465a.613.613 0 0 0-.032-.198.517.517 0 0 0-.145.04c-.087.035-.158.106-.196.283-.04.192-.03.469.046.822.024.111.054.227.09.346z"/>
                    </svg>
                  </div>

                  <small>{{ parseDateTimeString(item.mod_time) }}</small>

                  <span @click="deleteForm.show = true" class="btn delete-item">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5ZM11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H2.506a.58.58 0 0 0-.01 0H1.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 4.885 16h6.23a2 2 0 0 0 1.994-1.84l.853-10.66h.538a.5.5 0 0 0 0-1h-.995a.59.59 0 0 0-.01 0H11Zm1.958 1-.846 10.58a1 1 0 0 1-.997.92h-6.23a1 1 0 0 1-.997-.92L3.042 3.5h9.916Zm-7.487 1a.5.5 0 0 1 .528.47l.5 8.5a.5.5 0 0 1-.998.06L5 5.03a.5.5 0 0 1 .47-.53Zm5.058 0a.5.5 0 0 1 .47.53l-.5 8.5a.5.5 0 1 1-.998-.06l.5-8.5a.5.5 0 0 1 .528-.47ZM8 4.5a.5.5 0 0 1 .5.5v8.5a.5.5 0 0 1-1 0V5a.5.5 0 0 1 .5-.5Z"></path>
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
            <LoadMedia @loadedmedia="addNewMedia" :device-name="deviceName"></LoadMedia>
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

<!--Просмотр изображения-->
            <img v-if="currentItem.is_image" class="media-image" :src="currentItem.url" alt="image">

<!--Файл PDF-->
            <div v-else-if="currentItem.file_type === 'pdf'"
                 class="align-content-center justify-content-md-center row h-100">
              <div class="col-md-auto">
                <div class="file-link">
                  <a :href="currentItem.url" target="_blank">
                    <svg xmlns="http://www.w3.org/2000/svg" width="150" height="150" fill="#fb6464" viewBox="0 0 16 16">
                      <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"></path>
                      <path d="M4.603 14.087a.81.81 0 0 1-.438-.42c-.195-.388-.13-.776.08-1.102.198-.307.526-.568.897-.787a7.68 7.68 0 0 1 1.482-.645 19.697 19.697 0 0 0 1.062-2.227 7.269 7.269 0 0 1-.43-1.295c-.086-.4-.119-.796-.046-1.136.075-.354.274-.672.65-.823.192-.077.4-.12.602-.077a.7.7 0 0 1 .477.365c.088.164.12.356.127.538.007.188-.012.396-.047.614-.084.51-.27 1.134-.52 1.794a10.954 10.954 0 0 0 .98 1.686 5.753 5.753 0 0 1 1.334.05c.364.066.734.195.96.465.12.144.193.32.2.518.007.192-.047.382-.138.563a1.04 1.04 0 0 1-.354.416.856.856 0 0 1-.51.138c-.331-.014-.654-.196-.933-.417a5.712 5.712 0 0 1-.911-.95 11.651 11.651 0 0 0-1.997.406 11.307 11.307 0 0 1-1.02 1.51c-.292.35-.609.656-.927.787a.793.793 0 0 1-.58.029zm1.379-1.901c-.166.076-.32.156-.459.238-.328.194-.541.383-.647.547-.094.145-.096.25-.04.361.01.022.02.036.026.044a.266.266 0 0 0 .035-.012c.137-.056.355-.235.635-.572a8.18 8.18 0 0 0 .45-.606zm1.64-1.33a12.71 12.71 0 0 1 1.01-.193 11.744 11.744 0 0 1-.51-.858 20.801 20.801 0 0 1-.5 1.05zm2.446.45c.15.163.296.3.435.41.24.19.407.253.498.256a.107.107 0 0 0 .07-.015.307.307 0 0 0 .094-.125.436.436 0 0 0 .059-.2.095.095 0 0 0-.026-.063c-.052-.062-.2-.152-.518-.209a3.876 3.876 0 0 0-.612-.053zM8.078 7.8a6.7 6.7 0 0 0 .2-.828c.031-.188.043-.343.038-.465a.613.613 0 0 0-.032-.198.517.517 0 0 0-.145.04c-.087.035-.158.106-.196.283-.04.192-.03.469.046.822.024.111.054.227.09.346z"></path>
                    </svg>
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

<script>
import {defineComponent} from "vue";
import LoadMedia from "./LoadMedia.vue";

export default defineComponent({
  components: {LoadMedia},
  props: {
    deviceName: {required: true, type: String}
  },
  async created() {
    await this.loadMedia()
  },
  data() {
    return {
      items: null,
      currentItem: null,
      deleteForm: {
        show: false,
        notification: {
          error: "",
        }
      }
    }
  },
  methods: {
    itemClasses(item) {
      let defaultClasses = ["list-group-item", "list-group-item-action", "py-3", "lh-sm", "rounded-3"]
      if (item === this.currentItem) {
        defaultClasses.push("active")
      }
      return defaultClasses
    },

    async loadMedia() {
      try {
        const resp = await fetch(
          `/device/api/${this.deviceName}/media`,
          {
              method: "get",
              credentials: "include",
              headers: {
                  "X-CSRFToken": document.CSRF_TOKEN
              }
          }
        );
        const data = await resp.json()
        if (resp.ok) {
          this.items = data
        } else {
          this.error = data
        }
      } catch (e) {
        console.log(e)
      }
    },

    addNewMedia(media) {
      console.log("media", media)
      this.items.push(media)
    },

    // Функция для парсинга строки даты времени в формате ISO 8601
    parseDateTimeString(str) {
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
      hours = hours < 10 ? "0" + hours : hours;
      minutes = minutes < 10 ? "0" + minutes : minutes;
      day = day < 10 ? "0" + day : day;
      month = month < 10 ? "0" + month : month;
      // Формируем и возвращаем новую строку даты времени в желаемом формате
      return `${hours}:${minutes} - ${day}.${month}.${year}`;
    },

    async deleteCurrentItem() {
      if (!this.currentItem) return;
      try {
        const resp = await fetch(
          `/device/api/${this.deviceName}/media/${this.currentItem.id}`,
          {
              method: "delete",
              credentials: "include",
              headers: {
                  "X-CSRFToken": document.CSRF_TOKEN
              }
          }
        );
        if (resp.ok) {
          this.removeElement(this.items, this.currentItem)
          this.currentItem = null
          this.deleteForm.show = false

        } else {
          const data = await resp.json()
          this.deleteForm.notification.error = data.error
        }

      } catch (e) {
        this.deleteForm.notification.error = e
      }
    },

    removeElement(array, element) {
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
</style>