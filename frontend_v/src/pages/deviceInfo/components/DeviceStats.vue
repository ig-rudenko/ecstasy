<template>
  <div class="flex flex-wrap gap-3 items-center justify-end p-3 dark:text-gray-300">
    <!--  UPTIME -->
    <div v-if="uptime>0">
      <div v-tooltip.bottom="'Время работы'" class="flex gap-2 items-center">
        <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 16 16">
          <path
              d="M8.515 1.019A7 7 0 0 0 8 1V0a8 8 0 0 1 .589.022zm2.004.45a7 7 0 0 0-.985-.299l.219-.976q.576.129 1.126.342zm1.37.71a7 7 0 0 0-.439-.27l.493-.87a8 8 0 0 1 .979.654l-.615.789a7 7 0 0 0-.418-.302zm1.834 1.79a7 7 0 0 0-.653-.796l.724-.69q.406.429.747.91zm.744 1.352a7 7 0 0 0-.214-.468l.893-.45a8 8 0 0 1 .45 1.088l-.95.313a7 7 0 0 0-.179-.483m.53 2.507a7 7 0 0 0-.1-1.025l.985-.17q.1.58.116 1.17zm-.131 1.538q.05-.254.081-.51l.993.123a8 8 0 0 1-.23 1.155l-.964-.267q.069-.247.12-.501m-.952 2.379q.276-.436.486-.908l.914.405q-.24.54-.555 1.038zm-.964 1.205q.183-.183.35-.378l.758.653a8 8 0 0 1-.401.432z"/>
          <path d="M8 1a7 7 0 1 0 4.95 11.95l.707.707A8.001 8.001 0 1 1 8 0z"/>
          <path
              d="M7.5 3a.5.5 0 0 1 .5.5v5.21l3.248 1.856a.5.5 0 0 1-.496.868l-3.5-2A.5.5 0 0 1 7 9V3.5a.5.5 0 0 1 .5-.5"/>
        </svg>
        <span>{{ formatUptime(uptime) }}</span>
      </div>
    </div>

    <!--  CPU-->
    <div class="flex gap-2 items-center">
      <svg
          v-bind:fill="stats.cpu?valueColor(Math.max(...stats.cpu.util)):'grey'"
          class="bi bi-cpu" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" width="30" height="30">
        <path
            d="M5 0a.5.5 0 0 1 .5.5V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2A2.5 2.5 0 0 1 14 4.5h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14a2.5 2.5 0 0 1-2.5 2.5v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14A2.5 2.5 0 0 1 2 11.5H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2A2.5 2.5 0 0 1 4.5 2V.5A.5.5 0 0 1 5 0zm-.5 3A1.5 1.5 0 0 0 3 4.5v7A1.5 1.5 0 0 0 4.5 13h7a1.5 1.5 0 0 0 1.5-1.5v-7A1.5 1.5 0 0 0 11.5 3h-7zM5 6.5A1.5 1.5 0 0 1 6.5 5h3A1.5 1.5 0 0 1 11 6.5v3A1.5 1.5 0 0 1 9.5 11h-3A1.5 1.5 0 0 1 5 9.5v-3zM6.5 6a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3z"/>
      </svg>
      <span v-if="stats.cpu"> cpu {{ stats.cpu.util.join(', ') }}%</span>
      <span v-else> cpu -</span>
    </div>

    <!--  RAM-->
    <div class="flex gap-2 items-center">
      <svg
          v-bind:fill="stats.ram?valueColor(stats.ram.util):'grey'"
          class="bi bi-memory" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" width="30" height="30">
        <path
            d="M1 3a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h4.586a1 1 0 0 0 .707-.293l.353-.353a.5.5 0 0 1 .708 0l.353.353a1 1 0 0 0 .707.293H15a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H1Zm.5 1h3a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-4a.5.5 0 0 1 .5-.5Zm5 0h3a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-4a.5.5 0 0 1 .5-.5Zm4.5.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-4ZM2 10v2H1v-2h1Zm2 0v2H3v-2h1Zm2 0v2H5v-2h1Zm3 0v2H8v-2h1Zm2 0v2h-1v-2h1Zm2 0v2h-1v-2h1Zm2 0v2h-1v-2h1Z"/>
      </svg>
      <span v-if="stats.ram"> ram {{ stats.ram.util }}%</span>
      <span v-else> ram -</span>
    </div>

    <!--  FLASH-->
    <div class="flex gap-2 items-center">
      <svg v-bind:fill="stats.flash?valueColor(stats.flash.util):'grey'"
           class="bi bi-sd-card-fill" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" width="30" height="30">
        <path
            d="M12.5 0H5.914a1.5 1.5 0 0 0-1.06.44L2.439 2.853A1.5 1.5 0 0 0 2 3.914V14.5A1.5 1.5 0 0 0 3.5 16h9a1.5 1.5 0 0 0 1.5-1.5v-13A1.5 1.5 0 0 0 12.5 0Zm-7 2.75a.75.75 0 0 1 .75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 .75-.75Zm2 0a.75.75 0 0 1 .75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 .75-.75Zm2.75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 1.5 0Zm1.25-.75a.75.75 0 0 1 .75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 .75-.75Z"/>
      </svg>
      <span v-if="stats.flash"> flash {{ stats.flash.util }}%</span>
      <span v-else> flash -</span>
    </div>

    <!--  TEMP-->
    <div v-if="stats.temp" class="flex gap-2 items-center">
      <!--LOW-->
      <svg v-if="stats.temp.status === 'low'"
           xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="#0d6efd" viewBox="0 0 16 16">
        <path d="M8 14a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/>
        <path
            d="M8 0a2.5 2.5 0 0 0-2.5 2.5v7.55a3.5 3.5 0 1 0 5 0V2.5A2.5 2.5 0 0 0 8 0zM6.5 2.5a1.5 1.5 0 1 1 3 0v7.987l.167.15a2.5 2.5 0 1 1-3.333 0l.166-.15V2.5z"/>
      </svg>

      <!--NORMAL-->
      <svg v-else-if="stats.temp.status === 'normal'"
           xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="#198754" viewBox="0 0 16 16">
        <path d="M9.5 12.5a1.5 1.5 0 1 1-2-1.415V9.5a.5.5 0 0 1 1 0v1.585a1.5 1.5 0 0 1 1 1.415z"/>
        <path
            d="M5.5 2.5a2.5 2.5 0 0 1 5 0v7.55a3.5 3.5 0 1 1-5 0V2.5zM8 1a1.5 1.5 0 0 0-1.5 1.5v7.987l-.167.15a2.5 2.5 0 1 0 3.333 0l-.166-.15V2.5A1.5 1.5 0 0 0 8 1z"/>
      </svg>

      <!--MEDIUM-->
      <svg v-else-if="stats.temp.status === 'medium'"
           xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="#ff9836" viewBox="0 0 16 16">
        <path d="M9.5 12.5a1.5 1.5 0 1 1-2-1.415V6.5a.5.5 0 0 1 1 0v4.585a1.5 1.5 0 0 1 1 1.415z"/>
        <path
            d="M5.5 2.5a2.5 2.5 0 0 1 5 0v7.55a3.5 3.5 0 1 1-5 0V2.5zM8 1a1.5 1.5 0 0 0-1.5 1.5v7.987l-.167.15a2.5 2.5 0 1 0 3.333 0l-.166-.15V2.5A1.5 1.5 0 0 0 8 1z"/>
      </svg>

      <!--HIGH-->
      <svg v-else-if="stats.temp.status === 'high'"
           xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="#dc3545" viewBox="0 0 16 16">
        <path d="M9.5 12.5a1.5 1.5 0 1 1-2-1.415V2.5a.5.5 0 0 1 1 0v8.585a1.5 1.5 0 0 1 1 1.415z"/>
        <path
            d="M5.5 2.5a2.5 2.5 0 0 1 5 0v7.55a3.5 3.5 0 1 1-5 0V2.5zM8 1a1.5 1.5 0 0 0-1.5 1.5v7.987l-.167.15a2.5 2.5 0 1 0 3.333 0l-.166-.15V2.5A1.5 1.5 0 0 0 8 1z"/>
      </svg>
      {{ stats.temp.value + '℃' || "-" }}
    </div>

    <div v-else class="flex gap-2 items-center">
      <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="grey" viewBox="0 0 16 16">
        <path d="M8 14a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/>
        <path
            d="M8 0a2.5 2.5 0 0 0-2.5 2.5v7.55a3.5 3.5 0 1 0 5 0V2.5A2.5 2.5 0 0 0 8 0zM6.5 2.5a1.5 1.5 0 1 1 3 0v7.987l.167.15a2.5 2.5 0 1 1-3.333 0l.166-.15V2.5z"/>
      </svg>
      temp -
    </div>
  </div>

