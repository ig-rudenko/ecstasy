<template>
  <div id="app">

    <div class="header">
      <h2>Технические данные</h2>

      <a v-if="hasPermissionsToCreate" href="/gpon/tech-data/create" class="add-button text-decoration-none">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#6D5BD0" class="me-2" viewBox="0 0 16 16">
          <path fill-rule="evenodd"
                d="M8 5.5a.5.5 0 0 1 .5.5v1.5H10a.5.5 0 0 1 0 1H8.5V10a.5.5 0 0 1-1 0V8.5H6a.5.5 0 0 1 0-1h1.5V6a.5.5 0 0 1 .5-.5z"/>
          <path
              d="m10.273 2.513-.921-.944.715-.698.622.637.89-.011a2.89 2.89 0 0 1 2.924 2.924l-.01.89.636.622a2.89 2.89 0 0 1 0 4.134l-.637.622.011.89a2.89 2.89 0 0 1-2.924 2.924l-.89-.01-.622.636a2.89 2.89 0 0 1-4.134 0l-.622-.637-.89.011a2.89 2.89 0 0 1-2.924-2.924l.01-.89-.636-.622a2.89 2.89 0 0 1 0-4.134l.637-.622-.011-.89a2.89 2.89 0 0 1 2.924-2.924l.89.01.622-.636a2.89 2.89 0 0 1 4.134 0l-.715.698a1.89 1.89 0 0 0-2.704 0l-.92.944-1.32-.016a1.89 1.89 0 0 0-1.911 1.912l.016 1.318-.944.921a1.89 1.89 0 0 0 0 2.704l.944.92-.016 1.32a1.89 1.89 0 0 0 1.912 1.911l1.318-.016.921.944a1.89 1.89 0 0 0 2.704 0l.92-.944 1.32.016a1.89 1.89 0 0 0 1.911-1.912l-.016-1.318.944-.921a1.89 1.89 0 0 0 0-2.704l-.944-.92.016-1.32a1.89 1.89 0 0 0-1.912-1.911l-1.318.016z"/>
        </svg>
        Добавить
      </a>
    </div>

    <!-- ОШИБКА ЗАГРУЗКИ -->
    <div v-if="errorStatus" class="alert alert-danger">
      Ошибка при загрузке данных.
      <br> {{errorMessage||''}}
      <br> Статус: {{errorStatus}}
    </div>

    <Table v-if="tableData" :data="tableData"></Table>

  </div>
</template>

<script>
import Table from "./components/Table.vue";
import api_request from "../api_request.js";

export default {
  name: "Gpon_base.vue",
  components: {
    Table
  },
  data() {
    return {
      gponTechData: null,
      errorStatus: null,
      errorMessage: null,
      userPermissions: [],
    }
  },
  mounted() {
    api_request.get("/gpon/api/permissions").then(resp => {this.userPermissions = resp.data})

    api_request.get("/gpon/api/tech-data")
        .then(resp => this.gponTechData = resp.data)
        .catch(reason => {
          this.errorStatus = reason.response.status
          if (this.errorStatus === 403){
            this.errorMessage = reason.response.data.detail
          } else {
            this.errorMessage = reason.response.data
          }
        })
  },
  computed: {
    tableData() {
      return this.gponTechData
    },
    hasPermissionsToCreate(){
      return [
          "gpon.add_oltstate",
          "gpon.add_houseoltstate",
          "gpon.add_houseb",
          "gpon.add_end3",
      ].every(elem => {return this.userPermissions.includes(elem)})
    }
  }
}
</script>

<style scoped>
.header {
  text-align: right;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.add-button {
  margin: 15px;
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #6D5BD0;
  border: 1px #6D5BD0 solid;
}

.add-button:hover {
  box-shadow: 0 0 3px #6D5BD0;
}

</style>