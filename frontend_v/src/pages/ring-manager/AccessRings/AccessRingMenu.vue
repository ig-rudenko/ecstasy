<template>
    <div class="flex flex-col gap-5">
        <div class="not-sm:px-4 flex flex-wrap items-center justify-between gap-3">
            <div v-if="rings.selectedRing" class="flex items-center gap-1 sm:gap-3">
                <Button text rounded icon="pi pi-arrow-left" @click="backToAllRings" />
                <div>
                    <div class="text-sm sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {{ rings.selectedRing.head_name }}
                    </div>
                    <div class="font-mono text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                        {{ rings.selectedRing.ports }}
                    </div>
                </div>
            </div>

            <Button
                v-if="points.length"
                outlined
                severity="secondary"
                icon="pi pi-refresh"
                label="Обновить"
                class="rounded-2xl text-xs sm:text-base"
                @click="reloadRing"
            />
        </div>

        <div
            v-if="points.length"
            class="sm:rounded-3xl sm:border border-gray-200/70 dark:border-gray-700/70 bg-white/50 dark:bg-gray-950/20 p-4 sm:p-6"
        >
            <RingView :points="points" :ports-color-always="true" :copy-head-to-tail="true" />
        </div>

        <div
            v-else
            class="sm:rounded-3xl sm:border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 px-6 py-12 text-center backdrop-blur"
        >
            <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Опрашиваем интерфейсы, пожалуйста, подождите
            </div>
            <div class="mt-5">
                <ProgressSpinner />
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";

import RingView from "../TransportRingRotate/RingView.vue";
import api from "@/services/api";

export default defineComponent({
    name: "RingMenu",
    components: { RingView },
    props: {
        rings: {
            required: true,
            type: Object as PropType<{
                list: any[];
                selectedRing: { head_name: String; ports: String; description: String } | null;
            }>,
        },
    },
    data() {
        return {
            points: [],
            errors: [] as { text: any; time: string }[],
            infos: [],
        };
    },
    async mounted() {
        await this.getRing(false);
        await this.getRing(true);
    },

    computed: {
        reversedErrors() {
            return this.reverseArray(this.errors);
        },
        reversedInfos() {
            return this.reverseArray(this.infos);
        },
    },

    methods: {
        reverseArray(array: any[]) {
            let reversed = [];
            for (let i = array.length - 1; i >= 0; i--) {
                reversed.push(array[i]);
            }
            return reversed;
        },

        getTime(): string {
            let date = new Date();
            let padZero = (n: number) => (n < 10 ? "0" + n : n);
            return padZero(date.getHours()) + ":" + padZero(date.getMinutes()) + ":" + padZero(date.getSeconds());
        },

        formatDateToTime(date: Date) {
            let padZero = (n: number) => (n < 10 ? "0" + n : n);
            return padZero(date.getHours()) + ":" + padZero(date.getMinutes()) + ":" + padZero(date.getSeconds());
        },

        async getRing(currentStatus: boolean) {
            if (!this.rings.selectedRing) return;
            try {
                const url =
                    "/api/v1/ring-manager/access-ring/" +
                    this.rings.selectedRing.head_name +
                    "?ports=" +
                    this.rings.selectedRing.ports +
                    "&current_status=" +
                    currentStatus;
                let resp = await api.get(url);
                this.points = await resp.data.points;
            } catch (e) {
                console.log(e);
                this.errors.push({
                    text: e,
                    time: this.getTime(),
                });
            }
        },

        async reloadRing() {
            this.points = [];
            await this.getRing(false);
            await this.getRing(true);
        },

        backToAllRings() {
            this.rings.selectedRing = null;
        },
    },
});
</script>
