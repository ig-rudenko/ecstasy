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

<script>
import Asterisk from "./Asterisk.vue";

import api from "@/services/api";
import { formatAddress } from "@/formats";

export default {
    name: "SplittersRizersFind",
    components: {
        Asterisk,
    },
    props: {
        init: { required: false, default: null },
        type: { required: false, type: String, default: "both" },
        fromAddressID: { required: false, default: null },
        valid: { required: false, type: Boolean, default: true },
    },
    data() {
        return {
            connection: null,
            availableList: null,
            searchQuery: "",
            isLoading: false,
            hasNextPage: true,
            nextPage: 1,
            debounceTimer: null,
            pageSize: 20,
            error: {
                status: null,
                message: null,
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
        loadConnections({ reset = false } = {}) {
            if (this.isLoading) return;
            if (!reset && !this.hasNextPage) return;

            if (reset) {
                this.availableList = [];
                this.nextPage = 1;
                this.hasNextPage = true;
            }

            let url = "/api/v1/gpon/addresses/end3";
            if (this.fromAddressID) {
                url += "?address_id=" + this.fromAddressID;
            }

            this.isLoading = true;
            api.get(url, {
                params: {
                    page: this.nextPage,
                    page_size: this.pageSize,
                    search: this.searchQuery || undefined,
                },
            })
                .then((resp) => {
                    const results = Array.from(resp.data.results || []);
                    this.availableList = [...this.availableList, ...results];
                    this.hasNextPage = Boolean(resp.data.next);
                    this.nextPage += 1;
                })
                .catch((reason) => {
                    this.error.status = reason.response.status;
                    this.error.message = reason.response.data;
                })
                .finally(() => {
                    this.isLoading = false;
                });
        },
        onFilter(event) {
            this.searchQuery = (event.value || "").trim();
            if (this.debounceTimer) clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.loadConnections({ reset: true });
            }, 250);
        },
        onLazyLoad(event) {
            if (!event) return;
            const remaining = this.availableList.length - event.last;
            if (remaining <= 5) {
                this.loadConnections();
            }
        },
        getFullAddress(sr) {
            if (!sr.address) return "НЕТ АДРЕСА";
            let address = formatAddress(sr.address);
            address += ` Локация: ${sr.location}. Кол-во портов: ${sr.capacity}`;
            return address;
        },
    },
};
</script>

<style scoped></style>
