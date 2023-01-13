<template>
<table class="table">
  <thead>
    <tr>

      <th scope="col">IP</th>

      <th scope="col">Имя</th>

      <th scope="col" class="nav-item dropdown noselect">
          <a class="nav-link dropdown-toggle" data-bs-toggle="dropdown" role="button" aria-expanded="false">
              {{ "Вендор: " + currentVendor }}
          </a>
          <ul class="dropdown-menu" style="cursor: pointer">
                <li class="dropdown-item" @click="setVendor('')">Все вендоры</li>
                <li class="dropdown-item"
                 v-for="vendor in vendors"
                 @click="setVendor(vendor)">{{ vendor }}</li>
          </ul>
      </th>

      <th scope="col">Модель</th>

      <th scope="col"  class="nav-item dropdown noselect">
          <a class="nav-link dropdown-toggle" data-bs-toggle="dropdown" role="button" aria-expanded="false">
              {{ "Группа: " + currentGroup }}
          </a>
          <ul class="dropdown-menu" style="cursor: pointer">
                <li class="dropdown-item" @click="setGroup('')">Все группы</li>
                <li class="dropdown-item"
                 v-for="group in groups"
                 @click="setGroup(group)">{{ group }}</li>
          </ul>
      </th>
    </tr>
  </thead>
  <tbody>
      <tr v-for="dev in devices">

<!--    IP-->
        <td>
          <button class="btn position-relative" style="user-select: all">
            {{ dev.ip }}
          </button>
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

        <td>
          <div style="padding: 0.375rem 0.75rem;">
            {{ dev.model }}
          </div>
        </td>

        <td>
          <div style="padding: 0.375rem 0.75rem;">
            {{ dev.group }}
          </div>
        </td>

      </tr>
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