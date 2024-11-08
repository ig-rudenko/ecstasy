<template>
  <div class="table-plate">
    <div>
      <div class="flex items-center px-2">
        <div>
          <Button @click="show_filter = !show_filter" class="filter-button" outlined>
            <svg v-if="filteredData.length !== data.length" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                 fill="#8B83BA" viewBox="0 0 16 16">
              <path
                  d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#8B83BA" class="me-1"
                 viewBox="0 0 16 16">
              <path
                  d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2zm1 .5v1.308l4.372 4.858A.5.5 0 0 1 7 8.5v5.306l2-.666V8.5a.5.5 0 0 1 .128-.334L13.5 3.308V2h-11z"/>
            </svg>
            <div>Фильтрация</div>
          </Button>
        </div>

        <InputText id="filter-region" v-model.trim="filter.general" fluid
                   @keydown.enter="doFilter" placeholder="ФИО, транзит или номер телефона"/>
      </div>

      <!-- ФИЛЬТР -->
      <div v-show="show_filter" id="filter"
           class="table-plate rounded-xl filter-plate border bg-gray-50 dark:bg-gray-900 p-4">
        <div class="flex flex-wrap">
          <div style="width: 200px" class="me-2">
            <label for="filter-region" class="mx-2">Регион</label>
            <InputText style="width: 200px" id="filter-region" v-model.trim="filter.address.region" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <div style="width: 200px" class="me-2">
            <label for="filter-settlement" class="mx-2">Населенный пункт</label>
            <InputText style="width: 200px" id="filter-settlement" v-model.trim="filter.address.settlement" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <div style="width: 200px" class="me-2">
            <label for="filter-planStructure" class="mx-2">СНТ/ТСН</label>
            <InputText style="width: 200px" id="filter-planStructure" v-model.trim="filter.address.planStructure"
                       @keydown.enter="doFilter"/>
          </div>
        </div>

        <div class="flex flex-wrap">
          <div style="width: 300px" class="me-2">
            <label for="filter-street" class="mx-2 form-check-label">Улица/проспект</label>
            <InputText style="width: 300px" id="filter-street" v-model.trim="filter.address.street" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <div style="width: 100px" class="me-2">
            <label for="filter-house" class="mx-2 form-check-label">Дом</label>
            <InputText style="width: 100px" id="filter-house" v-model.trim="filter.address.house" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <div style="width: 100px" class="me-2">
            <label for="filter-block" class="mx-2 form-check-label">Корпус</label>
            <InputText style="width: 100px" id="filter-block" v-model.number="filter.address.block" type="text"
                       @keydown.enter="doFilter"/>
          </div>
        </div>

        <div class="flex flex-wrap">
          <div style="width: 300px" class="me-2">
            <label for="filter-deviceName" class="mx-2">ФИО</label>
            <InputText style="width: 300px" id="filter-deviceName" v-model.trim="filter.customerName" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <div style="width: 200px" class="me-2">
            <label for="filter-devicePort" class="mx-2 form-check-label">Номер контракта</label>
            <InputText style="width: 200px" id="filter-devicePort" v-model="filter.devicePort" type="text"
                       @keydown.enter="doFilter"/>
          </div>
          <Button class="search-button dark:!text-white" outlined severity="success" @click="doFilter">Поиск</Button>
        </div>
      </div>

    </div>

    <!-- TABLE -->
    <div class="overflow-auto">
      <table :style="{opacity: show_filter?0.4:1}" class="w-full">
        <thead class="dark:border-gray-600 border-b-2">
        <tr>
          <th scope="col" class="py-2">Абонент</th>
          <th scope="col" class="py-2">Адрес</th>
          <th scope="col" class="py-2">Данные абонента</th>
          <th scope="col" class="py-2">Услуги</th>
        </tr>
        </thead>

        <tbody>
        <tr v-for="line in tableData"
            class="dark:hover:bg-gray-800 hover:bg-purple-50 dark:border-gray-600 border-b-2">

          <!-- АБОНЕНТ -->
          <td class="flex items-center font-bold py-2 px-10 gap-3 dark:text-gray-300">
            <a class="hover:text-primary" :href="'/gpon/subscriber-data/customers/'+line.customer.id">
              {{ line.customer.surname }} {{ line.customer.firstName }} {{ line.customer.lastName }}
              {{ line.customer.companyName }}
            </a>
            <div class="secondary-text flex">
              <div v-if="line.customer.contract" class="flex items-center me-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="me-2"
                     viewBox="0 0 16 16">
                  <path d="M11 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"/>
                  <path
                      d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2v9.255S12 12 8 12s-5 1.755-5 1.755V2a1 1 0 0 1 1-1h5.5v2z"/>
                </svg>
                <span class="font-mono">{{ line.customer.contract }}</span>
              </div>
              <div v-if="line.customer.phone" class="flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="me-2"
                     viewBox="0 0 16 16">
                  <path fill-rule="evenodd"
                        d="M1.885.511a1.745 1.745 0 0 1 2.61.163L6.29 2.98c.329.423.445.974.315 1.494l-.547 2.19a.678.678 0 0 0 .178.643l2.457 2.457a.678.678 0 0 0 .644.178l2.189-.547a1.745 1.745 0 0 1 1.494.315l2.306 1.794c.829.645.905 1.87.163 2.611l-1.034 1.034c-.74.74-1.846 1.065-2.877.702a18.634 18.634 0 0 1-7.01-4.42 18.634 18.634 0 0 1-4.42-7.009c-.362-1.03-.037-2.137.703-2.877L1.885.511z"/>
                </svg>
                <span class="font-mono">{{ line.customer.phone }}</span>
              </div>
            </div>
          </td>

          <!-- АДРЕС -->
          <td class="dark:text-gray-300">
            <div>
              <span class="me-2">{{ getFullAddress(line.address) }}</span>
              <span v-if="line.address.apartment">кв. {{ line.address.apartment }}</span>
              <br>
              <span class="secondary-text">{{ line.address.settlement || line.address.region }}</span>
            </div>
          </td>

          <!-- Данные абонента -->
          <td>
            <Pill :text="customerTypeName(line.customer.type)"
                  :color="customerTypeColor(line.customer.type)"
                  :back-color="customerTypeBackColor(line.customer.type)">
            </Pill>
            <span class="secondary-text">
            <span>Транзит: <span class="font-mono">{{ line.transit }}</span></span>
          </span>
          </td>

          <!-- УСЛУГИ -->
          <td>
            <div class="flex flex-col gap-1">
              <span v-for="service in line.services" class="secondary-text font-mono">{{ service }}</span>
            </div>
          </td>

        </tr>
        </tbody>
      </table>
    </div>

    <!-- TABLE FOOTER -->
    <Paginator :paginator="paginator" :data-length="filteredData.length"/>

  </div>
