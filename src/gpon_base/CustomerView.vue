<template>
<div id="app" style="margin: auto;">

  <Toast/>
  <ConfirmPopup/>

  <div class="header w-75" style="margin: auto;">
    <ViewPrintEditButtons
        @print="printData"
        @changeMode="mode => editMode = mode"
        exitButtonURL="/gpon/subscriber-data"
        :has-permission-to-edit="hasPermissionToUpdate"
        :is-mobile="isMobile"/>
  </div>

  <!-- ОШИБКА ЗАГРУЗКИ -->
  <div v-if="error.status" class="alert alert-danger">
    Ошибка при загрузке данных.
    <br> {{error.message||''}}
    <br> Статус: {{error.status}}
  </div>

  <div id="subscriber-data-block">

    <div v-if="customer" class="d-flex flex-wrap align-items-center justify-content-center">
      <img class="header-image" style="max-height: 400px" :src="'/static/img/gpon/subscriber-'+gender+'.svg'" alt="subscriber-image">
      <div class="border shadow rounded-4 p-5 d-flex flex-column">

          <Dropdown v-if="editMode"
                    v-model="customer.type"
                    :options="['person','company','contract']" style="width: 100%"
                    placeholder="Выберите тип абонента" class="w-full md:w-14rem">
            <template #value="slotProps">
              <div v-if="slotProps.value" class="flex align-items-center"
                   v-html="subscriberVerbose(slotProps.value)"></div>
              <span v-else>{{ slotProps.placeholder }}</span>
            </template>
            <template #option="slotProps">
              <div class="flex align-items-center" v-html="subscriberVerbose(slotProps.option)"></div>
            </template>
          </Dropdown>

        <!-- ФАМИЛИ ИМЯ ОТЧЕСТВО АБОНЕНТА -->
        <template v-if="customer.type==='person'">
          <template v-if="editMode">
            <div class="pt-3 d-flex flex-wrap">
              <div class="me-2">
                <h6 class="px-2">Фамилия <Asterisk/></h6>
                <InputText v-model.trim="customer.surname" type="text" style="width: 100%"/>
              </div>

              <div class="me-2">
                <h6 class="px-2">Имя <Asterisk/></h6>
                <InputText v-model.trim="customer.firstName" type="text" style="width: 100%"/>
              </div>
            </div>

            <div class="py-2">
              <h6 class="pt-2 px-2">Отчество <Asterisk/></h6>
              <InputText v-model.trim="customer.lastName" type="text" style="width: 100%"/>
            </div>
          </template>
          <h4 class="p-2" v-else>{{ fullName }}</h4>
        </template>

        <!-- НАЗВАНИЕ КОМПАНИИ -->
        <template v-else>
          <div v-if="editMode" class="p-2 w-100">
            <h6 class="pt-2 px-2">Название кампании <Asterisk/></h6>
            <InputText v-model.trim="customer.companyName" type="text" style="width: 100%"/>
          </div>
          <h4 class="py-2" v-else>{{ customer.companyName }}</h4>
        </template>

        <!-- НОМЕР ТЕЛЕФОНА -->
        <div class="text-secondary d-flex align-items-center py-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" class="me-3" viewBox="0 0 16 16">
            <path fill-rule="evenodd" d="M1.885.511a1.745 1.745 0 0 1 2.61.163L6.29 2.98c.329.423.445.974.315 1.494l-.547 2.19a.678.678 0 0 0 .178.643l2.457 2.457a.678.678 0 0 0 .644.178l2.189-.547a1.745 1.745 0 0 1 1.494.315l2.306 1.794c.829.645.905 1.87.163 2.611l-1.034 1.034c-.74.74-1.846 1.065-2.877.702a18.634 18.634 0 0 1-7.01-4.42 18.634 18.634 0 0 1-4.42-7.009c-.362-1.03-.037-2.137.703-2.877L1.885.511z"/>
          </svg>
          <InputMask v-if="editMode" v-model="customer.phone" date="phone" style="width: 100%"
                         mask="+7 (999) 999-99-99" placeholder="+7 (999) 999-99-99"/>
          <h5 v-else>{{customer.phone}}</h5>
        </div>

        <!-- НОМЕР КОНТРАКТА -->
        <div class="text-secondary d-flex align-items-center py-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-3" viewBox="0 0 16 16">
            <path d="M11 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"/>
            <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2v9.255S12 12 8 12s-5 1.755-5 1.755V2a1 1 0 0 1 1-1h5.5v2z"/>
          </svg>
          <InputText v-if="editMode" v-model.trim="customer.contract" type="text" style="width: 100%"/>
          <h5 v-else>{{customer.contract}}</h5>
        </div>

        <!-- Сохранить изменения -->
        <div class="pt-3">
          <button v-if="editMode" @click="updateCustomerData" class="save-button">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
            </svg>
            <span v-if="!isMobile" class="m-2">Обновить</span>
          </button>
        </div>

      </div>
    </div>

    <div class="d-flex justify-content-center">
      <div v-if="customer">
        <h3 class="mb-4">Подключения:</h3>

        <div v-for="connection in customer.connections" class="border rounded-4 shadow mb-4">

          <div v-if="editMode && hasPermissionToDeleteConnection" style="position: absolute;">
              <Button @click="deleteConnection($event, connection)" severity="danger" rounded style="position: relative; top: 15px; left: 15px;">
                X
              </Button>
          </div>

          <div class="fs-4 p-3 text-center">
            <div class="me-3">{{getFullAddress(connection.address)}}</div>
            <div>Статус подключения: <TechCapabilityBadge :status="connection.status"/></div>
          </div>

          <div class="d-flex flex-wrap p-3">

            <div class="p-3">
              <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor" class="me-3" viewBox="0 0 16 16">
                <path d="M2 9a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zM2 2a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H2zm.5 3a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm2 0a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1z"/>
              </svg>
              <div class="fw-bold">{{ connection.houseOLTState.deviceName }}</div>
              <a :href="'/gpon/tech-data/'+connection.houseOLTState.deviceName + '?port=' + connection.houseOLTState.devicePort"
                 class="text-decoration-none fw-bold">
                {{ connection.houseOLTState.devicePort }}
              </a>
            </div>

            <div class="p-3">
              <a :href="'/gpon/tech-data/end3/'+connection.end3.id">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor" class="me-3" style="transform: rotate(270deg)" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5v-1zm-6 8A1.5 1.5 0 0 1 1.5 10h1A1.5 1.5 0 0 1 4 11.5v1A1.5 1.5 0 0 1 2.5 14h-1A1.5 1.5 0 0 1 0 12.5v-1zm6 0A1.5 1.5 0 0 1 7.5 10h1a1.5 1.5 0 0 1 1.5 1.5v1A1.5 1.5 0 0 1 8.5 14h-1A1.5 1.5 0 0 1 6 12.5v-1zm6 0a1.5 1.5 0 0 1 1.5-1.5h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5v-1z"/>
                </svg>
              </a>
              <div>{{ connection.end3.location }}</div>
              <div>{{ connection.end3.type }} port: {{ connection.end3Port }}</div>
            </div>

            <div class="p-3">
              <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor" class="me-3" viewBox="0 0 16 16">
                <path d="M5.525 3.025a3.5 3.5 0 0 1 4.95 0 .5.5 0 1 0 .707-.707 4.5 4.5 0 0 0-6.364 0 .5.5 0 0 0 .707.707Z"/>
                <path d="M6.94 4.44a1.5 1.5 0 0 1 2.12 0 .5.5 0 0 0 .708-.708 2.5 2.5 0 0 0-3.536 0 .5.5 0 0 0 .707.707Z"/>
                <path d="M2.974 2.342a.5.5 0 1 0-.948.316L3.806 8H1.5A1.5 1.5 0 0 0 0 9.5v2A1.5 1.5 0 0 0 1.5 13H2a.5.5 0 0 0 .5.5h2A.5.5 0 0 0 5 13h6a.5.5 0 0 0 .5.5h2a.5.5 0 0 0 .5-.5h.5a1.5 1.5 0 0 0 1.5-1.5v-2A1.5 1.5 0 0 0 14.5 8h-2.306l1.78-5.342a.5.5 0 1 0-.948-.316L11.14 8H4.86L2.974 2.342ZM2.5 11a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1Zm4.5-.5a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Zm2.5.5a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1Zm1.5-.5a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Zm2 0a.5.5 0 1 1 1 0 .5.5 0 0 1-1 0Z"/>
                <path d="M8.5 5.5a.5.5 0 1 1-1 0 .5.5 0 0 1 1 0Z"/>
              </svg>
              <span class="me-3 badge bg-primary fs-6">{{connection.ip}}</span>
              <span class="badge bg-secondary fs-6">{{connection.ont_mac}}</span>
              <div class="p-1">
                <span class="fw-bold me-2">ONT ID:</span>
                <span>{{connection.ont_id}}</span>
              </div>
              <div class="p-1">
                <span class="fw-bold me-2">Серийный номер ONT:</span><br>
                <span>{{connection.ont_serial}}</span>
              </div>
            </div>

            <div class="p-3 d-flex">
              <div>
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor" class="me-3" viewBox="0 0 16 16">
                  <path d="M5 4a.5.5 0 0 0 0 1h6a.5.5 0 0 0 0-1H5zm-.5 2.5A.5.5 0 0 1 5 6h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5zM5 8a.5.5 0 0 0 0 1h6a.5.5 0 0 0 0-1H5zm0 2a.5.5 0 0 0 0 1h3a.5.5 0 0 0 0-1H5z"/>
                  <path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2zm10-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1z"/>
                </svg>
              </div>
              <div class="">
                <div class="p-1">
                  <span class="fw-bold me-2">Транзит </span>
                  <span>{{connection.transit}}</span>
                </div>
                <div class="p-1">
                  <span class="fw-bold me-4">Наряд</span>
                  <span>{{connection.order}}</span>
                </div>
              </div>
            </div>
          </div>



        </div>

      </div>
    </div>


  </div>

