<template>
<nav v-if="num_pages > 1" class="py-2 noselect">
    <ul class="pagination justify-content-center">

    <li v-if="pObject.page > 2" class="page-item" style="cursor: pointer">
        <a v-if="pObject.page > 2" @click="goToPage(0)" class="page-link">1 &lt;&lt; </a>
        <a v-else class="page-link">1 &lt;&lt; </a>
    </li>

    <li class="page-item" v-bind:class="{disabled: pObject.page === 0}" style="cursor: pointer">
      <a v-if="pObject.page === 0" class="page-link">&lt;</a>
      <a v-else @click="goToPage(pObject.page)" class="page-link">&lt;</a>
    </li>

    <li v-if="pObject.page !== 0" class="page-item" style="cursor: pointer">
        <a @click="goToPage(pObject.page)" class="page-link" >{{ pObject.page }}</a>
    </li>

    <li class="page-item active" aria-current="page" style="cursor: pointer">
      <a class="page-link">{{ pObject.page + 1 }}</a>
    </li>

    <li v-if="num_pages !== (pObject.page + 1)" class="page-item" style="cursor: pointer">
        <a @click="goToPage(pObject.page+2)" class="page-link">{{ pObject.page+2 }}</a>
    </li>

    <li v-if="(pObject.page + 3) <= num_pages" class="page-item" style="cursor: pointer">
        <a @click="goToPage(pObject.page+3)" class="page-link">{{ pObject.page+3 }}</a>
    </li>

    <li class="page-item" v-bind:class="{disabled: (pObject.page + 1) === num_pages}" style="cursor: pointer">
      <a v-if="(pObject.page + 1) === num_pages" class="page-link">&gt;</a>
      <a v-else @click="goToPage(pObject.page+2)" class="page-link">&gt;</a>
    </li>

    <li v-if="(pObject.page + 3) < num_pages" class="page-item" style="cursor: pointer">
      <span @click="goToPage(num_pages)" class="page-link"> &gt;&gt; {{ num_pages }}</span>
    </li>

    </ul>
</nav>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
    pObject: {
      required: true,
      type: {
          count: Number,
          page: Number,
          rows_per_page: Number
      },
    }
  },
  computed: {
    num_pages: function () {
      return Math.floor(this.pObject.count / this.pObject.rows_per_page) + 1
    },
  },
  methods: {
    goToPage: function (num) {
      if (num <= 0) {
        this.pObject.page = 0
      } else if (num >= this.pObject.num_pages){
        this.pObject.page = this.pObject.num_pages - 1
      } else {
        this.pObject.page = num - 1
      }
    }
  }
})
</script>