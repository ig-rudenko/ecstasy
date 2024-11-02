<template>
  <Doughnut id="my-chart-id" :options="chartOptions" :data="chartData" :labels="labels"/>
</template>

<script>
import {Doughnut} from 'vue-chartjs'
import {ArcElement, CategoryScale, Chart as ChartJS, LinearScale, Title, Tooltip} from 'chart.js'

ChartJS.register(Title, Tooltip, CategoryScale, LinearScale, ArcElement)

export default {
  name: 'DoughnutChart',
  components: { Doughnut },
  props: {
    data: { required: true, type: Array}
  },
  computed: {
    chartData() {
      return {
        datasets: [
          {
            data: this.data,

          }
        ]
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
          '#cfcfcf',
          '#0dcaf0'
        ],
      }
    }
  }
}
</script>