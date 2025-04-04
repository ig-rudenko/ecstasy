<template>

  <Button @click="showDialog=true" severity="success" size="small">
    Найти абонента
  </Button>

  <Dialog v-model:visible="showDialog" modal header="Поиск абонента">

    <Message v-if="error.message" severity="error">
      Ошибка загрузки данных {{ error.message }}<br>
      Статус: {{ error.status }}
    </Message>

    <DataTable v-model:filters="filters" :value="subscribers" paginator :rows="10" paginator-position="both"
               filter-display="menu"
               :globalFilterFields="['surname', 'firstName', 'lastName', 'companyName']"
               :show-headers="false">
      <template #header>
        <InputText v-model="filters['global'].value" fluid placeholder="Поиск"/>
      </template>
      <Column field="type">
        <template #body="{ data }">
          <template v-if="data.type === 'person'">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2"
                 viewBox="0 0 16 16">
              <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"/>
              <path fill-rule="evenodd"
                    d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1z"/>
            </svg>
          </template>

          <template v-else-if="data.type === 'company'">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2"
                 viewBox="0 0 16 16">
              <path
                  d="M6.5 1A1.5 1.5 0 0 0 5 2.5V3H1.5A1.5 1.5 0 0 0 0 4.5v1.384l7.614 2.03a1.5 1.5 0 0 0 .772 0L16 5.884V4.5A1.5 1.5 0 0 0 14.5 3H11v-.5A1.5 1.5 0 0 0 9.5 1h-3zm0 1h3a.5.5 0 0 1 .5.5V3H6v-.5a.5.5 0 0 1 .5-.5z"/>
              <path
                  d="M0 12.5A1.5 1.5 0 0 0 1.5 14h13a1.5 1.5 0 0 0 1.5-1.5V6.85L8.129 8.947a.5.5 0 0 1-.258 0L0 6.85v5.65z"/>
            </svg>
          </template>

          <template v-else-if="data.type === 'contract'">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="me-2"
                 viewBox="0 0 16 16">
              <path
                  d="m8 0 6.61 3h.89a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.5.5H15v7a.5.5 0 0 1 .485.38l.5 2a.498.498 0 0 1-.485.62H.5a.498.498 0 0 1-.485-.62l.5-2A.501.501 0 0 1 1 13V6H.5a.5.5 0 0 1-.5-.5v-2A.5.5 0 0 1 .5 3h.89L8 0ZM3.777 3h8.447L8 1 3.777 3ZM2 6v7h1V6H2Zm2 0v7h2.5V6H4Zm3.5 0v7h1V6h-1Zm2 0v7H12V6H9.5ZM13 6v7h1V6h-1Zm2-1V4H1v1h14Zm-.39 9H1.39l-.25 1h13.72l-.25-1Z"/>
            </svg>
          </template>
        </template>
      </Column>

      <Column>
        <template #body="{data}">
          <div @click="selected(data)" class="hover:text-primary cursor-pointer font-bold pb-2">
            {{ data.surname }} {{ data.firstName }} {{ data.lastName }} {{ data.companyName }}
          </div>
          <div class="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path fill-rule="evenodd"
                    d="M1.885.511a1.745 1.745 0 0 1 2.61.163L6.29 2.98c.329.423.445.974.315 1.494l-.547 2.19a.678.678 0 0 0 .178.643l2.457 2.457a.678.678 0 0 0 .644.178l2.189-.547a1.745 1.745 0 0 1 1.494.315l2.306 1.794c.829.645.905 1.87.163 2.611l-1.034 1.034c-.74.74-1.846 1.065-2.877.702a18.634 18.634 0 0 1-7.01-4.42 18.634 18.634 0 0 1-4.42-7.009c-.362-1.03-.037-2.137.703-2.877L1.885.511z"/>
            </svg>
            <div>{{ data.phone || '-' }}</div>
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
              <path
                  d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
            </svg>
            <div>{{ data.contract || '-' }}</div>
          </div>
        </template>
      </Column>
    </DataTable>

  </Dialog>
</template>

<script>
import {FilterMatchMode} from "@primevue/core/api";

import api from "@/services/api";

export default {
  name: "CustomerSearch",
  props: {
    isMobile: {required: true, type: Boolean},
  },
  data() {
    return {
      showDialog: false,
      search: '',
      _subscribers: [],
      error: {
        message: null,
        status: null,
      },
      filters: {
        global: {value: null, matchMode: FilterMatchMode.CONTAINS},
      }
    }
  },
  computed: {
    subscribers() {
      if (this.search.length < 2) return this._subscribers
      const search = this.search.toLowerCase()
      return this._subscribers.filter(
          value => {
            if (value.firstName && value.firstName.toLowerCase().indexOf(search) >= 0) return true;
            if (value.surname && value.surname.toLowerCase().indexOf(search) >= 0) return true;
            if (value.lastName && value.lastName.toLowerCase().indexOf(search) >= 0) return true;
            if (value.companyName && value.companyName.toLowerCase().indexOf(search) >= 0) return true;
            if (value.contract && value.contract.toLowerCase().indexOf(search) >= 0) return true;
            return value.phone && value.phone.toLowerCase().indexOf(search) >= 0;
          }
      )
    },
  },
  mounted() {
    api.get("/api/v1/gpon/customers")
        .then(resp => this._subscribers = resp.data)
        .catch(
            reason => {
              this.error.message = reason.response.data;
              this.error.status = reason.response.status;
            }
        )
  },
  methods: {
    selected(value) {
      // Отправляем новый объект
      this.$emit("select",
          {
            id: value.id,
            type: value.type,
            firstName: value.firstName,
            surname: value.surname,
            lastName: value.lastName,
            companyName: value.companyName,
            contract: value.contract,
            phone: value.phone,
          }
      )
      this.showDialog = false
    }
  }
}
</script>
