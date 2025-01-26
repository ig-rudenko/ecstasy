<template>

  <Header/>

  <div class="p-2 mx-auto">

    <div class="flex gap-2 justify-around items-center py-5">
      <div class="text-3xl font-semibold px-3">Абонентские данные</div>

      <router-link :to="{name: 'gpon-create-subscriber-data'}" v-if="hasPermissionsToCreate">
        <Button outlined class="add-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#6D5BD0" viewBox="0 0 16 16">
            <path fill-rule="evenodd"
                  d="M8 5.5a.5.5 0 0 1 .5.5v1.5H10a.5.5 0 0 1 0 1H8.5V10a.5.5 0 0 1-1 0V8.5H6a.5.5 0 0 1 0-1h1.5V6a.5.5 0 0 1 .5-.5z"/>
            <path
                d="m10.273 2.513-.921-.944.715-.698.622.637.89-.011a2.89 2.89 0 0 1 2.924 2.924l-.01.89.636.622a2.89 2.89 0 0 1 0 4.134l-.637.622.011.89a2.89 2.89 0 0 1-2.924 2.924l-.89-.01-.622.636a2.89 2.89 0 0 1-4.134 0l-.622-.637-.89.011a2.89 2.89 0 0 1-2.924-2.924l.01-.89-.636-.622a2.89 2.89 0 0 1 0-4.134l.637-.622-.011-.89a2.89 2.89 0 0 1 2.924-2.924l.89.01.622-.636a2.89 2.89 0 0 1 4.134 0l-.715.698a1.89 1.89 0 0 0-2.704 0l-.92.944-1.32-.016a1.89 1.89 0 0 0-1.911 1.912l.016 1.318-.944.921a1.89 1.89 0 0 0 0 2.704l.944.92-.016 1.32a1.89 1.89 0 0 0 1.912 1.911l1.318-.016.921.944a1.89 1.89 0 0 0 2.704 0l.92-.944 1.32.016a1.89 1.89 0 0 0 1.911-1.912l-.016-1.318.944-.921a1.89 1.89 0 0 0 0-2.704l-.944-.92.016-1.32a1.89 1.89 0 0 0-1.912-1.911l-1.318.016z"/>
          </svg>
          <span>Добавить</span>
        </Button>
      </router-link>
    </div>

    <!-- ОШИБКА ЗАГРУЗКИ -->
    <Message v-if="errorStatus" severity="error">
      Ошибка при загрузке данных.
      <br> {{ errorMessage || '' }}
      <br> Статус: {{ errorStatus }}
    </Message>

    <SubscriberDataTable v-if="gponSubscriberData" :data="gponSubscriberData"/>

    <div v-else class="flex justify-center p-4">
      <ProgressSpinner/>
    </div>

  </div>

  <Footer/>

</template>

<script>
import api from "@/services/api";

import SubscriberDataTable from "./components/SubscriberDataTable.vue";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "SubscribersData",
  components: {Footer, Header, SubscriberDataTable},
  data() {
    return {
      gponSubscriberData: null,
      errorStatus: null,
      errorMessage: null,
      userPermissions: [],
    }
  },
  mounted() {
    api.get("/api/v1/gpon/permissions").then(resp => {
      this.userPermissions = resp.data
    })

    api.get("/api/v1/gpon/subscriber-data")
        .then(resp => this.gponSubscriberData = resp.data)
        .catch(reason => {
          this.errorStatus = reason.response.status
          if (this.errorStatus === 403) {
            this.errorMessage = reason.response.data.detail
          } else {
            this.errorMessage = reason.response.data
          }
        })

  },
  computed: {
    hasPermissionsToCreate() {
      return [
        "gpon.add_customer",
        "gpon.add_subscriberconnection",
      ].every(elem => {
        return this.userPermissions.includes(elem)
      })
    }
  }
}
</script>

<style scoped>
.add-button {
  margin: 15px;
  padding: 7px 10px;
  border-radius: 12px;
  color: #6D5BD0;
  border: 1px #6D5BD0 solid;
}

.add-button:hover {
  box-shadow: 0 0 3px #6D5BD0;
}

</style>