</div>
</template>

<script>
import Button from "primevue/button/Button.vue";
import ConfirmPopup from "primevue/confirmpopup";
import Dropdown from "primevue/dropdown/Dropdown.vue";
import InputMask from "primevue/inputmask/InputMask.vue";
import InputText from "primevue/inputtext/InputText.vue";
import Toast from "primevue/toast/Toast.vue"

import Asterisk from "./components/Asterisk.vue";
import TechCapabilityBadge from "./components/TechCapabilityBadge.vue";
import ViewPrintEditButtons from "./components/ViewPrintEditButtons.vue";
import api_request from "../api_request";
import formatAddress from "../helpers/address";
import getSubscriberTypeVerbose from "../helpers/subscribers";
import printElementById from "../helpers/print";

export default {
  name: "CustomerView.vue",
  components: {
    Asterisk,
    Button,
    ConfirmPopup,
    Dropdown,
    InputMask,
    InputText,
    TechCapabilityBadge,
    Toast,
    ViewPrintEditButtons,
  },
  data() {
    return {
      customer: null,
      userPermissions: [],
      windowWidth: window.innerWidth,
      editMode: false,
      error: {
        status: null,
        message: null,
      }
    }
  },

  mounted() {
    window.addEventListener('resize', () => { this.windowWidth = window.innerWidth});
    api_request.get("/gpon/api/permissions").then(resp => {this.userPermissions = resp.data});
    this.getSubscriberData();
  },

  computed: {
    fullName() {
      return this.customer.surname+" "+this.customer.firstName+" "+this.customer.lastName
    },

    hasPermissionsToCreate(){
      return [
          "gpon.add_customer",
          "gpon.add_subscriberconnection",
      ].every(elem => {return this.userPermissions.includes(elem)})
    },

    gender() {
      if (this.customer.type === "company") return "company";
      if (this.customer.type === "contract") return "contract";
      const lastName = this.customer.lastName;
      if (!lastName) return "man";
      if (RegExp(/\S+в?ич$/).test(lastName)) return "man"
      if (RegExp(/\S+в?на$/).test(lastName)) return "woman"
      return "man"
    },

    hasPermissionToUpdate() {
      return [
          "gpon.change_customer",
          "gpon.change_subscriberconnection",
      ].every(elem => {return this.userPermissions.includes(elem)})
    },

    hasPermissionToDeleteConnection() {
      return this.userPermissions.includes("gpon.delete_subscriberconnection")
    },

    isMobile() {
      return this.windowWidth <= 768
    },


  },

  methods: {

    getSubscriberData() {
      let url = window.location.href
      // /gpon/api/customer/{id}
      api_request.get("/gpon/api/" + url.match(/customers\S+/)[0])
          .then(resp => this.customer = resp.data)
          .catch(reason => {
            this.error.status = reason.response.status
            this.error.message = reason.response.data
          })
    },

    printData() {printElementById('subscriber-data-block')},

    getFullAddress(address) {
      let address_string = formatAddress(address)
      if (address.apartment){
        address_string += ` кв. ${address.apartment}`
      }
      if (address.floor){
        address_string += ` (${address.floor} этаж)`
      }
      return address_string
    },

    updateCustomerData(){
      const data = {
        type: this.customer.type,
        companyName: this.customer.companyName,
        firstName: this.customer.firstName,
        surname: this.customer.surname,
        lastName: this.customer.lastName,
        phone: this.customer.phone,
        contract: this.customer.contract,
      }
      this.handleRequest(
          api_request.put("/gpon/api/customers/"+this.customer.id, data),
          "Данные абонента были успешно обновлены"
      )
    },

    deleteConnection(event, connection) {
      this.$confirm.require({
          target: event.currentTarget,
          message: 'Вы уверены, что хотите удалить данное подключение?',
          icon: 'pi pi-info-circle',
          acceptLabel: "Да",
          rejectLabel: "Нет",
          acceptClass: 'p-button-danger p-button-sm',
          defaultFocus: "reject",
          accept: () => {
              api_request.delete("/gpon/api/subscriber-connection/"+connection.id).then(
                  () => {
                    this.$toast.add({severity: 'error', summary: 'Confirmed', detail: 'Подключение было удалено', life: 3000});
                    this.getSubscriberData();  // Обновляем данные абонента
                  }
              ).catch(
                  reason => this.$toast.add({ severity: 'error', summary: reason.response.status, detail: reason.response.data, life: 3000 })
              )
          },
          reject: () => {}
      });
    },

    subscriberVerbose(type){ return getSubscriberTypeVerbose(type) },

    /**
     * Обрабатывает запрос и отображает всплывающее окно с результатом ответа
     * @param {Promise} request
     * @param {String} successInfo
     */
    handleRequest(request, successInfo){
      request.then(
            resp => {
              this.$toast.add({severity: 'success',summary: 'Обновлено',detail: successInfo,life: 3000});
              this.editMode = false;
            }
          )
          .catch(
              reason => {
                const status = reason.response.status
                this.$toast.add({severity: 'error', summary: `Ошибка ${status}`, detail: reason.response.data, life: 5000})
              }
          )
    },

  },

}
</script>

