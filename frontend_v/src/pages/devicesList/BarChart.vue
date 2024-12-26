<template>
  <Bar :data="chartData" :options="options"/>
</template>

<script lang="ts">
import {Bar} from 'vue-chartjs';
import {defineComponent, PropType} from "vue";
import {BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

export default defineComponent({
  name: "BarChart",
  components: {Bar,},
  props: {
    data: {required: true, type: Object as PropType<number[]>},
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
          'rgb(21 128 61)',
          'rgb(34 197 94)',
          'rgb(252 165 165)',
          'rgb(209 213 219)',
          'rgb(96 165 250)'
        ],
      }
    }
  }
})
</script>

<style scoped>

</style>