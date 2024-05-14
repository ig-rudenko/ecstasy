<template>
  <Bar :data="chartData" :options="options"/>
</template>

<script lang="ts">
import {Bar} from 'vue-chartjs'
import {defineComponent} from "vue";
import {BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

export default defineComponent({
  name: "BarChart",
  components: {Bar,},
  props: {
    data: {required: true},
  },
  computed: {
    chartData() {
      return {
        labels: [
          'Абонентские (UP) с описанием',
          'Абонентские (UP) без описания',
          'Абонентские (DOWN) с описанием',
          'Незадействованные порты',
          'Служебные порты',
        ],
        datasets: [{data: this.data}]
      }
    },
    options() {
      return {
        responsive: true,
        backgroundColor: [
          '#198754',
          '#74bf9c',
          '#ffbdbd',
          '#cfcfcf',
          '#0dcaf0'
        ],
      }
    }
  }
})
</script>

<style scoped>

</style>