<template>
  <div class="relative rounded-[1.5rem] border border-gray-200/80 bg-white/80 p-4 shadow-[0_14px_40px_-30px_rgba(15,23,42,0.35)] dark:border-gray-700/80 dark:bg-gray-950/35">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div>
        <div class="text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">Doughnut</div>
        <div class="mt-1 text-sm font-semibold text-gray-900 dark:text-gray-100">Доли категорий</div>
      </div>
      <div class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-xs font-mono text-gray-600 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300">
        {{ total }} портов
      </div>
    </div>

    <div class="relative mx-auto h-[240px] w-[240px]">
      <Doughnut id="devices-workload-chart" :options="chartOptions" :data="chartData"/>
      <div class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
        <div class="text-[11px] font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400">Всего</div>
        <div class="mt-1 text-3xl font-semibold text-gray-900 dark:text-gray-100">{{ total }}</div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {PropType} from "vue";
import {Doughnut} from "vue-chartjs";
import {ArcElement, Chart as ChartJS, Legend, Tooltip} from "chart.js";

ChartJS.register(Tooltip, ArcElement, Legend);

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

export default {
  name: "DoughnutChart",
  components: {Doughnut},
  props: {
    data: {required: true, type: Array as PropType<number[]>}
  },
  computed: {
    total(): number {
      return this.data.reduce((sum, value) => sum + Number(value || 0), 0);
    },
    chartData() {
      return {
        labels: chartLabels,
        datasets: [
          {
            data: this.data,
            backgroundColor: chartColors,
            borderColor: ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
            borderWidth: 3,
            hoverBorderWidth: 3,
            spacing: 4,
            hoverOffset: 6,
          }
        ]
      };
    },
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
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
            callbacks: {
              label: (context: any) => `${context.label}: ${context.raw}`,
            }
          }
        }
      };
    }
  }
};
</script>
