<script setup lang="ts">
import {computed, ref} from "vue";
import pinnedDevices from "@/services/pinnedDevices.ts";

const popoverRef = ref();
const count = computed(() => pinnedDevices.pinnedDevices.value.length);
const visible = computed(() => count.value > 0);

function toggle(event: Event) {
  popoverRef.value?.toggle(event);
}
</script>

<template>
  <div v-if="visible" class="inline-flex">
    <Button
        type="button"
        icon="pi pi-bookmark-fill"
        :label="'Избранное (' + count + ')'"
        text
        :severity="count>0?'success':'secondary'"
        class="rounded-2xl! "
        @click="toggle"/>

    <Popover
        ref="popoverRef"
        :pt="{
          root: {
            class: 'before:!hidden overflow-hidden rounded-2xl border border-gray-200/80 ' +
                'dark:border-gray-700/60 bg-white/95 shadow-lg dark:bg-gray-900/70 dark:backdrop-blur-xl dark:!ring-1 dark:!ring-white/5',
          },
          content: { class: '!p-0' },
        }">
      <div class="p-4">
        <div
            class="pb-3 mb-3 flex w-full justify-between items-start gap-3 border-b border-gray-200/80 dark:border-gray-700/70">
          <div>
            <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Ваши избранные устройства</div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Быстрый доступ с списка оборудования</div>
          </div>
          <Button
              v-if="count > 0"
              outlined
              icon="pi pi-trash"
              size="small"
              v-tooltip.bottom="'Очистить избранное'"
              severity="danger"
              class="shrink-0"
              @click="pinnedDevices.clear()"/>
        </div>
        <div class="flex flex-col gap-2 max-h-[min(50vh,320px)] overflow-y-auto pr-1">
          <div
              v-for="dev in pinnedDevices.pinnedDevices.value"
              :key="dev.ip + dev.name"
              class="flex flex-row gap-2 items-center rounded-xl px-2 py-2 border border-gray-100 dark:border-gray-700/60 bg-gray-50/80 dark:bg-gray-800/40">
            <router-link
                :to="'/device/' + dev.name"
                class="text-sm font-mono flex-1 min-w-0 truncate text-indigo-600 dark:text-indigo-400 hover:underline"
                v-tooltip.bottom="dev.vendor + ' ' + dev.model">
              {{ dev.name }}
              <span class="text-gray-500 dark:text-gray-400 font-normal">({{ dev.ip }})</span>
            </router-link>
            <div class="flex items-center gap-1 shrink-0">
              <a
                  v-if="dev.console_url"
                  :href="dev.console_url"
                  class="group/console inline-flex text-indigo-600 dark:text-indigo-400 p-1 rounded-lg hover:bg-white/80 dark:hover:bg-gray-900/50"
                  target="_blank"
                  rel="noopener noreferrer"
                  v-tooltip.bottom="'Консоль'">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor"
                     class="inline group-hover/console:hidden" viewBox="0 0 16 16">
                  <path
                      d="M6 9a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3A.5.5 0 0 1 6 9M3.854 4.146a.5.5 0 1 0-.708.708L4.793 6.5 3.146 8.146a.5.5 0 1 0 .708.708l2-2a.5.5 0 0 0 0-.708z"/>
                  <path
                      d="M2 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2zm12 1a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z"/>
                </svg>
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor"
                     class="hidden group-hover/console:inline" viewBox="0 0 16 16">
                  <path
                      d="M0 3a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2zm9.5 5.5h-3a.5.5 0 0 0 0 1h3a.5.5 0 0 0 0-1m-6.354-.354a.5.5 0 1 0 .708.708l2-2a.5.5 0 0 0 0-.708l-2-2a.5.5 0 1 0-.708.708L4.793 6.5z"/>
                </svg>
              </a>
              <a
                  :href="'/device/' + dev.name"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex p-1 rounded-lg text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-white/80 dark:hover:bg-gray-900/50"
                  v-tooltip.bottom="'В новой вкладке'">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path fill-rule="evenodd"
                        d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5"/>
                  <path fill-rule="evenodd"
                        d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0z"/>
                </svg>
              </a>
              <button
                  type="button"
                  class="inline-flex p-1 rounded-lg text-gray-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-white/80 dark:hover:bg-gray-900/50 cursor-pointer"
                  v-tooltip.bottom="'Убрать из избранного'"
                  @click="pinnedDevices.removeDevice(dev)">
                <i class="pi pi-times text-sm"/>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Popover>
  </div>
</template>
