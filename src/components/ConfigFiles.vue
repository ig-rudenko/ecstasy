<template>
  <div class="py-4">
    <div class="card rounded-2 shadow">
    <div class="card-body">

<!--  HEADER-->
      <h4 v-if="!collectNew.active" class="py-2">
        <span class="me-2">Конфигурации</span>

      <!-- ADD NEW -->
        <span @click="collectConfig" style="cursor: pointer">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-plus-circle" viewBox="0 0 16 16">
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
            <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"></path>
          </svg>
        </span>
      </h4>
<!--      -->


<!--  ELSE | COLLECTING-->
      <div v-else style="padding-bottom: 5px;">
        <div style="padding-bottom: 5px;">
          <h4>Собираем текущую конфигурацию</h4>
        </div>
        <div class="progress" role="progressbar" aria-label="Animated striped example" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100">
          <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%;"></div>
        </div>
      </div>
<!--      -->


<!--    ALERT-->
      <div v-if="collectNew.display" :class="alertClasses">
        <div style="padding-right: 0;">
          <span class="me-2">
            {{collectNew.text}}
          </span>
          <button @click="collectNew.display=false" type="button" class="btn-close" style="position: sticky;vertical-align: middle;left: 100%;"></button>
        </div>
      </div>
<!--      -->

      <div class="table-responsive-lg">
      <table class="table">
      <tbody style="vertical-align: middle;">

      <template v-for="file in files">
          <tr>
            <td style="width: 100px; text-align: right;">
              <div class="button-group">

<!--        DOWNLOAD-->
                <div @click="downloadFile(file)" class="button-element">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-download" viewBox="0 0 16 16">
                    <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"></path>
                    <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"></path>
                  </svg>
                </div>

<!--        DELETE-->
                <div @click="selectedFile=file" class="button-element" data-bs-toggle="modal" data-bs-target="#delete-config-file-modal">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="red" class="bi bi-x-lg" viewBox="0 0 16 16">
                    <path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"></path>
                  </svg>
                </div>
              </div>
            </td>

            <td>
              <span v-html="fileIcon(file.name)"></span>
              <span @click="toggleFileDisplay(file)" style="cursor: pointer;">{{ file.name }}</span>
            </td>

            <td>{{formatBytes(file.size)}}</td>

            <td>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-clock me-2" viewBox="0 0 16 16">
                <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"></path>
                <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z"></path>
              </svg>
              <span>{{ file.modTime }}</span>
            </td>

          </tr>

          <tr v-if="file.display && file.content">
            <td colspan="4" style="max-width: 1rem;">

              <div style="font-family: monospace; padding: 1rem" v-html="format_to_html(file.content)"></div>

            </td>
          </tr>
      </template>
      </tbody>
      </table>
      </div>
    </div>
    </div>
  </div>

<!-- Delete Modal -->
<div class="modal fade" id="delete-config-file-modal" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header">
        <h1 class="modal-title fs-5" id="exampleModalLabel">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="red" class="me-2" viewBox="0 0 16 16">
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
            <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"></path>
          </svg>
          <span>Внимание!</span>
        </h1>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body text-center">
        <p>Вы уверены, что хотите удалить конфигурацию?</p>
        <p v-if="selectedFile">{{selectedFile.name}}</p>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Нет</button>
        <button type="button" class="btn btn-danger" @click="deleteFile(selectedFile)" data-bs-dismiss="modal">Удалить</button>
      </div>
    </div>
  </div>
</div>

