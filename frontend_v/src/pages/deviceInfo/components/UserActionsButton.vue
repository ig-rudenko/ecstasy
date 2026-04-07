<template>
  <Button text @click="openDialog" v-tooltip.bottom="'Пользовательские действия'" class="rounded-2xl shadow-sm border-none">
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 16 16">
      <path d="M6 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm-5 6s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H1zM11 3.5a.5.5 0 0 1 .5-.5h4a.5.5 0 0 1 0 1h-4a.5.5 0 0 1-.5-.5zm.5 2.5a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1h-4zm2 3a.5.5 0 0 0 0 1h2a.5.5 0 0 0 0-1h-2zm0 3a.5.5 0 0 0 0 1h2a.5.5 0 0 0 0-1h-2z"></path>
    </svg>
  </Button>

  <Dialog v-model:visible="showDialog" header="Пользовательские действия" modal class="w-[min(96vw,1100px)]" content-class="!p-0">
    <div class="flex flex-col gap-5 bg-gray-50/60 p-4 dark:bg-gray-950/30 sm:p-6">
      <Message v-if="error.status" severity="error" class="rounded-2xl">
        Ошибка загрузки: {{ error.status }}. {{ error.msg }}
      </Message>

      <section v-if="filteredActions?.length" class="rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">История действий</div>
            <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Фильтрация по пользователю и тексту действия.</div>
          </div>

          <div class="grid gap-3 md:grid-cols-2 lg:min-w-lg">
            <IconField>
              <InputIcon class="pi pi-search" />
              <InputText v-model.trim="filters.user" placeholder="Фильтр по пользователю" fluid class="rounded-2xl"/>
            </IconField>
            <IconField>
              <InputIcon class="pi pi-search" />
              <InputText v-model.trim="filters.action" placeholder="Фильтр по действию" fluid class="rounded-2xl"/>
            </IconField>
          </div>
        </div>
      </section>

      <section class="rounded-3xl border border-gray-200/80 bg-white/85 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
        <div v-if="filteredActions?.length" class="divide-y divide-gray-200/80 dark:divide-gray-700/80">
          <article v-for="act in filteredActions" :key="`${act.user}-${act.time}-${act.action}`" class="grid gap-4 px-4 py-4 md:grid-cols-[minmax(0,14rem),minmax(0,1fr)]">
            <div class="flex items-center gap-3">
              <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-sky-100 text-sm font-semibold uppercase text-sky-700 dark:bg-sky-500/15 dark:text-sky-300">
                {{ initials(act.user) }}
              </div>
              <div class="min-w-0">
                <div class="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">{{ act.user }}</div>
                <div class="mt-1 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                  <i class="pi pi-clock" />
                  <span>{{ formatTime(act.time) }}</span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <div class="mt-0.5 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                <i :class="actionIcon(act.action).icon" :style="{ color: actionIcon(act.action).color }" />
              </div>
              <div class="min-w-0">
                <div class="text-sm leading-6 text-gray-700 dark:text-gray-200">{{ act.action }}</div>
              </div>
            </div>
          </article>
        </div>

        <div v-else-if="actions" class="px-4 py-10 text-center text-sm text-gray-500 dark:text-gray-400">
          Действия не найдены
        </div>

        <div v-else class="flex justify-center p-8">
          <ProgressSpinner />
        </div>
      </section>
    </div>
  </Dialog>
</template>

<script lang="ts">
import api from "@/services/api";
import {defineComponent} from "vue";
import {AxiosResponse} from "axios";

interface UserAction {
  action: string
  time: string
  user: string
}

export default defineComponent({
  name: "UserActionsButton",
  props: {
    deviceName: {required: true, type: String},
  },
  data() {
    return {
      showDialog: false,
      actions: null as UserAction[] | null,
      filters: {
        user: "",
        action: "",
      },
      error: {
        status: null as number | null,
        msg: null as string | null,
      }
    };
  },
  computed: {
    filteredActions(): UserAction[] | null {
      if (!this.actions) return null;
      const userQuery = this.filters.user.trim().toLowerCase();
      const actionQuery = this.filters.action.trim().toLowerCase();

      return this.actions.filter((item) => {
        const matchesUser = !userQuery || item.user.toLowerCase().includes(userQuery);
        const matchesAction = !actionQuery || item.action.toLowerCase().includes(actionQuery);
        return matchesUser && matchesAction;
      });
    }
  },
  methods: {
    openDialog() {
      this.showDialog = true;
      this.error.status = null;
      this.error.msg = null;
      api.get(`/api/v1/devices/${this.deviceName}/actions`).then(
          (resp: AxiosResponse<UserAction[]>) => {
            this.actions = resp.data;
          }
      ).catch(
          (reason) => {
            this.error.status = reason.response.status;
            this.error.msg = reason.response.data;
          }
      );
    },
    initials(user: string): string {
      return user
          .split(/\s+/)
          .filter(Boolean)
          .slice(0, 2)
          .map((part) => part[0]?.toUpperCase())
          .join("") || "?";
    },
    actionIcon(action: string): { icon: string; color: string } {
      if (action.match("up port")) return {icon: "pi pi-arrow-up-right", color: "#22c55e"};
      if (action.match("down port")) return {icon: "pi pi-arrow-down-right", color: "#ef4444"};
      if (action.match("reload port")) return {icon: "pi pi-refresh", color: "#f59e0b"};
      if (action.match("Saved OK")) return {icon: "pi pi-check-circle", color: "#22c55e"};
      if (action.match("Saved ERROR")) return {icon: "pi pi-times-circle", color: "#f97316"};
      if (action.match("Without saving")) return {icon: "pi pi-save", color: "#64748b"};
      return {icon: "pi pi-history", color: "#64748b"};
    },
    formatTime(datetime: string): string {
      const date = new Date(datetime);
      const delta = Math.round((Date.now() - date.getTime()) / 1000);
      const minute = 60;
      const hour = minute * 60;

      if (delta < 30) return "только что";
      if (delta < minute) return `${delta} сек. назад`;
      if (delta < 2 * minute) return "минуту назад";
      if (delta < hour) return `${Math.floor(delta / minute)} мин. назад`;

      return date.toLocaleString("ru", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    }
  }
});
</script>
