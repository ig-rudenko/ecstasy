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
          'rgb(21 128 61)',
          'rgb(34 197 94)',
          'rgb(252 165 165)',
          'rgb(209 213 219)',
          'rgb(96 165 250)'
        ],
      }
    }
  }
}
</script>