<template>
<table class="table head-padding">
  <thead>
    <tr>

      <th scope="col" class="text-center">IP</th>

      <th scope="col" style="padding-left: 2.5rem;">Имя</th>

      <th scope="col" class="noselect" style="padding-left: 0;">

          <span class="badge bg-primary" data-bs-toggle="dropdown" role="button" style="font-size: 15px;">
              {{ "Вендор: " + currentVendor }}
          </span>
          <ul class="dropdown-menu" style="cursor: pointer">
                <li class="dropdown-item" @click="setVendor('')">Все вендоры</li>
                <li class="dropdown-item"
                 v-for="vendor in vendors"
                 @click="setVendor(vendor)">{{ vendor }}</li>
          </ul>
      </th>

      <th scope="col">Модель</th>

      <th scope="col"  class="noselect" style="padding-left: 0;">
          <span class="badge bg-primary" data-bs-toggle="dropdown" role="button" style="font-size: 15px;">
              {{ "Группа: " + currentGroup }}
          </span>
          <ul class="dropdown-menu" style="cursor: pointer">
                <li class="dropdown-item" @click="setGroup('')">Все группы</li>
                <li class="dropdown-item"
                 v-for="group in groups"
                 @click="setGroup(group)">{{ group }}</li>
          </ul>
      </th>
    </tr>
  </thead>


  <tbody style="vertical-align: middle;">

      <template v-for="dev in devices">
        <tr :style="dev.interfaces_count?{'border-bottom': 'hidden'}:{}">
    <!--    IP-->
            <td class="text-center table-padding">
                {{ dev.ip }}
            </td>

    <!--    NAME-->
            <td>
              <a class="text-decoration-none nowrap btn btn-outline-primary"
                 style="border: none;"
                 :href="'/device/' + dev.name"
                 >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-right" viewBox="0 0 16 16">
                  <path d="M6 12.796V3.204L11.481 8 6 12.796zm.659.753 5.48-4.796a1 1 0 0 0 0-1.506L6.66 2.451C6.011 1.885 5 2.345 5 3.204v9.592a1 1 0 0 0 1.659.753z"/>
                </svg>
                {{ dev.name }}
              </a>
            </td>

    <!--    VENDOR-->
            <td>
              <button
                  @click="setVendor(dev.vendor)"
                  v-if="dev.vendor"
                  class="btn position-relative">
                {{ dev.vendor }}
                <span
                    :style="{'background-color': stringToColour(dev.vendor)}"
                    class="position-absolute top-50 start-0 translate-middle p-2 border border-light rounded-circle">
                </span>
              </button>
            </td>

            <td class="table-padding">
                {{ dev.model }}
            </td>

            <td class="table-padding">
                {{ dev.group }}
            </td>
          </tr>

          <tr v-if="dev.interfaces_count && dev.interfaces_count.abons">

            <td class="table-padding" colspan="5" style="padding-bottom: 1.5rem;">
            <div class="col-5">
              <div class="progress">

<!--                Абонентские порты UP С ОПИСАНИЕМ -->
                <div v-if="dev.interfaces_count.abons_up_with_desc"
                     class="progress-bar bg-success" role="progressbar"
                     :style="{width: dev.interfaces_count.abons_up_with_desc / dev.interfaces_count.abons * 100 + '%'}"
                     :aria-valuemax="dev.interfaces_count.abons">
                  {{ dev.interfaces_count.abons_up_with_desc }}
                </div>

<!--                Абонентские порты UP Без описания -->
                <div class="progress-bar" role="progressbar" style="background-color: #74bf9c"
                     v-if="dev.interfaces_count.abons_up_no_desc"
                     :style="{width: dev.interfaces_count.abons_up_no_desc / dev.interfaces_count.abons * 100 + '%'}"
                     :aria-valuemax="dev.interfaces_count.abons">
                  {{ dev.interfaces_count.abons_up_no_desc }}
                </div>

<!--                Абонентские порты DOWN С ОПИСАНИЕМ -->
                <div class="progress-bar text-dark" role="progressbar" style="background-color: #ffbdbd"
                     v-if="dev.interfaces_count.abons_down_with_desc"
                     :style="{width: dev.interfaces_count.abons_down_with_desc / dev.interfaces_count.abons * 100 + '%'}"
                     :aria-valuemax="dev.interfaces_count.abons">
                  {{ dev.interfaces_count.abons_down_with_desc }}
                </div>

<!--                Абонентские порты Остальные-->
                <div class="progress-bar text-dark" role="progressbar" style="background-color: #cfcfcf"
                     v-if="dev.interfaces_count.abons_down_no_desc"
                     :style="{width: dev.interfaces_count.abons_down_no_desc / dev.interfaces_count.abons * 100 + '%'}"
                     :aria-valuemax="dev.interfaces_count.abons">
                  {{ dev.interfaces_count.abons_down_no_desc }}
                </div>

              </div>
            </div>
            </td>
          </tr>

      </template>

  </tbody>
</table>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
      devices: {
        required: true,
        type: Array,
        default: function () { return [] }
      },
      setVendor: {
        required: true,
        type: Function
      },
      setGroup: {
        required: true,
        type: Function
      },
      currentVendor: {
        required: true,
        type: String
      },
      currentGroup: {
        required: true,
        type: String
      },
      vendors: {
        required: true,
        type: Array
      },
      groups: {
        required:true,
        type: Array
      }
  },
  methods: {
    stringToColour: function(str) {
      if (!str) return '';
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
         hash = str.toLowerCase().charCodeAt(i) + ((hash << 5) - hash);
      }
      let c = (hash & 0x00FFFFFF)
          .toString(16)
          .toUpperCase();
      console.log("00000".substring(0, 6 - c.length) + c)
      return "#" + "00000".substring(0, 6 - c.length) + c;
    }
  }
})
</script>

<style scoped>
.head-padding th {
  padding: 0.875rem 1.25rem;
}
</style>