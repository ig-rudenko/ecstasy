<script setup lang="ts">

</script>

<template>
  <div class="container mx-auto dark:text-gray-300 relative mt-16">
    <footer class="sticky bottom-0 p-5">

      <hr class="dark:border-gray-700 border-gray-400 py-3">

      <div class="sm:grid grid-cols-2 md:grid-cols-3">
        <div class="py-2 flex flex-col gap-2">
          <div class="text-xl font-semibold">Навигация</div>
          <div><a class="link-secondary text-decoration-none" href="/admin/">Панель администратора</a></div>
          <div><a class="link-secondary text-decoration-none" href="/">Главная</a></div>
        </div>

        <div class="py-2 flex flex-col gap-2">
          <div class="text-xl font-semibold">Документация</div>
          <div><a class="link-secondary text-decoration-none" target="_blank" href="/api/swagger/">API</a></div>
        </div>

        <div class="py-2 flex flex-col gap-2">
          <div class="text-xl font-semibold">О программе</div>
          <span class="text-muted">
              Ecstasy - Equipment Control System To Assist You - программа для управления сетевым оборудованием
          </span>
        </div>

      </div>

      <div class="flex gap-4 justify-between">

        <div class="flex items-center text-muted-color">
          <img class="me-3 w-[70px] h-[70px] rounded-full" src="/video/logo.webp">
          <span class="nowrap">© 2022-{{ new Date().getFullYear() }} Ecstasy</span>
        </div>

        <div class="py-4 col justify-content-end list-unstyled d-flex">
          <a class="text-dark" href="https://github.com/ig-rudenko/ecstasy" target="_blank" title="GitHub">
            <i class="pi pi-github text-[60px]"/>
          </a>
        </div>

      </div>
    </footer>
  </div>

</template>

<style scoped>

</style>