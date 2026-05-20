<template>
    <Dialog
        :visible="visible"
        modal
        dismissable-mask
        :draggable="false"
        :base-z-index="11050"
        :style="{ width: 'min(92vw, 38rem)' }"
        header="Информация об узле"
        @update:visible="$emit('update:visible', $event)"
        @hide="$emit('hide')"
    >
        <div v-if="node" class="space-y-4">
            <div class="space-y-1">
                <div class="break-all text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {{ nodeLabel }}
                </div>
                <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Идентификатор узла</div>
                <div class="break-all font-mono text-sm text-gray-700 dark:text-gray-200">
                    {{ nodeId }}
                </div>
            </div>

            <div
                v-if="titleHtml"
                class="traceroute-node-popup rounded-2xl border border-gray-200/80 bg-gray-50 p-4 text-sm text-gray-800 dark:border-gray-700/60 dark:bg-gray-900/60 dark:text-gray-100"
                v-html="titleHtml"
            />

            <div class="flex flex-wrap gap-3">
                <a
                    v-if="deviceRouteAvailable"
                    :href="deviceHref"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center justify-center rounded-2xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white no-underline transition hover:bg-indigo-500"
                >
                    Перейти к оборудованию
                </a>
                <span
                    v-else
                    class="inline-flex items-center rounded-2xl border border-gray-200 px-4 py-2 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400"
                >
                    Для этого узла переход недоступен
                </span>
            </div>
        </div>
    </Dialog>
</template>

<script setup lang="ts">
import type { TracerouteNodeData } from "../net";

defineProps<{
    visible: boolean;
    node: TracerouteNodeData | null;
    nodeId: string;
    nodeLabel: string;
    titleHtml: string;
    deviceRouteAvailable: boolean;
    deviceHref: string;
}>();

defineEmits<{
    "update:visible": [value: boolean];
    hide: [];
}>();
</script>

<style scoped>
.traceroute-node-popup:deep(br) {
    display: block;
    content: "";
    margin-top: 0.35rem;
}

.traceroute-node-popup:deep(div) {
    word-break: break-word;
}

.traceroute-node-popup:deep(span) {
    word-break: break-word;
}
</style>