</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import {HardwareStats} from "../hardwareStats";

export default defineComponent({
  props: {
    stats: {required: true, type: Object as PropType<HardwareStats>},
    uptime: {required: false, type: Number, default: -1}
  },
  methods: {
    valueColor(value: number): string {
      if (!value) return "grey"
      if (value < 30) return "#198754";
      if (value < 80) return "#ff9836";
      return "#dc3545";
    },
    formatUptime(seconds: number) {
      if (seconds < 0) return ""
      const units = [
        {name: 'год', seconds: 365 * 24 * 60 * 60},
        {name: 'месяц', seconds: 30 * 24 * 60 * 60},
        {name: 'день', seconds: 24 * 60 * 60},
        {name: 'час', seconds: 60 * 60},
        {name: 'минута', seconds: 60},
        {name: 'секунда', seconds: 1}
      ];

      let result: string[] = [];

      for (let unit of units) {
        const quotient = Math.floor(seconds / unit.seconds);
        if (quotient > 0) {
          result.push(`${quotient} ${this.decline(unit.name, quotient)}`);
          seconds -= quotient * unit.seconds;
        }
        if (result.length === 3) {
          break;
        }
      }

      return result.join(', ');
    },

    decline(unit: string, count: number): string {
      const declensions: any = {
        'год': ['год', 'года', 'лет'],
        'месяц': ['месяц', 'месяца', 'месяцев'],
        'день': ['день', 'дня', 'дней'],
        'час': ['час', 'часа', 'часов'],
        'минута': ['минута', 'минуты', 'минут'],
        'секунда': ['секунда', 'секунды', 'секунд']
      };

      let forms = declensions[unit];
      return (count % 10 == 1 && count % 100 != 11) ? forms[0] :
          (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) ? forms[1] : forms[2];
    }

  }
})
</script>