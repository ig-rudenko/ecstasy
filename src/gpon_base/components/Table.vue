<template>
  <div class="table-plate">
    <button class="filter-button">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#8B83BA" class="me-1" viewBox="0 0 16 16">
        <path
            d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5v-2z"/>
      </svg>
      Filter
    </button>
    <table class="table">
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
        <th></th>
        <th>
          {{ line.address.street }}, д. {{ line.address.house }}
          <br>
          <span class="secondary-text">{{ line.address.settlement || line.address.region }}</span>
        </th>
        <td>
          <div style="display: flex;align-items: center;">
            <Pill :text="line.oltPort"></Pill>
            <span class="secondary-text">подъезды: {{ line.entrances }}</span>
          </div>
          <span class="secondary-text">{{ line.deviceName }}</span>
        </td>
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
    {{ (current_page - 1) * rows_per_page + 1 }}-{{ Math.min(((current_page - 1) * rows_per_page) + rows_per_page, data.length) }} из {{ data.length }}
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
        rows_per_page: 5
      },
      current_page: 1,
      filter: {
        address: {
          region: "",
          settlement: "",
          CHT: "",
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
      if (this.limit_offset >= this.data.length) {
        this.current_page = this.max_pages
      }
      console.log(this.current_page, this.rows_per_page, this.max_pages)
      return this.data.slice(this.limit_offset, this.limit_offset + this.rows_per_page)
    }
  },

  methods: {
    calculateMaxPages() {
      this.max_pages = Math.ceil(this.data.length / this.rows_per_page)
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

tr:hover {
  background-color: #F4F2FF;
}

.filter-button {
  margin: 15px;
  padding: 7px 10px;
  background: white;
  border-radius: 6px;
  border: 1px #6D5BD0 solid;
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