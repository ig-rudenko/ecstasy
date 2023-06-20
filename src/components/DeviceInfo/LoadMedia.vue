<template>

<!--Оповещение-->
<div v-if="notification.type" :class="notificationClasses">
  <div class="w-100" style="text-align: center;">{{ notification.text }}</div>
  <button class="btn-close" @click="notification.type=null"></button>
</div>

<div :class="areaClasses">
  <div class="col-md-auto">
    <div class="file-upload">
      <label for="file-input">

        <span v-if="file" style="cursor: pointer" class="btn btn-outline-primary">Заменить файл</span>
        <span v-else>
          <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" fill="currentColor" style="cursor: pointer" viewBox="0 0 16 16">
            <path d="M8 6.5a.5.5 0 0 1 .5.5v1.5H10a.5.5 0 0 1 0 1H8.5V11a.5.5 0 0 1-1 0V9.5H6a.5.5 0 0 1 0-1h1.5V7a.5.5 0 0 1 .5-.5z"/>
            <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
          </svg>
        </span>

      </label>
      <input hidden id="file-input" type="file" @change="handleFileChange"/>
      <div v-if="file">

<!--        Предпросмотр изображения-->
        <img v-if="isImage" class="rounded-3" :src="imageSrc" alt="Предпросмотр изображения"/>

<!--        Отображение иконки файла-->
        <div v-else class="align-items-md-center d-flex flex-column py-4">
          <i :class="['bi', fileEarmarkClass]" style="font-size: 150px"></i>
          {{file.name}}
        </div>

      </div>
    </div>

    <div v-if="file">
      <textarea v-model.trim="description" cols="50" rows="4" class="form-control"></textarea>
      <button @click="uploadFile" class="btn btn-outline-success">Загрузить</button>
    </div>

  </div>
</div>

</template>

<script>
import getFileEarmarkClass from "../../helpers/fileFormat";

export default {
  name: "LoadMedia",
  props: {
    deviceName: {required: true, type: String}
  },
  data() {
    return {
      file: null,
      isImage: false,
      imageSrc: "",
      description: "",
      notification: {
        type: null,
        text: "",
      },
    }
  },

  computed: {
    areaClasses() {
      let classes = ["align-content-center", "justify-content-md-center", "row"]
      if (!this.file) {
        classes.push("h-100")
      }
      return classes
    },
    notificationClasses() {
      let classes = ["alert", "modal-header", "rounded-3"]
      classes.push(`alert-${this.notification.type}`)
      return classes
    },

    fileEarmarkClass() {
      if (!this.file) return;
      return getFileEarmarkClass(this.file.name)
    },
  },

  methods: {
    handleFileChange(event) {
      this.file = event.target.files[0];
      this.isImage = this.file.type.startsWith("image/");
      if (this.isImage) {
        // Создать URL-адрес объекта для предварительного просмотра изображения
        this.imageSrc = URL.createObjectURL(this.file);
      }
    },

    handleUploadFileError(error) {
      if (error.description) {
        return `Ошибка при указании описания: "${error.description}"`
      } else {
        return error
      }
    },

    async uploadFile() {
      if (this.file) {
        // Создать объект FormData для отправки файла
        let formData = new FormData();
        formData.append("file", this.file);
        formData.append("description", this.description)
        try {
          const resp = await fetch(
            `/device/api/${this.deviceName}/media`,
            {
              method: "post",
              body: formData,
              credentials: "include",
              headers: {
                "X-CSRFToken": document.CSRF_TOKEN,
              }
            }
          )
          const data = await resp.json()
          if (resp.ok) {
            this.notification.type = "success"
            this.notification.text = "Медиафайл был успешно загружен"
            console.log(data)
            this.$emit("loadedmedia", data)
            this.file = null

          } else {
            this.notification.type = "danger"
            this.notification.text = this.handleUploadFileError(data)
          }

        } catch (e) {
          this.notification.type = "danger"
          this.notification.text = e
        }
        console.log(this.notification.text)
      }
    },
  }
}
</script>

<style scoped>
img {
  max-width: 100%;
  min-height: 500px;
  max-height: 500px;
}
.file-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
}
</style>