</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  data() {
    return {
      files: [{name: String, size: Number, modTime: String, content: String}],
      selectedFile: null,
      deviceName: decodeURI(window.location.pathname).split('/').slice(-1).join(""),
      collectNew: {
        active: false,
        status: "",
        display: false,
        text: ""
      }
    }
  },
  async mounted() {
    await this.getFiles()
  },
  computed: {
    alertClasses(){
      if (this.collectNew.status === "success"){
        return ["alert", "alert-success"]
      } else if (this.collectNew.status === "error"){
        return ["alert", "alert-danger"]
      }
    }
  },
  methods: {

    fileIcon(file_name) {
      if (file_name.endsWith(".txt")) {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" class="bi bi-file-earmark-text me-1" viewBox="0 0 16 16" style="cursor: pointer;">
                  <path d="M5.5 7a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1h-5zM5 9.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0 2a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1h-2a.5.5 0 0 1-.5-.5z"></path>
                  <path d="M9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.5L9.5 0zm0 1v2A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5z"></path>
                </svg>`
      }
      if (file_name.endsWith(".zip")) {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" class="bi bi-file-earmark-zip me-1" viewBox="0 0 16 16">
                  <path d="M5 7.5a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1v.938l.4 1.599a1 1 0 0 1-.416 1.074l-.93.62a1 1 0 0 1-1.11 0l-.929-.62a1 1 0 0 1-.415-1.074L5 8.438V7.5zm2 0H6v.938a1 1 0 0 1-.03.243l-.4 1.598.93.62.929-.62-.4-1.598A1 1 0 0 1 7 8.438V7.5z"/>
                  <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1h-2v1h-1v1h1v1h-1v1h1v1H6V5H5V4h1V3H5V2h1V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
                </svg>`
      }

      return `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" class="bi bi-file-binary me-1" viewBox="0 0 16 16">
                <path d="M5.526 13.09c.976 0 1.524-.79 1.524-2.205 0-1.412-.548-2.203-1.524-2.203-.978 0-1.526.79-1.526 2.203 0 1.415.548 2.206 1.526 2.206zm-.832-2.205c0-1.05.29-1.612.832-1.612.358 0 .607.247.733.721L4.7 11.137a6.749 6.749 0 0 1-.006-.252zm.832 1.614c-.36 0-.606-.246-.732-.718l1.556-1.145c.003.079.005.164.005.249 0 1.052-.29 1.614-.829 1.614zm5.329.501v-.595H9.73V8.772h-.69l-1.19.786v.688L8.986 9.5h.05v2.906h-1.18V13h3z"/>
                <path d="M4 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H4zm0 1h8a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1z"/>
              </svg>`
    },

     formatBytes(bytes) {
      let marker = 1024; // Измените на 1000 при необходимости
      let decimal = 1;
      let kiloBytes = marker; // Один килобайт - это 1024 байта
      let megaBytes = kiloBytes * marker; // Один мегабайт - это 1024 килобайта

      if (bytes < kiloBytes) return bytes + " Б";
      else if (bytes < megaBytes) return (bytes / kiloBytes).toFixed(decimal) + " КБ";
      else if (bytes < marker * megaBytes) return (bytes / megaBytes).toFixed(decimal) + " МБ";
    },

    /**
     * Превращаем строку в html, для корректного отображения
     *
     * @param string Строка, для форматирования.
     * Заменяем перенос строки на `<br>` пробелы на `&nbsp;`
     */
    format_to_html: function (string) {

      let space_re = new RegExp(' ', 'g');
      let n_re = new RegExp('\n', 'g');

      string = string.replace(space_re, '&nbsp;').replace(n_re, '<br>')
      return string
    },

    async getFiles(){
      try {
        const response = await fetch(
            "/device/api/" + this.deviceName + "/configs",
            {
              method: "GET",
              credentials: "same-origin",
            }
        )
        this.files = await response.json()

      } catch (error) {
        console.log(error)
      }
    },

    async collectConfig(){
      // Это проверка для предотвращения множественных запросов к серверу.
      if (this.collectNew.active) return

      try {
        this.collectNew.active = true
        const response = await fetch(
            "/device/api/" + this.deviceName + "/collect-config",
            {
              method: "POST",
              credentials: "same-origin",
              headers: {
                "X-CSRFToken": document.CSRF_TOKEN
              },
            }
        )

        const data = await response.json()
        if (response.ok) {
          await this.getFiles()
          this.collectNew.status = "success"
          this.collectNew.text = data.status
        } else {
          this.collectNew.status = "error"
          this.collectNew.text = data.error
        }

      } catch (error) {
        console.log(error)
        this.collectNew.status = "error"
        this.collectNew.text = "Ошибка во время сбора новой конфигурации"
        await this.getFiles()
      }

      this.collectNew.display = true
      this.collectNew.active = false

    },

    async deleteFile(file){
      try {
        const response = await fetch(
            "/device/api/" + this.deviceName + "/config/" + file.name,
            {
              method: "DELETE",
              credentials: "same-origin",
              headers: {
                "X-CSRFToken": document.CSRF_TOKEN
              },
            }
        )

        if (response.status === 204) {
          await this.getFiles()
        }

      } catch (error) {
        console.log(error)
      }
    },

    async getFile(file) {
      try {
        const response = await fetch(
            "/device/api/" + this.deviceName + "/config/" + file.name,
            {method: "GET", credentials: "same-origin"}
        )
        // получаем blob из ответа
        return await response.blob()
      } catch (error) {
        console.log(error)
      }
    },

    async toggleFileDisplay(file) {
      if (file.size > 1024 * 1024) return

      if (!file.content) {
        let content = await this.getFile(file)
        if (!content) return

        file.content = await content.text()
      }
      file.display = !file.display;
    },

    async downloadFile(file){

       const blob = await this.getFile(file)

       // создаем ссылку на файл из blob
       const fileURL = URL.createObjectURL(blob);
       // создаем элемент <a> с атрибутом href равным ссылке на файл
       const link = document.createElement("a");
       link.href = fileURL;
       // задаем имя файла для загрузки (можно получить из ответа сервера)
       link.download = file.name;
       // добавляем элемент <a> в документ
       document.body.appendChild(link);
       // имитируем клик по элементу <a>
       link.click();
       // удаляем элемент <a> из документа
       document.body.removeChild(link);
    }
  }
})

</script>

<style scoped>
.button-group {
  display: flex!important;
  justify-content: flex-end!important;

}
.button-element {
  margin: 10px 5px;
  cursor: pointer;
  user-select: none;
}
</style>