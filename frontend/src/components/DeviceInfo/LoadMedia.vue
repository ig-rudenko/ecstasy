<template>

<!--Оповещение-->
<div v-if="notification.type" :class="notificationClasses">
  <div class="w-100" style="text-align: center;">{{ notification.text }}</div>
  <button class="btn-close" @click="notification.type=null"></button>
</div>

<div id="drag-drop-area" :class="areaClasses">
  <div class="col-md-auto">
    <div class="file-upload">

      <div>
        <button @click="uploadAllFiles" v-if="files.length" class="btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" class="bi bi-cloud-arrow-up me-2" viewBox="0 0 16 16">
            <path fill-rule="evenodd" d="M7.646 5.146a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1-.708.708L8.5 6.707V10.5a.5.5 0 0 1-1 0V6.707L6.354 7.854a.5.5 0 1 1-.708-.708l2-2z"></path>
            <path d="M4.406 3.342A5.53 5.53 0 0 1 8 2c2.69 0 4.923 2 5.166 4.579C14.758 6.804 16 8.137 16 9.773 16 11.569 14.502 13 12.687 13H3.781C1.708 13 0 11.366 0 9.318c0-1.763 1.266-3.223 2.942-3.593.143-.863.698-1.723 1.464-2.383zm.653.757c-.757.653-1.153 1.44-1.153 2.056v.448l-.445.049C2.064 6.805 1 7.952 1 9.318 1 10.785 2.23 12 3.781 12h8.906C13.98 12 15 10.988 15 9.773c0-1.216-1.02-2.228-2.313-2.228h-.5v-.5C12.188 4.825 10.328 3 8 3a4.53 4.53 0 0 0-2.941 1.1z"></path>
          </svg>
          Загрузить ({{files.length}})
        </button>

        <label class="py-3" for="file-input">
          <span v-if="files.length" style="cursor: pointer" class="btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" class="bi bi-file-earmark-plus" viewBox="0 0 16 16">
              <path d="M8 6.5a.5.5 0 0 1 .5.5v1.5H10a.5.5 0 0 1 0 1H8.5V11a.5.5 0 0 1-1 0V9.5H6a.5.5 0 0 1 0-1h1.5V7a.5.5 0 0 1 .5-.5z"/>
              <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
            </svg>
            Добавить файл
          </span>

          <span v-else>
            <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" fill="currentColor" style="cursor: pointer" viewBox="0 0 16 16">
              <path d="M8 6.5a.5.5 0 0 1 .5.5v1.5H10a.5.5 0 0 1 0 1H8.5V11a.5.5 0 0 1-1 0V9.5H6a.5.5 0 0 1 0-1h1.5V7a.5.5 0 0 1 .5-.5z"/>
              <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
            </svg>
          </span>

        </label>
        <input hidden id="file-input" multiple type="file" @change="handleFileChange"/>
      </div>

      <div v-if="loadingBar.active" class="py-3 w-100">
        <div class="progress">
          <div v-for="part in loadingBar.progress" :class="['progress-bar', part.className]" :style="{width: `${loadingBar.partWidth}%`}"
               role="progressbar" aria-valuemin="0" aria-valuemax="100"></div>
        </div>
      </div>

      <div v-if="files.length">

        <div v-for="(file_obj, index) in files" class="card mb-3 shadow">

          <div class="g-0 row">

            <!--Кнопка удаления-->
            <div class="p-3" style="text-align: right"><button @click="deleteFile(file_obj)" class="btn-close"></button></div>

            <!--Ошибки при загрузке-->
            <div v-if="file_obj.errors.length" class="px-3">
              <div v-for="err in file_obj.errors" class="alert alert-danger m-0">
                <div>{{err}}</div>
              </div>
            </div>

            <div class="col-md-6 m-3">
              <MediaPreview :item="file_obj"></MediaPreview>
            </div>

            <div class="card-body col-md-5">
              <label :for="`desc-${index}`" class="form-label">Описание</label>
              <textarea v-model.trim="file_obj.description" :id="`desc-${index}`" cols="50" rows="8" class="form-control"></textarea>
            </div>
          </div>

        </div>

      </div>
    </div>


  </div>
</div>

</template>

<script>
import MediaPreview from "./MediaPreview.vue";

export default {
  name: "LoadMedia",
  components: {MediaPreview},
  props: {
    deviceName: {required: true, type: String}
  },
  data() {
    return {
      files: [],
        //   file: null,
        //   isImage: false,
        //   imageSrc: null,
        //   description: "",

      notification: {
        type: null,
        text: "",
      },
      loadingBar: {
        active: false,
        partWidth: 0,
        progress: [],
      },
    }
  },

  mounted() {
    this.addDragAndDropListeners()
  },

  computed: {
    areaClasses() {
      let classes = ["align-content-center", "justify-content-md-center", "row"]
      if (!this.files.length) {
        classes.push("h-100")
      }
      return classes
    },
    notificationClasses() {
      let classes = ["alert", "modal-header", "rounded-3"]
      classes.push(`alert-${this.notification.type}`)
      return classes
    },
  },

  methods: {

    addDragAndDropListeners() {
      let container = document.querySelector("#drag-drop-area");
      container.addEventListener("dragover", e => e.preventDefault());
      container.addEventListener("drop", (e) => this.addByDragAndDrop(e));
    },

    addByDragAndDrop(e) {
      e.preventDefault();
      this.addFiles(e.dataTransfer.files)
    },

    handleFileChange(event) {
      this.addFiles(event.target.files)
    },

    addFiles(files) {
      // Если после загрузки добавляются еще файлы, то обнуляем статус загрузки
      this.loadingBar.active = false

      for (const file of files) {
        let imageSrc = null
        const isImage = file.type.startsWith("image/");
        if (isImage) {
          // Создать URL-адрес объекта для предварительного просмотра изображения
          imageSrc = URL.createObjectURL(file);
        }

        this.files.unshift(
            {
              file: file,
              isImage: isImage,
              imageSrc: imageSrc,
              description: "",
              errors: [],
            }
        )

        console.log(this.files)
      }
    },

    handleUploadFileError(error) {
      if (error.description) {
        return `Ошибка при указании описания: "${error.description}"`
      } else {
        return error
      }
    },

    deleteFile(file_obj){
      const index = this.files.indexOf(file_obj)
      if (index !== -1) {
        this.files.splice(index, 1)
      }
    },

    async uploadAllFiles() {
      if (!this.files.length) return;

      // Создаем временные список файлов для загрузки
      const files = new Array(...this.files)

      // Показываем статус загрузки и обнуляем прогресс
      this.loadingBar.active = true
      this.loadingBar.progress = []
      this.loadingBar.partWidth = 100 / files.length

      for (let i = 0; i < files.length; i++) {
        await this.uploadFile(files[i])

        // Добавляем статус загрузки файла (смотрим, нет ли ошибок)
        this.loadingBar.progress.push({
          className: files[i].errors.length>0?"bg-danger":"bg-primary"
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

    async uploadFile(file_obj) {
      if (!file_obj.file) return;

      // Создать объект FormData для отправки файла
      let formData = new FormData();
      formData.append("file", file_obj.file);
      formData.append("description", file_obj.description)
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
          this.deleteFile(file_obj)
          this.$emit("loadedmedia", data)
        } else {
          file_obj.errors.push(this.handleUploadFileError(data))
        }

      } catch (e) {
        file_obj.errors.push = e
      }

    },
  }
}
</script>

<style scoped>
.file-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
}
</style>