</template>

<script>
import Pill from "./Pill.vue";
import BuildingIcon from "./BuildingIcon.vue";
import Paginator from "./Paginator.vue";

export default {
  name: "Table",
  components: {
    BuildingIcon,
    Paginator,
    Pill,
  },
  props: {
    data: {required: true}
  },
  data() {
    return {
      paginator: {
        max_pages: 0,
        pages: {
          rows_per_page: 10
        },
        limit_offset: 0,
        current_page: 1,
      },

      show_filter: false,
      filteredData: this.data,
      filter: {
        address: {
          region: "",
          settlement: "",
          planStructure: "",
          street: "",
          house: "",
          block: null,
        },
        customerName: "",
        general: "",
      }
    }
  },

  mounted() {
    let urlObj = new URL(window.location.href);
    this.current_page = Number(urlObj.searchParams.get("page")) || 1
    this.doFilter()
  },

  computed: {
    tableData() {
      if (this.paginator.limit_offset >= this.filteredData.length) {
        this.paginator.current_page = 1
      }
      return this.filteredData.slice(
          this.paginator.limit_offset,
          this.paginator.limit_offset + this.paginator.pages.rows_per_page
      )
    }
  },

  methods: {

    getFullAddress(address) {
      let str = ""
      if (address.planStructure.length) str += `СНТ ${address.planStructure},`;
      if (address.street.length) str += ` ${address.street},`;
      str += ` д. ${address.house}`;
      if (address.block) str += `/${address.block}`;
      return str
    },

    doFilter() {
      let addressFilter = this.filter.address
      let customerNameFilter = this.filter.customerName
      let generalFilter = this.filter.general

      this.filteredData = Array.from(this.data).filter(
          function (elem) {

            // Поиск по адресу
            const match_region = addressFilter.region.length === 0 || elem.address.region.toLowerCase().indexOf(addressFilter.region.toLowerCase()) > -1
            const match_settlement = addressFilter.settlement.length === 0 || elem.address.settlement.toLowerCase().indexOf(addressFilter.settlement.toLowerCase()) > -1
            const match_planStructure = addressFilter.planStructure.length === 0 || elem.address.planStructure.toLowerCase().indexOf(addressFilter.planStructure.toLowerCase()) > -1
            const match_street = addressFilter.street.length === 0 || elem.address.street.toLowerCase().indexOf(addressFilter.street.toLowerCase()) > -1
            const match_house = addressFilter.house.length === 0 || elem.address.house.toLowerCase().indexOf(addressFilter.house.toLowerCase()) > -1
            const match_block = !addressFilter.block || addressFilter.block === elem.address.block

            // Поиск по ФИО
            const match_firstName = customerNameFilter.length === 0 || elem.customer.firstName && elem.customer.firstName.toLowerCase().indexOf(customerNameFilter.toLowerCase()) > -1
            const match_surname = customerNameFilter.length === 0 || elem.customer.surname && elem.customer.surname.toLowerCase().indexOf(customerNameFilter.toLowerCase()) > -1
            const match_lastName = customerNameFilter.length === 0 || elem.customer.lastName && elem.customer.lastName.toLowerCase().indexOf(customerNameFilter.toLowerCase()) > -1

            // General
            const generalMatch_firstName = generalFilter.length === 0 || elem.customer.firstName && elem.customer.firstName.toLowerCase().indexOf(generalFilter.toLowerCase()) > -1
            const generalMatch_surname = generalFilter.length === 0 || elem.customer.surname && elem.customer.surname.toLowerCase().indexOf(generalFilter.toLowerCase()) > -1
            const generalMatch_lastName = generalFilter.length === 0 || elem.customer.lastName && elem.customer.lastName.toLowerCase().indexOf(generalFilter.toLowerCase()) > -1
            const generalMatch_companyName = generalFilter.length === 0 || elem.customer.companyName && elem.customer.companyName.toLowerCase().indexOf(generalFilter.toLowerCase()) > -1
            const generalMatch_transit = generalFilter.length === 0 || String(elem.transit).toLowerCase().indexOf(generalFilter.toLowerCase()) > -1
            const generalMatch_phone = generalFilter.length === 0 || String(elem.customer.phone).toLowerCase().indexOf(generalFilter.toLowerCase()) > -1

            return match_region && match_settlement && match_planStructure && match_street && match_house && match_block
                && (match_firstName || match_surname || match_lastName)
                && (generalMatch_firstName || generalMatch_surname || generalMatch_lastName || generalMatch_companyName || generalMatch_transit || generalMatch_phone)
          }
      )
      this.show_filter = false
    },

    customerTypeName(type) {
      if (type === "person") {
        return "Физ. лицо"
      } else if (type === "company") {
        return "Юр. лицо"
      } else {
        return "Гос. контракт"
      }
    },
    customerTypeBackColor(type) {
      if (type === "person") {
        return "#CDFFCD"
      } else if (type === "company") {
        return "#fce9da"
      } else {
        return "#dae6fc"
      }
    },
    customerTypeColor(type) {
      if (type === "person") {
        return "#047f00"
      } else if (type === "company") {
        return "#ff9f72"
      } else {
        return "#7289ff"
      }
    },

    goToDetailSubscriberView() {
      window.location.href = `/gpon/subscriber-data/`
    },

  }
}
</script>

