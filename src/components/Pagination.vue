<template>
<nav aria-label="..." class="py-3 noselect">
    <ul v-if="num_pages > 1" class="pagination justify-content-center">

    <li v-if="page > 2" class="page-item" style="cursor: pointer">
        <a v-if="page > 2" @click="goToPage(0)" class="page-link">1 &lt;&lt; </a>
        <a v-else class="page-link">1 &lt;&lt; </a>
    </li>

    <li class="page-item" v-bind:class="{disabled: page === 0}" style="cursor: pointer">
      <a v-if="page === 0" class="page-link">&lt;</a>
      <a v-else @click="goToPage(page)" class="page-link">&lt;</a>
    </li>

    <li v-if="page !== 0" class="page-item" style="cursor: pointer">
        <a @click="goToPage(page)" class="page-link" >{{ page }}</a>
    </li>

    <li class="page-item active" aria-current="page" style="cursor: pointer">
      <a class="page-link">{{ page + 1 }}</a>
    </li>

    <li v-if="num_pages !== (page + 1)" class="page-item" style="cursor: pointer">
        <a @click="goToPage(page+2)" class="page-link">{{ page + 2 }}</a>
    </li>

    <li v-if="(page + 3) <= num_pages" class="page-item" style="cursor: pointer">
        <a @click="goToPage(page+3)" class="page-link">{{ page + 3 }}</a>
    </li>

    <li class="page-item" v-bind:class="{disabled: (page + 1) === num_pages}" style="cursor: pointer">
      <a v-if="(page + 1) === num_pages" class="page-link">&gt;</a>
      <a v-else @click="goToPage(page+2)" class="page-link">&gt;</a>
    </li>

    <li v-if="(page + 3) < num_pages" class="page-item" style="cursor: pointer">
      <span @click="goToPage(num_pages)" class="page-link"> &gt;&gt; {{ num_pages }}</span>
    </li>

    </ul>
</nav>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
    props: {
      page: {
        required: true,
        type: Number,
        default: 0
      },
      num_pages: {
        required: true,
        type: Number,
        default: 0
      },
      goToPage: {
        required: true,
        type: Function
      }
    }
  }
)
</script>