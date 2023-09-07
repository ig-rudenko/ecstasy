<template>
  <div class="table-plate">
    <div>
      <button @click="show_filter = !show_filter" class="filter-button">
        <svg v-if="filteredData.length !== data.length" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
             fill="#8B83BA" class="me-1" viewBox="0 0 16 16">
          <path
              d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#8B83BA" class="me-1"
             viewBox="0 0 16 16">
          <path
              d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2zm1 .5v1.308l4.372 4.858A.5.5 0 0 1 7 8.5v5.306l2-.666V8.5a.5.5 0 0 1 .128-.334L13.5 3.308V2h-11z"/>
        </svg>
        Фильтрация
      </button>

      <!-- ФИЛЬТР -->
      <div v-show="show_filter" id="filter" class="table-plate filter-plate p-4">
        <div class="d-flex flex-wrap">
          <div style="width: 200px" class="me-2">
            <label for="filter-region" class="mx-2 form-check-label">Регион</label>
            <input style="width: 200px" id="filter-region" v-model.trim="filter.address.region" type="text"
                   class="form-control">
          </div>
          <div style="width: 200px" class="me-2">
            <label for="filter-settlement" class="mx-2 form-check-label">Населенный пункт</label>
            <input style="width: 200px" id="filter-settlement" v-model.trim="filter.address.settlement" type="text"
                   class="form-control">
          </div>
          <div style="width: 200px" class="me-2">
            <label for="filter-planStructure" class="mx-2 form-check-label">СНТ/ТСН</label>
            <input style="width: 200px" id="filter-planStructure" v-model.trim="filter.address.planStructure"
                   type="text"
                   class="form-control">
          </div>
        </div>

        <div class="d-flex flex-wrap">
          <div style="width: 300px" class="me-2">
            <label for="filter-street" class="mx-2 form-check-label">Улица/проспект</label>
            <input style="width: 300px" id="filter-street" v-model.trim="filter.address.street" type="text"
                   class="form-control">
          </div>
          <div style="width: 100px" class="me-2">
            <label for="filter-house" class="mx-2 form-check-label">Дом</label>
            <input style="width: 100px" id="filter-house" v-model.number="filter.address.house" type="text"
                   class="form-control">
          </div>
          <div style="width: 100px" class="me-2">
            <label for="filter-block" class="mx-2 form-check-label">Корпус</label>
            <input style="width: 100px" id="filter-block" v-model.number="filter.address.block" type="text"
                   class="form-control">
          </div>
        </div>

        <div class="d-flex flex-wrap">
          <div style="width: 300px" class="me-2">
            <label for="filter-deviceName" class="mx-2 form-check-label">Название оборудования</label>
            <input style="width: 300px" id="filter-deviceName" v-model.trim="filter.deviceName" type="text"
                   class="form-control">
          </div>
          <div style="width: 200px" class="me-2">
            <label for="filter-oltPort" class="mx-2 form-check-label">Порт OLT</label>
            <input style="width: 200px" id="filter-oltPort" v-model="filter.oltPort" type="text" class="form-control">
          </div>
          <div class="me-2">
            <button class="search-button" @click="doFilter">Поиск</button>
          </div>
        </div>
      </div>

    </div>

    <!-- TABLE -->
    <div class="table-responsive-lg">
      <table :style="{opacity: show_filter?0.4:1}" class="table">
        <thead>
        <tr>
          <th scope="col"></th>
          <th scope="col">Адрес</th>
          <th scope="col">Порт olt</th>
          <th scope="col">Абонентская линия</th>
          <th scope="col">Кол-во</th>
          <th scope="col"></th>
        </tr>
        </thead>

      <tbody>
      <tr v-for="line in tableData">
        <td></td>

        <!-- АДРЕС -->
        <td style="font-weight: 650">
          {{ line.address.street }}, д. {{ line.address.house }}{{ line.address.block ? "/" + line.address.block : "" }}
          <br>
          <span class="secondary-text">{{ line.address.settlement || line.address.region }}</span>
        </td>

        <!-- ПОРТ OLT -->
        <td>
          <div style="display: flex;align-items: center;">
            <Pill :text="line.oltPort"></Pill>
            <span class="secondary-text">подъезды: {{ line.entrances }}</span>
          </div>
          <span class="secondary-text">{{ line.deviceName }}</span>
        </td>

        <!-- АБОНЕНТСКАЯ ЛИНИЯ -->
        <td>
          <Pill :text="customerLineTypeName(line.customerLine.type)"
                :color="customerLineTypeColor(line.customerLine.type)"
                :back-color="customerLineTypeBackColor(line.customerLine.type)">
          </Pill>
          <span class="secondary-text">
          <span v-if="line.customerLine.type === 'splitter'">Количество портов: {{ line.customerLine.typeCount }}</span>
          <span
              v-else-if="line.customerLine.type === 'rizer'">Количество волокон: {{ line.customerLine.typeCount }}</span>
          <span v-else>Неизвестный тип: "{{ line.customerLine.type }}"</span>
        </span>
        </td>

        <!-- КОЛИЧЕСТВО -->
        <td>
          {{ line.customerLine.count }}
        </td>
        <th>
          <a href="/" class="text-decoration-none">
            <span class="secondary-text">Редактировать</span>
          </a>
        </th>
      </tr>
      </tbody>
      </table>
    </div>

    <!-- TABLE FOOTER -->
    <div class="table-footer">

  <span class="secondary-text me-3">Row per page:
  <select class="secondary-text page-select" v-model.number="rows_per_page">
    <option value="5">5</option>
    <option value="10">10</option>
    <option value="25">25</option>
  </select>
  </span>

      <span class="secondary-text me-3">
    <!-- Диапазон отображаемых значений (от и до из скольки) Например: `50-100 из 123` или `20-23 из 23` -->
    {{
          (current_page - 1) * rows_per_page + 1
        }}-{{
          Math.min(((current_page - 1) * rows_per_page) + rows_per_page, filteredData.length)
        }} из {{ filteredData.length }}
  </span>

      <svg @click="prevPage" xmlns="http://www.w3.org/2000/svg" style="cursor: pointer" width="24" height="24"
           fill="#6E6893" class="me-3" viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/>
      </svg>

      <svg @click="nextPage" xmlns="http://www.w3.org/2000/svg" style="cursor: pointer" width="24" height="24"
           fill="#6E6893" class="bi bi-chevron-right" viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
      </svg>

    </div>

  </div>