<style scoped>

.search-button {
  font-size: 14px;
  margin-top: 23px;
  border: 1px solid green;
  padding: 6px 30px;
  border-radius: 14px;
}

.search-button:hover {
  box-shadow: 0 0 3px green;
}

label {
  font-size: 12px;
  font-weight: 700;
}

input[type=text] {
  border-radius: 14px;
  font-size: 14px;
}

table {
  margin: 0;
}

thead {
  color: #6E6893;
  font-size: 12px;
  text-transform: uppercase;
}

tbody {
  color: #25213B;
}

tr, tr * {
  text-wrap: nowrap;
}

.filter-button {
  margin: 15px;
  padding: 7px 10px;
  border-radius: 6px;
}

.secondary-text {
  color: #6E6893;
  font-size: 14px;
  font-weight: 500;
}

.secondary-text:where(.dark, .dark *) {
  color: #9088c3;
}

.table-plate {
  box-shadow: 0 10px 50px rgba(0, 0, 0, 0.20);
}

.filter-plate {
  width: max-content;
  position: absolute;
  z-index: 10;
}

@media (max-width: 770px) {
  .filter-plate {
    width: 450px
  }
}

@media (max-width: 500px) {
  .filter-plate {
    max-width: 450px;
    width: min-content;
    margin: 0;
  }
}

</style>