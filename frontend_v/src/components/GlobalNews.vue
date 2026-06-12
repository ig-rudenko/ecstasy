<script setup lang="ts">
import { onMounted, ref } from "vue";

import { getGlobalNews, GlobalNews, GlobalNewsSeverity } from "@/services/news";

type MessageSeverity = "success" | "info" | "warn" | "error" | "secondary" | "contrast";

const news = ref<GlobalNews[]>([]);
const loading = ref(true);
const loadError = ref(false);

const severityMap: Record<GlobalNewsSeverity, MessageSeverity> = {
    primary: "info",
    secondary: "secondary",
    success: "success",
    warning: "warn",
    danger: "error",
    info: "info",
    light: "secondary",
    dark: "contrast",
};

async function loadNews(): Promise<void> {
    loading.value = true;
    loadError.value = false;

    try {
        news.value = await getGlobalNews();
    } catch {
        loadError.value = true;
    } finally {
        loading.value = false;
    }
}

onMounted(loadNews);
</script>

<template>
    <section
        v-if="loading || loadError || news.length"
        class="mx-auto max-w-375 px-2 sm:px-4 lg:px-8"
        aria-label="Объявления"
        :aria-busy="loading"
    >
        <div
            v-if="loading"
            class="h-18 animate-pulse rounded-3xl border border-gray-200/70 bg-white/55 dark:border-gray-700/70 dark:bg-gray-900/35"
            aria-label="Загрузка объявлений"
        />

        <Message v-else-if="loadError" severity="error" class="rounded-3xl">
            <div class="flex flex-wrap items-center justify-between px-6 gap-3">
                <span>Не удалось загрузить объявления.</span>
                <Button
                    label="Повторить"
                    icon="pi pi-refresh"
                    size="small"
                    text
                    rounded
                    severity="danger"
                    @click="loadNews"
                />
            </div>
        </Message>

        <div v-else class="grid gap-2">
            <Message
                v-for="item in news"
                :key="item.id"
                :severity="severityMap[item.severity]"
                :closable="false"
                class="delay-0 transition hover:-translate-y-0.5 relative overflow-hidden rounded-2xl border backdrop-blur hover:shadow-md"
            >
                <template #container>
                    <div class="py-1 px-6">
                        <div class="flex flex-wrap items-center gap-x-4 gap-y-1">
                            <div class="text-base font-semibold">{{ item.title }}</div>
                            <div class="whitespace-pre-line text-sm">{{ item.content }}</div>
                        </div>
                    </div>
                </template>
            </Message>
        </div>
    </section>
</template>
