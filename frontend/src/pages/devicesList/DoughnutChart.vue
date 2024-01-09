<template>
  <Doughnut id="my-chart-id" :options="chartOptions" :data="chartData"/>
</template>

<script>
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, CategoryScale, LinearScale, ArcElement } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, CategoryScale, LinearScale, ArcElement)

export default {
  name: 'DoughnutChart',
  components: { Doughnut },
  props: {
    data: { required: true, type: Array}
  },
  computed: {
    chartData() {
      return {
        datasets: [ {
          data: this.data,
          label: 'Кол-во интерфейсов',
        } ]
      }
    },
    chartOptions() {
      return {
        hoverOffset: 10,
        responsive: true,
        backgroundColor: [
          '#198754',
          '#74bf9c',
          '#ffbdbd',
          '#cfcfcf'
        ],
      }
    }
  }
}
</script>