</template>

<script>
import Pill from "./Pill.vue";

export default {
  name: "Table",
  components: {Pill},
  props: {
    data: {required: true}
  },
  data() {
    return {
      max_pages: 0,
      pages: {
        rows_per_page: 10
      },
      current_page: 1,
      show_filter: false,
      filteredData: [],
      filter: {
        address: {
          region: "",
          settlement: "",
          planStructure: "",
          street: "",
          house: null,
          block: null,
        },
        deviceName: "",
        oltPort: ""
      }
    }
  },

  mounted() {
    this.filteredData = this.data
    let urlObj = new URL(window.location.href);
    this.current_page = Number(urlObj.searchParams.get("page")) || 1
    this.calculateMaxPages()
  },

  computed: {
    rows_per_page: {
      set: function (value) {
        const new_value = Number(value)
        if (new_value) {
          this.pages.rows_per_page = new_value
        }
        this.calculateMaxPages()
      },
      get: function () {
        return this.pages.rows_per_page
      }
    },

    limit_offset() {
      return (this.current_page - 1) * this.rows_per_page
    },

    tableData() {
      if (this.limit_offset >= this.filteredData.length) {
        this.current_page = 1
      }
      console.log(this.current_page, this.rows_per_page, this.max_pages)
      return this.filteredData.slice(this.limit_offset, this.limit_offset + this.rows_per_page)
    }
  },

  methods: {
    doFilter() {
      let address_filter = this.filter.address
      let oltPort_filter = this.filter.oltPort
      let deviceName_filter = this.filter.deviceName

      this.filteredData = Array.from(this.data).filter(
          function (elem) {

            // Поиск по адресу
            const match_region = address_filter.region.length === 0 || elem.address.region.toLowerCase().indexOf(address_filter.region.toLowerCase()) > -1
            const match_settlement = address_filter.settlement.length === 0 || elem.address.settlement.toLowerCase().indexOf(address_filter.settlement.toLowerCase()) > -1
            const match_planStructure = address_filter.planStructure.length === 0 || elem.address.planStructure.toLowerCase().indexOf(address_filter.planStructure.toLowerCase()) > -1
            const match_street = address_filter.street.length === 0 || elem.address.street.toLowerCase().indexOf(address_filter.street.toLowerCase()) > -1
            const match_house = !address_filter.house || address_filter.house === elem.address.house
            const match_block = !address_filter.block || address_filter.block === elem.address.block

            // Поиск по OLT порту
            const match_oltPort = oltPort_filter.length === 0 || elem.oltPort.toLowerCase().indexOf(oltPort_filter.toLowerCase()) > -1
            const match_deviceName = deviceName_filter.length === 0 || elem.deviceName.toLowerCase().indexOf(deviceName_filter.toLowerCase()) > -1

            return match_region && match_settlement && match_planStructure && match_street && match_house && match_block && match_oltPort && match_deviceName
          }
      )
      this.show_filter = false
    },

    calculateMaxPages() {
      this.max_pages = Math.ceil(this.filteredData.length / this.rows_per_page)
    },
    nextPage() {
      if (this.current_page + 1 <= this.max_pages) this.current_page++
    },
    prevPage() {
      if (this.current_page - 1 >= 1) this.current_page--
    },

    customerLineTypeName(type) {
      if (type === "splitter") {
        return "Сплиттер"
      } else if (type === "rizer") {
        return "Райзер"
      } else {
        return type
      }
    },
    customerLineTypeBackColor(type) {
      if (type === "splitter") {
        return "#CDFFCD"
      } else if (type === "rizer") {
        return "#DAE8FC"
      } else {
        return "#f2dafc"
      }
    },
    customerLineTypeColor(type) {
      if (type === "splitter") {
        return "#007F00"
      } else if (type === "rizer") {
        return "#7572FF"
      } else {
        return "#d572ff"
      }
    }
  }
}
</script>

<style scoped>

.search-button {
  font-size: 14px;
  margin-top: 23px;
  border: 1px solid green;
  background-color: white;
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
  background-color: #F4F2FF;
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

tr:hover {
  background-color: #F4F2FF;
}

.filter-button {
  margin: 15px;
  padding: 7px 10px;
  background: white;
  border-radius: 6px;
  border: 0 #6D5BD0 solid;
}

.filter-button:hover {
  box-shadow: 0 0 3px #6D5BD0;
}

.secondary-text {
  color: #6E6893;
  font-size: 14px;
  font-weight: 500;
}

.table-plate {
  box-shadow: 0 10px 50px rgba(0, 0, 0, 0.20);
  border-radius: 8px;
}

.filter-plate {
  background-color: white;
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

.table-footer {
  background-color: #F4F2FF;
  padding: 20px;
  width: 100%;
  text-align: right;
  user-select: none;
}

.page-select {
  background-color: #F4F2FF;
  border: none;
  outline: none;
}

.page-select option {
  background-color: #F4F2FF;
}

</style>