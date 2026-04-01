<template>
  <div class="rounded-3xl border border-gray-200/80 bg-white/30 p-4 dark:border-gray-700/80 dark:bg-gray-950/35">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div>
        <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">Bar Chart</div>
        <div class="mt-1 text-sm font-semibold text-gray-900 dark:text-gray-100">Распределение категорий</div>
      </div>
    </div>
    <div class="h-[320px]">
      <Bar :data="chartData" :options="options"/>
    </div>
  </div>
</template>

<script lang="ts">
import {Bar} from "vue-chartjs";
import {defineComponent, PropType} from "vue";
import {BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const chartLabels = [
  "Абонентские UP с описанием",
  "Абонентские UP без описания",
  "Абонентские DOWN с описанием",
  "Незадействованные порты",
  "Служебные порты",
];

const chartColors = [
  "#166534",
  "#22c55e",
  "#fca5a5",
  "#cbd5e1",
  "#60a5fa",
];

export default defineComponent({
  name: "BarChart",
  components: {Bar},
  props: {
    data: {required: true, type: Object as PropType<number[]>},
  },
  computed: {
    chartData() {
      return {
        labels: chartLabels,
        datasets: [
          {
            label: "Порты",
            data: this.data,
            backgroundColor: chartColors,
            borderRadius: 12,
            borderSkipped: false,
            maxBarThickness: 42,
          }
        ]
      };
    },
    options() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 500,
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: "rgba(15,23,42,0.92)",
            titleColor: "#f8fafc",
            bodyColor: "#e2e8f0",
            padding: 12,
            displayColors: true,
            cornerRadius: 12,
          }
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              color: "#64748b",
              font: {
                size: 0,
              },
            },
            border: {
              display: false,
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              color: "rgba(148, 163, 184, 0.18)",
              drawBorder: false,
            },
            ticks: {
              color: "#64748b",
              precision: 0,
              font: {
                size: 11,
              },
            },
            border: {
              display: false,
            }
          }
        }
      };
    }
  }
});
</script>
