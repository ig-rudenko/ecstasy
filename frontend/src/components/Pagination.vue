<template>
<nav v-if="pObject.pagesCount > 1" class="py-2 noselect">
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

    <li v-if="pObject.pagesCount !== (pObject.page + 1)" class="page-item" style="cursor: pointer">
        <a @click="goToPage(pObject.page+2)" class="page-link">{{ pObject.page+2 }}</a>
    </li>

    <li v-if="(pObject.page + 3) <= pObject.pagesCount" class="page-item" style="cursor: pointer">
        <a @click="goToPage(pObject.page+3)" class="page-link">{{ pObject.page+3 }}</a>
    </li>

    <li class="page-item" v-bind:class="{disabled: (pObject.page + 1) === pObject.pagesCount}" style="cursor: pointer">
      <a v-if="(pObject.page + 1) === pObject.pagesCount" class="page-link">&gt;</a>
      <a v-else @click="goToPage(pObject.page+2)" class="page-link">&gt;</a>
    </li>

    <li v-if="(pObject.page + 3) < pObject.pagesCount" class="page-item" style="cursor: pointer">
      <span @click="goToPage(pObject.pagesCount)" class="page-link"> &gt;&gt; {{ pObject.pagesCount }}</span>
    </li>

    </ul>
</nav>
</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import Paginator from "../types/paginator";

export default defineComponent({
  props: {
    pObject: {required: true, type: Object as PropType<Paginator>}
  },
  methods: {
    goToPage: function (num: number) {
      if (num <= 0) {
        this.pObject.page = 0
      } else if (num >= this.pObject.pagesCount){
        this.pObject.page = this.pObject.pagesCount - 1
      } else {
        this.pObject.page = num - 1
      }
    }
  }
})
</script>

<style>
.noselect {
  -webkit-touch-callout: none; /* iOS Safari */
    -webkit-user-select: none; /* Safari */
     -khtml-user-select: none; /* Konqueror HTML */
       -moz-user-select: none; /* Old versions of Firefox */
        -ms-user-select: none; /* Internet Explorer/Edge */
            user-select: none; /* Non-prefixed version, currently
                                  supported by Chrome, Edge, Opera and Firefox */
}
</style>