<template>
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
          (paginator.current_page - 1) * rows_per_page + 1
        }}-{{
          Math.min(
              ((paginator.current_page - 1) * rows_per_page) + rows_per_page,
              dataLength
          )
        }} из {{ dataLength }}
  </span>

  <!-- first -->
  <svg @click="firstPage" xmlns="http://www.w3.org/2000/svg" style="cursor: pointer" width="24" height="24" fill="#6E6893" class="me-3" viewBox="0 0 16 16">
    <path fill-rule="evenodd" d="M11.854 3.646a.5.5 0 0 1 0 .708L8.207 8l3.647 3.646a.5.5 0 0 1-.708.708l-4-4a.5.5 0 0 1 0-.708l4-4a.5.5 0 0 1 .708 0zM4.5 1a.5.5 0 0 0-.5.5v13a.5.5 0 0 0 1 0v-13a.5.5 0 0 0-.5-.5"/>
  </svg>

  <!-- prev -->
  <svg @click="prevPage" xmlns="http://www.w3.org/2000/svg" style="cursor: pointer" width="24" height="24" fill="#6E6893" class="me-3" viewBox="0 0 16 16">
    <path fill-rule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/>
  </svg>

  <!-- next -->
  <svg @click="nextPage" xmlns="http://www.w3.org/2000/svg" style="cursor: pointer" width="24" height="24" fill="#6E6893" class="me-3" viewBox="0 0 16 16">
    <path fill-rule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
  </svg>

  <!-- last -->
  <svg @click="lastPage" xmlns="http://www.w3.org/2000/svg" style="cursor: pointer" width="24" height="24" fill="#6E6893" class="me-3" viewBox="0 0 16 16">
    <path fill-rule="evenodd" d="M4.146 3.646a.5.5 0 0 0 0 .708L7.793 8l-3.647 3.646a.5.5 0 0 0 .708.708l4-4a.5.5 0 0 0 0-.708l-4-4a.5.5 0 0 0-.708 0zM11.5 1a.5.5 0 0 1 .5.5v13a.5.5 0 0 1-1 0v-13a.5.5 0 0 1 .5-.5"/>
  </svg>

</div>
</template>

<script>
export default {
  name: "Paginator.vue",
  props: {
    paginator: {
      required: true,
      type: Object
      // max_pages: 0,
      // pages: {
      //   rows_per_page: 10
      // },
      // limit_offset: 0,
      // current_page: 1,
    },
    dataLength: {
      required: true,
      type: Number,
    }
  },

  mounted() {
    this.calculateMaxPages()
  },

  computed: {
    rows_per_page: {
      set: function (value) {
        const new_value = Number(value)
        if (new_value) {
          this.paginator.pages.rows_per_page = new_value
        }
        this.calculateMaxPages()
      },
      get: function () {
        return this.paginator.pages.rows_per_page
      }
    },

  },

  methods: {
    calculateMaxPages() {
      this.paginator.max_pages = Math.ceil(this.dataLength / this.rows_per_page) || 1
    },
    calculateOffset() {
      this.paginator.limit_offset = (this.paginator.current_page - 1) * this.rows_per_page
    },
    firstPage() {
      this.paginator.current_page = 1
      this.calculateOffset()
    },
    nextPage() {
      if (this.paginator.current_page + 1 <= this.paginator.max_pages) {
        this.paginator.current_page++
        this.calculateOffset()
      }
    },
    prevPage() {
      if (this.paginator.current_page - 1 >= 1) {
        this.paginator.current_page--
        this.calculateOffset()
      }
    },
    lastPage() {
      this.paginator.current_page = this.paginator.max_pages
      this.calculateOffset()
    },
  }
}
</script>

<style scoped>

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