<style scoped>

.header {
  display: flex;
  justify-content: end;
  align-items: center;
}

.print-button {
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #6D5BD0;
  border: 1px #6D5BD0 solid;
}
.print-button:hover {
  box-shadow: 0 0 3px #6D5BD0;
}

.edit-button {
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #ff802a;
  border: 1px #ff802a solid;
}
.edit-button:hover {
  box-shadow: 0 0 3px #ff802a;
}

.view-button {
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #2a4dff;
  border: 1px #2a4dff solid;
}
.view-button:hover {
  box-shadow: 0 0 3px #2a4dff;
}

.save-button {
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #008b1e;
  border: 1px #008b1e solid;
}
.save-button:hover {
  box-shadow: 0 0 3px #008b1e;
}

.back-button {
  padding: 7px 10px;
  background: white;
  border-radius: 12px;
  color: #4a4a4a;
  border: 1px #4a4a4a solid;
}
.back-button:hover {
  box-shadow: 0 0 3px #4a4a4a;
}

.grey-back {
  background-color: #ebebeb;
}

@media (max-width: 835px) {
  .container {
    margin-left: 0 !important;
    margin-right: 0 !important;
    max-width: 100% !important;
  }

  .shadow {
    box-shadow: none!important;
  }

  .border {
    border: none!important;
  }

  img {
    max-height: 300px!important;
  }

  .header {
    flex-direction: column;
  }
}

</style>