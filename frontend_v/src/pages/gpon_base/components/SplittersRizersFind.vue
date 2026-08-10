<template>
    <div class="px-2 flex items-center gap-2 pb-2">
        Выберите существующий {{ verboseType }}
        <Asterisk />
    </div>

    <Select
        v-if="!error.status && availableList !== null"
        v-model="connection"
        :options="availableList"
        filter
        showClear
        :loading="isLoading"
        fluid
        :class="valid ? ['w-full'] : ['p-invalid', 'w-full']"
        class="rounded-2xl"
        @filter="onFilter"
        :virtualScrollerOptions="virtualScrollerOptions"
        @change="(e) => $emit('change', e)"
        :optionLabel="getFullAddress"
        placeholder="Выберите"
    >
        <template #value="slotProps">
            <div v-if="slotProps.value" class="flex items-center text-wrap">
                <div>{{ getFullAddress(slotProps.value) }}</div>
            </div>
            <span v-else>
                {{ slotProps.placeholder }}
            </span>
        </template>
        <template #option="slotProps">
            <div v-if="slotProps.option" class="items-center flex text-wrap">
                <div>{{ getFullAddress(slotProps.option) }}</div>
            </div>
        </template>
    </Select>

    <Message v-else severity="error"> Ошибка {{ error.message }}. Код ошибки {{ error.status }} </Message>
</template>

<script lang="ts">
import Asterisk from "./Asterisk.vue";

import errorFmt, { getErrorStatus } from "@/errorFmt";
import { getEnd3Addresses } from "@/services/gpon";
import type { PropType } from "vue";
import type { End3WithCapability, GponFilterEvent, GponLazyLoadEvent } from "@/types/gpon";
import { formatAddress } from "@/formats";

export default {
    name: "SplittersRizersFind",
    emits: ["change"],
    components: {
        Asterisk,
    },
    props: {
        init: { required: false, type: Object as PropType<End3WithCapability | null>, default: null },
        type: { required: false, type: String as PropType<"both" | "splitter" | "rizer">, default: "both" },
        fromAddressID: { required: false, type: Number, default: null },
        valid: { required: false, type: Boolean, default: true },
    },
    data() {
        return {
            connection: null as End3WithCapability | null,
            availableList: [] as End3WithCapability[],
            searchQuery: "",
            isLoading: false,
            hasNextPage: true,
            nextPage: 1,
            debounceTimer: null as ReturnType<typeof setTimeout> | null,
            pageSize: 20,
            error: {
                status: null as number | string | null,
                message: null as string | null,
            },
        };
    },
    mounted() {
        this.loadConnections({ reset: true });
        this.connection = this.init;
    },

    computed: {
        verboseType() {
            if (this.type === "both") return "сплиттер или райзер";
            if (this.type === "splitter") return "сплиттер";
            if (this.type === "rizer") return "райзер";
            return "объект";
        },
        virtualScrollerOptions() {
            return {
                itemSize: 38,
                lazy: true,
                onLazyLoad: this.onLazyLoad,
                showLoader: true,
                loading: this.isLoading,
            };
        },
    },
    methods: {
        /** Loads a page of splitters and risers for the selector. */
        async loadConnections({ reset = false }: { reset?: boolean } = {}): Promise<void> {
            if (this.isLoading || (!reset && !this.hasNextPage)) return;

            if (reset) {
                this.availableList = [];
                this.nextPage = 1;
                this.hasNextPage = true;
            }

            this.isLoading = true;
            try {
                const page = await getEnd3Addresses({
                    page: this.nextPage,
                    page_size: this.pageSize,
                    search: this.searchQuery || undefined,
                    address_id: this.fromAddressID ?? undefined,
                });
                this.availableList = [...this.availableList, ...page.results];
                this.hasNextPage = Boolean(page.next);
                this.nextPage += 1;
            } catch (reason) {
                this.error.status = getErrorStatus(reason) ?? null;
                this.error.message = errorFmt(reason);
            } finally {
                this.isLoading = false;
            }
        },
        /** Restarts loading after the search filter changes. */
        onFilter(event: GponFilterEvent): void {
            this.searchQuery = (event.value || "").trim();
            if (this.debounceTimer) clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.loadConnections({ reset: true });
            }, 250);
        },
        /** Loads the next page near the end of the virtual list. */
        onLazyLoad(event?: GponLazyLoadEvent): void {
            if (!event) return;
            const remaining = this.availableList.length - event.last;
            if (remaining <= 5) {
                this.loadConnections();
            }
        },
        /** Formats an endpoint for display in the selector. */
        getFullAddress(sr: End3WithCapability): string {
            if (!sr.address) return "НЕТ АДРЕСА";
            let address = formatAddress(sr.address);
            address += ` Локация: ${sr.location}. Кол-во портов: ${sr.capacity}`;
            return address;
        },
    },
};
</script>

<style scoped></style>
