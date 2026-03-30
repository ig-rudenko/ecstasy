<template>
  <div class="flex flex-wrap justify-between gap-3">
    <div class="flex items-center justify-between gap-3">
      <div v-if="uptime > 0" class="inline-flex items-center gap-2 rounded-2xl border border-gray-200/70 bg-gray-50/80 px-3 py-2 text-xs text-gray-600 dark:border-gray-700/70 dark:bg-gray-800/60 dark:text-gray-300">
        <i class="pi pi-clock text-[0.8rem] text-indigo-500 dark:text-indigo-300" />
        <span class="font-medium">{{ formatUptime(uptime) }}</span>
      </div>
    </div>

    <div class="flex flex-wrap gap-2">
      <article
          v-for="item in statItems"
          :key="item.label"
          class=" flex items-center gap-3 rounded-2xl border border-gray-200/70 bg-white/75 px-3 py-3 dark:border-gray-700/70 dark:bg-gray-800/45"
      >
        <div
            class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gray-100/80 dark:bg-gray-700/40"
            :style="{ color: item.color }"
        >
          <component :is="item.icon" />
        </div>
        <div class="min-w-0">
          <div class="text-[11px] font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-gray-400 font-mono">
            {{ item.label }}
          </div>
          <div class="truncate text-gray-900 dark:text-gray-100 font-mono">
            {{ item.value }}
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent, h, PropType} from "vue";
import {HardwareStats} from "../hardwareStats";

function iconWrapper(paths: string[]) {
  return () => h("svg", {
    xmlns: "http://www.w3.org/2000/svg",
    width: 26,
    height: 26,
    viewBox: "0 0 16 16",
    fill: "currentColor"
  }, paths.map((d) => h("path", {d})));
}

const CpuIcon = iconWrapper([
  "M5 0a.5.5 0 0 1 .5.5V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2A2.5 2.5 0 0 1 14 4.5h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14a2.5 2.5 0 0 1-2.5 2.5v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14A2.5 2.5 0 0 1 2 11.5H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2A2.5 2.5 0 0 1 4.5 2V.5A.5.5 0 0 1 5 0zm-.5 3A1.5 1.5 0 0 0 3 4.5v7A1.5 1.5 0 0 0 4.5 13h7a1.5 1.5 0 0 0 1.5-1.5v-7A1.5 1.5 0 0 0 11.5 3h-7z",
  "M6.5 6a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3z"
]);
const RamIcon = iconWrapper([
  "M1 3a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h4.586a1 1 0 0 0 .707-.293l.353-.353a.5.5 0 0 1 .708 0l.353.353a1 1 0 0 0 .707.293H15a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H1Zm.5 1h3a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-4a.5.5 0 0 1 .5-.5Zm5 0h3a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-4a.5.5 0 0 1 .5-.5Zm4.5.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-4Z",
  "M2 10v2H1v-2h1Zm2 0v2H3v-2h1Zm2 0v2H5v-2h1Zm3 0v2H8v-2h1Zm2 0v2h-1v-2h1Zm2 0v2h-1v-2h1Zm2 0v2h-1v-2h1Z"
]);
const FlashIcon = iconWrapper([
  "M12.5 0H5.914a1.5 1.5 0 0 0-1.06.44L2.439 2.853A1.5 1.5 0 0 0 2 3.914V14.5A1.5 1.5 0 0 0 3.5 16h9a1.5 1.5 0 0 0 1.5-1.5v-13A1.5 1.5 0 0 0 12.5 0Zm-7 2.75a.75.75 0 0 1 .75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 .75-.75Zm2 0a.75.75 0 0 1 .75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 .75-.75Zm2.75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 1.5 0Zm1.25-.75a.75.75 0 0 1 .75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 .75-.75Z"
]);
const TempIcon = iconWrapper([
  "M9.5 12.5a1.5 1.5 0 1 1-2-1.415V2.5a.5.5 0 0 1 1 0v8.585a1.5 1.5 0 0 1 1 1.415z",
  "M5.5 2.5a2.5 2.5 0 0 1 5 0v7.55a3.5 3.5 0 1 1-5 0V2.5zM8 1a1.5 1.5 0 0 0-1.5 1.5v7.987l-.167.15a2.5 2.5 0 1 0 3.333 0l-.166-.15V2.5A1.5 1.5 0 0 0 8 1z"
]);

export default defineComponent({
  props: {
    stats: {required: true, type: Object as PropType<HardwareStats>},
    uptime: {required: false, type: Number, default: -1}
  },
  computed: {
    tempColor(): string {
      if (!this.stats.temp) return "#94a3b8";
      if (this.stats.temp.status === "low") return "#2563eb";
      if (this.stats.temp.status === "normal") return "#16a34a";
      if (this.stats.temp.status === "medium") return "#f59e0b";
      return "#dc2626";
    },
    statItems(): { label: string; value: string; color: string; icon: any }[] {
      return [
        {
          label: "CPU",
          value: this.stats.cpu ? `${this.stats.cpu.util.join(", ")}%` : "-",
          color: this.stats.cpu ? this.valueColor(Math.max(...this.stats.cpu.util)) : "#94a3b8",
          icon: CpuIcon
        },
        {
          label: "RAM",
          value: this.stats.ram ? `${this.stats.ram.util}%` : "-",
          color: this.stats.ram ? this.valueColor(this.stats.ram.util) : "#94a3b8",
          icon: RamIcon
        },
        {
          label: "Flash",
          value: this.stats.flash ? ` ${this.stats.flash.util}%` : "-",
          color: this.stats.flash ? this.valueColor(this.stats.flash.util) : "#94a3b8",
          icon: FlashIcon
        },
        {
          label: "Temp",
          value: this.stats.temp?.value ? `${this.stats.temp.value}℃` : "-",
          color: this.tempColor,
          icon: TempIcon
        }
      ];
    }
  },
  methods: {
    valueColor(value: number): string {
      if (!value) return "#94a3b8";
      if (value < 30) return "#198754";
      if (value < 80) return "#ff9836";
      return "#dc3545";
    },
    formatUptime(seconds: number) {
      if (seconds < 0) return "";
      const units = [
        {name: "год", seconds: 365 * 24 * 60 * 60},
        {name: "месяц", seconds: 30 * 24 * 60 * 60},
        {name: "день", seconds: 24 * 60 * 60},
        {name: "час", seconds: 60 * 60},
        {name: "минута", seconds: 60},
        {name: "секунда", seconds: 1}
      ];

      const result: string[] = [];

      for (const unit of units) {
        const quotient = Math.floor(seconds / unit.seconds);
        if (quotient > 0) {
          result.push(`${quotient} ${this.decline(unit.name, quotient)}`);
          seconds -= quotient * unit.seconds;
        }
        if (result.length === 2) {
          break;
        }
      }

      return result.join(", ");
    },
    decline(unit: string, count: number): string {
      const declensions: Record<string, string[]> = {
        "год": ["год", "года", "лет"],
        "месяц": ["месяц", "месяца", "месяцев"],
        "день": ["день", "дня", "дней"],
        "час": ["час", "часа", "часов"],
        "минута": ["минута", "минуты", "минут"],
        "секунда": ["секунда", "секунды", "секунд"]
      };

      const forms = declensions[unit];
      return (count % 10 === 1 && count % 100 !== 11) ? forms[0] :
          (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) ? forms[1] : forms[2];
    }
  }
});
</script>
