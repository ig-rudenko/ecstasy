<template>
  <section
      id="port-info"
      class="flex flex-wrap gap-5 rounded-[1.75rem] border border-gray-200/80 bg-white/80 p-4 dark:border-gray-700/80 dark:bg-gray-900/55">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="min-w-0">
        <div class="flex flex-wrap items-center gap-3">
          <div
              class="inline-flex items-center gap-2 rounded-full border border-indigo-200/80 bg-indigo-50 px-3 py-1.5 text-sm text-indigo-900 dark:border-indigo-900/70 dark:bg-indigo-500/15 dark:text-indigo-100">
            <span class="inline-flex h-2.5 w-2.5 rounded-full bg-indigo-500"></span>
            xDSL profile
          </div>
          <div class="font-mono text-base font-semibold text-gray-900 dark:text-gray-100">
            {{ data.profile_name }}
          </div>
          <Button
              @click="dialogVisible = true"
              text
              severity="info"
              size="small"
              class="rounded-2xl!"
              v-tooltip.bottom="'Изменить профиль'">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor"
                 class="text-sky-500 dark:text-sky-300" viewBox="0 0 16 16">
              <path
                  d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"></path>
            </svg>
          </Button>
        </div>

        <div class="mt-4 border-2xl p-3">
          <p v-for="line in data.first_col" class="font-mono whitespace-pre-line">{{ line }}</p>
        </div>
      </div>
    </div>

    <div
        v-if="data.streams.length"
        class="overflow-hidden rounded-3xl border border-gray-200/80 bg-white/70 dark:border-gray-700/80 dark:bg-gray-950/25">
      <div class="border-b border-gray-200/80 bg-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:bg-gray-900/70">
        <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Параметры линии</div>
        <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">Сравнение downstream и upstream по ключевым
          метрикам.
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full">
          <thead>
          <tr class="bg-gray-50/70 dark:bg-gray-900/70">
            <th class="px-4 py-1 text-left text-[11px] font-semibold uppercase tracking-[0.22em] text-gray-500 dark:text-gray-400"></th>
            <th class="px-4 py-1 text-center text-[11px] font-semibold uppercase tracking-[0.22em] text-gray-500 dark:text-gray-400">
              Downstream
            </th>
            <th class="px-4 py-1 text-center text-[11px] font-semibold uppercase tracking-[0.22em] text-gray-500 dark:text-gray-400">
              Upstream
            </th>
          </tr>
          </thead>
          <tbody class="divide-y divide-gray-200/70 dark:divide-gray-700/80">
          <tr v-for="line in data.streams" :key="line.name">
            <td class="px-4 py-3 text-right text-sm font-medium text-gray-600 dark:text-gray-300">
              {{ line.name }}
            </td>
            <td class="px-4 py-1">
              <div
                  :style="streamCellStyle(line.down.color)"
                  class="rounded-2xl px-3 py-2 text-center font-mono text-sm text-gray-950 shadow-sm dark:opacity-85">
                {{ line.down.value }}
              </div>
            </td>
            <td class="px-4 py-1">
              <div
                  :style="streamCellStyle(line.up.color)"
                  class="rounded-2xl px-3 py-2 text-center font-mono text-sm text-gray-950 shadow-sm dark:opacity-85">
                {{ line.up.value }}
              </div>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <Dialog
      modal
      v-model:visible="dialogVisible"
      header="Выберите новый профиль для порта"
      class="w-[min(96vw,880px)]"
      content-class="!p-0">
    <div class="flex flex-col gap-5 bg-gray-50/60 p-4 dark:bg-gray-950/30 sm:p-6">
      <section
          class="rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Доступные профили</div>
            <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Выберите профиль, который нужно применить к порту {{ interface.name }}.
            </div>
          </div>
          <div
              class="inline-flex w-fit items-center gap-2 rounded-full border border-sky-200/80 bg-sky-50 px-3 py-1.5 text-sm text-sky-900 dark:border-sky-900/70 dark:bg-sky-500/10 dark:text-sky-200">
            <span class="inline-flex h-2.5 w-2.5 rounded-full bg-sky-500"></span>
            Текущий: {{ data.profile_name }}
          </div>
        </div>
      </section>

      <section
          class="rounded-3xl border border-gray-200/80 bg-white/85 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55">
        <div class="overflow-hidden rounded-3xl">
          <div
              class="hidden bg-gray-50/80 px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.22em] text-gray-500 dark:bg-gray-900/80 dark:text-gray-400 md:grid md:grid-cols-12 md:gap-4">
            <div class="md:col-span-2">Index</div>
            <div class="md:col-span-10">Profile name</div>
          </div>

          <div class="divide-y divide-gray-200/80 dark:divide-gray-700/80">
            <button
                v-for="profile in data.profiles"
                :key="profile[0]"
                type="button"
                class="
                    grid w-full gap-1 md:grid md:grid-cols-12 md:items-center md:gap-4
                    px-4 py-4
                    text-left transition cursor-pointer
                    hover:bg-gray-500/10 dark:hover:bg-gray-800/60
                "
                @click="changePortProfile(profile[0], profile[1])">
              <span class="font-mono text-sm text-gray-500 dark:text-gray-400 md:col-span-2">{{ profile[0] }}</span>
              <span class="font-medium text-gray-900 dark:text-gray-100 md:col-span-10">{{ profile[1] }}</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  </Dialog>
</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";
import api from "@/services/api";
import {DeviceInterface} from "@/services/interfaces";
import {errorToast, successToast} from "@/services/my.toast.ts";
import errorFmt from "@/errorFmt.ts";

type xDLSData = {
  profile_name: string,
  first_col: string[],
  streams: [
    {
      name: string,
      down: { color: string, value: string },
      up: { color: string, value: string }
    }
  ],
  profiles: Array<[string, string]>
}

export default defineComponent({
  props: {
    deviceName: {required: true, type: String},
    data: {required: true, type: Object as PropType<xDLSData>},
    interface: {required: true, type: Object as PropType<DeviceInterface>}
  },
  data() {
    return {
      dialogVisible: false,
    }
  },

  methods: {
    streamCellStyle(color: string): Record<string, string> {
      return {"background-color": color}
    },

    async changePortProfile(profile_index: string, profile_name: string) {
      this.dialogVisible = false

      const data = {
        port: this.interface.name,
        index: profile_index
      }

      try {
        await api.post("/api/v1/devices/" + this.deviceName + "/change-dsl-profile", data)
        successToast("OK", "Профиль был изменен на " + profile_name)
      } catch (error: any) {
        errorToast("Ошибка при изменении профиля", errorFmt(error))
      }
    }
  }
})
</script>
