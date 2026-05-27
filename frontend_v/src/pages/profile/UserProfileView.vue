<script setup lang="ts">
import { computed, ref } from "vue";
import { useStore } from "vuex";

import { User } from "@/services/user";
import permissions from "@/services/permissions";
import decorConfig from "@/services/decor";

type ServiceAccess = {
    key: string;
    label: string;
    enabled: boolean;
};

const store = useStore();
const user = computed<User | null>(() => store.state.auth.user);
const serviceAccess = computed<ServiceAccess[]>(() => permissions.getServiceAccess());
const userPermissions = computed<string[]>(() => permissions.getAll());
const isWinterMonth = computed<boolean>(() => [0, 1, 11].includes(new Date().getMonth()));
const permissionSearch = ref<string>("");

const fullName = computed<string>(() => {
    if (!user.value) return "Неизвестный пользователь";
    const value = `${user.value.firstName || ""} ${user.value.lastName || ""}`.trim();
    return value || user.value.username;
});

const filteredPermissions = computed<string[]>(() => {
    const query = permissionSearch.value.trim().toLowerCase();
    if (!query) return userPermissions.value;
    return userPermissions.value.filter((permission) => permission.toLowerCase().includes(query));
});
</script>

<template>
    <main class="mx-auto max-w-320 px-3 py-6 sm:px-6 sm:py-8 lg:px-8">
        <section
            class="rounded-3xl border border-gray-200/80 bg-white/80 p-5 shadow-[0_20px_60px_-42px_rgba(15,23,42,0.45)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:p-7"
        >
            <div class="flex flex-wrap items-center gap-3 justify-between">
                <div>
                    <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">Профиль пользователя</h1>
                    <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">
                        Просмотр данных профиля и уровней доступа. Изменение доступно только через админ-панель.
                    </p>
                </div>
                <a v-if="user?.isStaff" href="/admin/">
                    <Button label="Админ-панель" icon="pi pi-cog" severity="secondary" outlined />
                </a>
            </div>

            <div class="mt-6 grid gap-4 lg:grid-cols-2">
                <div
                    class="rounded-2xl border border-gray-200/80 bg-white/75 p-4 dark:border-gray-700/70 dark:bg-gray-900/50"
                >
                    <h2 class="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                        Личная информация
                    </h2>
                    <div class="mt-3 grid gap-3">
                        <div>
                            <div class="text-xs text-slate-500 dark:text-slate-400">ФИО</div>
                            <div class="text-sm font-medium text-slate-900 dark:text-slate-100">{{ fullName }}</div>
                        </div>
                        <div>
                            <div class="text-xs text-slate-500 dark:text-slate-400">Логин</div>
                            <div class="text-sm font-medium text-slate-900 dark:text-slate-100">
                                {{ user?.username || "-" }}
                            </div>
                        </div>
                        <div>
                            <div class="text-xs text-slate-500 dark:text-slate-400">Email</div>
                            <div class="text-sm font-medium text-slate-900 dark:text-slate-100">
                                {{ user?.email || "-" }}
                            </div>
                        </div>
                    </div>
                </div>

                <div
                    class="rounded-2xl border border-gray-200/80 bg-white/75 p-4 dark:border-gray-700/70 dark:bg-gray-900/50"
                >
                    <h2 class="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                        Роли
                    </h2>
                    <div class="mt-3 flex gap-2 flex-wrap">
                        <Tag :severity="user?.isSuperuser ? 'danger' : 'secondary'" value="Superuser" />
                        <Tag :severity="user?.isStaff ? 'warn' : 'secondary'" value="Staff" />
                        <Tag severity="info" :value="`ID: ${user?.id || '-'}`" />
                    </div>
                </div>
            </div>

            <div
                class="mt-6 rounded-2xl border border-gray-200/80 bg-white/75 p-4 dark:border-gray-700/70 dark:bg-gray-900/50"
            >
                <h2 class="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                    Доступ к сервисам Ecstasy
                </h2>
                <div class="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                    <div
                        v-for="service in serviceAccess"
                        :key="service.key"
                        class="rounded-2xl border px-3 py-3"
                        :class="
                            service.enabled
                                ? 'border-emerald-200 bg-emerald-50/80 dark:border-emerald-700/50 dark:bg-emerald-900/20'
                                : 'border-gray-200 bg-gray-50/80 dark:border-gray-700 dark:bg-gray-800/50'
                        "
                    >
                        <div class="flex items-center justify-between gap-2">
                            <div class="text-sm font-medium text-slate-900 dark:text-slate-100">
                                {{ service.label }}
                            </div>
                            <Tag
                                :severity="service.enabled ? 'success' : 'contrast'"
                                :value="service.enabled ? 'Есть доступ' : 'Нет доступа'"
                            />
                        </div>
                    </div>
                </div>
            </div>

            <div
                class="mt-6 rounded-2xl border border-gray-200/80 bg-white/75 p-4 dark:border-gray-700/70 dark:bg-gray-900/50"
            >
                <h2 class="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                    Настройки интерфейса
                </h2>
                <div class="mt-3 grid gap-3">
                    <label
                        v-if="isWinterMonth"
                        class="flex items-center justify-between gap-3 rounded-2xl border border-gray-200/80 bg-white/70 px-3 py-3 dark:border-gray-700 dark:bg-gray-900/50"
                    >
                        <span class="text-sm font-medium text-slate-900 dark:text-slate-100">Зимний декор</span>
                        <ToggleSwitch v-model="decorConfig.winterDecor" />
                    </label>
                    <label
                        class="flex items-center justify-between gap-3 rounded-2xl border border-gray-200/80 bg-white/70 px-3 py-3 dark:border-gray-700 dark:bg-gray-900/50"
                    >
                        <span class="text-sm font-medium text-slate-900 dark:text-slate-100"
                            >Компактный режим меню</span
                        >
                        <ToggleSwitch v-model="decorConfig.compactMenu" />
                    </label>
                    <label
                        class="flex items-center justify-between gap-3 rounded-2xl border border-gray-200/80 bg-white/70 px-3 py-3 dark:border-gray-700 dark:bg-gray-900/50"
                    >
                        <span class="text-sm font-medium text-slate-900 dark:text-slate-100"
                            >Автораскрытие большой информации порта</span
                        >
                        <ToggleSwitch v-model="decorConfig.autoExpandLargeInterfaceInfo" />
                    </label>
                </div>
            </div>

            <div
                class="mt-6 rounded-2xl border border-gray-200/80 bg-white/75 p-4 dark:border-gray-700/70 dark:bg-gray-900/50"
            >
                <Fieldset legend="Полный список прав" :toggleable="true" :collapsed="true">
                    <div class="mb-3">
                        <IconField>
                            <InputIcon class="pi pi-search" />
                            <InputText
                                v-model="permissionSearch"
                                class="w-full"
                                placeholder="Поиск по правам доступа"
                                aria-label="Поиск по правам доступа"
                            />
                        </IconField>
                        <div class="mt-2 text-xs text-slate-500 dark:text-slate-400">
                            Найдено: {{ filteredPermissions.length }} из {{ userPermissions.length }}
                        </div>
                    </div>
                    <div v-if="filteredPermissions.length" class="max-h-80 overflow-auto pr-1">
                        <div class="flex flex-wrap gap-2">
                            <Tag
                                v-for="permission in filteredPermissions"
                                :key="permission"
                                severity="contrast"
                                :value="permission"
                            />
                        </div>
                    </div>
                    <Message v-else severity="secondary" size="small"> Ничего не найдено по текущему запросу. </Message>
                </Fieldset>
            </div>
        </section>
    </main>
</template>
