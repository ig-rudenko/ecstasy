<script setup lang="ts">

</script>

<template>
  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pb-4">
    <footer class="rounded-3xl border border-gray-200/70 dark:border-gray-700/70 bg-white/70 dark:bg-gray-900/40 backdrop-blur p-6 sm:p-8">
      <div class="grid gap-8 md:grid-cols-3">
        <div class="flex flex-col gap-3">
          <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Навигация</div>
          <div class="flex flex-col gap-2 text-sm">
            <a class="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100" href="/admin/">
              Панель администратора
            </a>
            <a class="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100" href="/">
              Главная
            </a>
          </div>
        </div>

        <div class="flex flex-col gap-3">
          <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Документация</div>
          <div class="flex flex-col gap-2 text-sm">
            <a class="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100" target="_blank"
               href="/api/swagger/">
              API (Swagger)
            </a>
          </div>
        </div>

        <div class="flex flex-col gap-3">
          <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">О программе</div>
          <div class="text-sm text-gray-600 dark:text-gray-300">
            Ecstasy — Equipment Control System To Assist You — программа для управления сетевым оборудованием.
          </div>
        </div>
      </div>

      <div class="my-8 h-px bg-gray-200/70 dark:bg-gray-700/70"/>

      <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div class="flex items-center gap-3 text-gray-600 dark:text-gray-300">
          <img class="w-12 h-12 rounded-full" src="/video/logo.webp" alt="logo">
          <span class="whitespace-nowrap">© 2022-{{ new Date().getFullYear() }} Ecstasy</span>
        </div>

        <a class="inline-flex items-center gap-2 text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100"
           href="https://github.com/ig-rudenko/ecstasy" target="_blank" title="GitHub">
          <i class="pi pi-github text-3xl"/>
          <span class="text-sm font-medium">GitHub</span>
        </a>
      </div>
    </footer>
  </div>

</template>
