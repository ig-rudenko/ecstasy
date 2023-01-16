<template src="./App_description_search.html"></template>

<script>
import Comment from "./components/Comment.vue";
import Pagination from "./components/Pagination.vue";
import SearchInput from "./components/SearchInput.vue";

export default {
  data() {
    return {
      interfaces: null,
      pattern: "",
      last_pattern: "",
      waitResult: false,
      pagination: {
        count: 0,
        page: 0,
        rows_per_page: 50,
        next_page: "",
      },
    }
  },
  methods: {
    async searchDescription() {
      if (this.pattern.length < 2) return;
      this.waitResult = true
      try {
        let current_pattern = this.pattern
        let url = "/tools/ajax/find?" + new URLSearchParams({pattern: current_pattern}).toString()

        let response = await fetch(url, {method: "GET", credentials: "same-origin"});
        let data = await response.json()

        this.interfaces = data.interfaces
        this.last_pattern = current_pattern

        this.pagination.count = data.interfaces.length
        this.pagination.page = 0

      } catch (error) {
        console.log(error)
      }
      this.waitResult = false
    },

    /** Обновляем паттерн поиска */
    updateSearch: function (event) { this.pattern = event.target.value },

    /** Выделяем тегом <mark></mark> часть в описании, которая совпадает с паттерном поиска
     * @param {String} desc
     */
    markDescription: function (desc) {
      return desc.replace(
          new RegExp(this.last_pattern, 'ig'),
          s => '<mark>'+s+'</mark>'
      )
    }
  },
  computed: {
    paginatedInterfaces: function () {
      // Обрезаем по размеру страницы
      return this.interfaces.slice(
          this.pagination.page * this.pagination.rows_per_page,
          (this.pagination.page + 1) * this.pagination.rows_per_page
      )
    }
  },
  components: {
    "comment": Comment,
    "pagination": Pagination,
    "search-desc": SearchInput,
  }
}

</script>

<style>
mark {
    padding: 0;
}
tr {
    text-align: center;
}
a {
    cursor: pointer;
}
.device:hover svg {
    visibility: visible;
    color: #558af1;
}
.device:hover a {
    color: #558af1;
}

.device:not(:hover) svg {
    visibility: hidden;
    color: rgb(33,37,41);
}
.device:not(:hover) a {
    color: rgb(33,37,41);
}
tr:hover {
    background: #e8efff;
}
</style>