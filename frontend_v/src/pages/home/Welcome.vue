<script setup lang="ts">
import {useStore} from "vuex";

import {User} from "@/services/user";
import permissions from "@/services/permissions.ts";
import {computed, ref} from "vue";

const store = useStore();
const user: User | null = store.state.auth.user;

const showGPONCard = computed(() => permissions.hasGPONAnyPermission());
const showMapsCard = computed(() => permissions.has("auth.can_view_maps"));
const showTracerouteCard = computed(() => permissions.has("auth.access_traceroute"));
const showDescSearchCard = computed(() => permissions.has("auth.access_desc_search"));
const showWTFCard = computed(() => permissions.has("auth.access_wtf_search"));

const alphabet = 'abcdef1234567890';

const randomMAC = ref("");
const randomIP = ref("");

function macGenerator() {
  let random_mac = '';
  for (let i = 0; i < 17; i++) {
    if (i % 3 === 2) {
      random_mac += ':'
    } else {
      random_mac += alphabet[Math.round(Math.random() * (alphabet.length - 1))];
    }
  }
  randomMAC.value = random_mac
}

function ipGenerator() {
  let random_ip = [];
  for (let i = 0; i < 4; i++) {
    random_ip.push(Math.round(Math.random() * (255 - 1) + 1));
  }
  randomIP.value = random_ip.join('.');
}

function timer() {
  macGenerator();
  ipGenerator();
  setTimeout(timer, 300);
}

setTimeout(timer, 300);

</script>

<template>

  <main class="container mx-auto p-5">
    <div class="flex flex-col gap-4">

      <div class="p-3 bg-gray-100 dark:bg-gray-800 rounded-3xl shadow">
        <div class="p-3">
          <div class="flex align-items">
            <div class="text-2xl font-bold me-2 text-gray-900 dark:text-gray-200">Добро пожаловать,
              {{ user?.firstName || user?.username }}
            </div>
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="#ffa22b" viewBox="0 0 16 16">
              <path
                  d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16M7 6.5C7 7.328 6.552 8 6 8s-1-.672-1-1.5S5.448 5 6 5s1 .672 1 1.5M4.285 9.567a.5.5 0 0 1 .683.183A3.5 3.5 0 0 0 8 11.5a3.5 3.5 0 0 0 3.032-1.75.5.5 0 1 1 .866.5A4.5 4.5 0 0 1 8 12.5a4.5 4.5 0 0 1-3.898-2.25.5.5 0 0 1 .183-.683M10 8c-.552 0-1-.672-1-1.5S9.448 5 10 5s1 .672 1 1.5S10.552 8 10 8"></path>
            </svg>
          </div>
        </div>
      </div>

      <router-link :to="{name: 'gpon'}" v-if="showGPONCard">
        <div class="rounded-3xl shadow w-full text-gray-100"
             style="background-image: url('/img/gpon/sphere-global.jpeg'); background-position: left; background-size: cover">
          <div class="p-10">
            <div class="text-2xl font-bold">База GPON</div>
            <div class="flex flex-col gap-3 py-3">
              <div class="flex gap-2 items-center">
                <svg class="bi me-2" width="16" height="16" role="img">
                  <use xlink:href="#list-icon"></use>
                </svg>
                <div>Отображение технических данных GPON</div>
              </div>
              <div class="flex gap-2 items-center">
                <svg class="bi me-2" width="16" height="16" role="img">
                  <use xlink:href="#splitter"></use>
                </svg>
                <div>Просмотр задействованных OLT портов</div>
              </div>
              <div class="flex gap-2 items-center">
                <svg class="bi me-2" width="16" height="16" role="img">
                  <use xlink:href="#building"></use>
                </svg>
                <div>Подключение строений к сети GPON</div>
              </div>
              <div class="flex gap-2 items-center">
                <svg class="bi me-2" width="16" height="16" role="img">
                  <use xlink:href="#people"></use>
                </svg>
                <div>Управление абонентами GPON</div>
              </div>
              <div class="flex gap-2 items-center">
                <svg class="bi me-2" width="16" height="16" role="img">
                  <use xlink:href="#node-plus"></use>
                </svg>
                <div>Создание и просмотр подключений абонентов</div>
              </div>
            </div>
          </div>
        </div>
      </router-link>

      <router-link :to="{name: 'devices-list'}"
                   class="rounded-3xl px-5 sm:px-10 py-5 border shadow flex flex-col md:flex-row justify-between gap-4">
        <div class="">
          <div class="text-2xl py-5 font-bold">Управление оборудованием</div>

          <div class="flex flex-col gap-3">
            <div class="flex gap-2 items-center">
              <div>
                <svg width="16" height="16" role="img">
                  <use xlink:href="#list-icon"></use>
                </svg>
              </div>
              <div>Отображение интерфейсов оборудования в реальном времени</div>
            </div>
            <div class="flex gap-2 items-center">
              <div>
                <svg width="16" height="16" role="img">
                  <use xlink:href="#up-down-icon"></use>
                </svg>
              </div>
              <div>Управление состоянием порта</div>
            </div>

            <div class="flex gap-2 items-center">
              <div>
                <svg width="16" height="16" role="img">
                  <use xlink:href="#bar-icon"></use>
                </svg>
              </div>
              <div>Просмотр MAC адресов на порту</div>
            </div>

            <div class="flex gap-2 items-center">
              <div>
                <svg width="16" height="16" role="img">
                  <use xlink:href="#gear-icon"></use>
                </svg>
              </div>
              <div>Просмотр текущей конфигурации порта</div>
            </div>

            <div class="flex gap-2 items-center">
              <div>
                <svg width="16" height="16" role="img">
                  <use xlink:href="#journals-icon"></use>
                </svg>
              </div>
              <div>Перенаправление для просмотра логов в Elastic Stack</div>
            </div>

            <div class="flex gap-2 utems-center">
              <div>
                <svg width="16" height="16" role="img">
                  <use xlink:href="#warning-icon"></use>
                </svg>
              </div>
              <div>Просмотр ошибок на порту</div>
            </div>

            <div class="flex gap-2 items-center">
              <div>
                <svg width="16" height="16" role="img">
                  <use xlink:href="#radios-grid-icon"></use>
                </svg>
              </div>
              <div>Возможность просматривать и сбрасывать текущую сессию по MAC адресу</div>
            </div>

          </div>
        </div>

        <div class="flex justify-center">
          <img class="h-[200px] sm:h-[350px]" src="/img/dev-box.svg" alt="device">
        </div>
      </router-link>

      <a v-if="showMapsCard" href="#" class="p-4 rounded-3xl shadow"
         style="background-image: url('/img/maps/background.png'); background-position: center center; height: 200px">
        <div class="text-2xl text-gray-900 font-bold">Интерактивные карты</div>
      </a>

      <div class="md:grid md:grid-cols-2 xl:grid-cols-3 gap-4">

        <router-link v-if="showTracerouteCard" :to="{name: 'tools-traceroute'}" class="">
          <div class="text-center h-full p-4 py-8 rounded-3xl text-gray-200 shadow"
               style="
             background-image: url('/img/background.png');
             background-position: center center;
             background-size: cover;
            ">
            <div class="text-2xl font-bold">Traceroute</div>
            <div class="py-5">
              <svg class="bi me-2 fill-orange-400" width="100%" height="200px">
                <use xlink:href="#vlan-icon"></use>
              </svg>
            </div>

            <div class="">Отображение топологии конкретного VLAN, а также прохождение MAC адреса</div>
          </div>
        </router-link>

        <router-link :to="{name: 'tools-search'}" v-if="showDescSearchCard">
          <div class="text-center h-full p-4 py-8 border rounded-3xl shadow">
            <div class="text-2xl font-bold">Description search</div>
            <div class="py-5">
              <img class="h-[12rem] mx-auto" src="/img/home-search-description.svg">
            </div>
            <p>
              Поиск конкретной строки в описании порта и его комментариев на всех собранных заранее
              интерфейсах у каждого оборудования
            </p>
          </div>
        </router-link>

        <router-link to="/" v-if="showWTFCard">
          <div class="text-center h-full p-4 py-8 border rounded-3xl shadow bg-gray-800 text-gray-200">
            <div class="text-2xl font-bold">WTF search</div>

            <div class="py-20 font-mono text-3xl">
              <div>{{ randomIP }}</div>
              <div>{{ randomMAC }}</div>
            </div>

            <p>Осуществляет поиск по IP/MAC адресам в таблицах arp. Также отображает соответствие с базой Zabbix</p>

          </div>
        </router-link>
      </div>

    </div>

  </main>

  <svg xmlns="http://www.w3.org/2000/svg" style="display: none;">
    <symbol id="vlan-icon">
      <svg viewBox="200 200 350 350" xmlns="http://www.w3.org/2000/svg">
        <path
            d="m565.43 437.57c-1.4219 0-2.8398 0-3.7891 0.47266l-63.461-126.45c3.3164-2.3672 5.6836-6.6289 5.6836-11.367 0-8.0508-6.1562-14.207-14.207-14.207-5.2109 0-9.4727 2.8398-12.312 6.6289l-163.39-65.352c0.47656-0.94531 0.47656-1.8945 0.47656-2.8398 0-8.0508-6.1562-14.207-14.207-14.207s-14.207 6.1562-14.207 14.207c0 1.8945 0.47266 4.2617 1.4219 5.6836l-90.457 60.145c-2.8438-2.3711-6.1562-4.2656-10.418-4.2656-8.0508 0-14.207 6.1562-14.207 14.207 0 8.0508 6.1562 14.207 14.207 14.207 1.4219 0 2.8398 0 4.2617-0.94531l49.727 99.453-43.57 28.887c-2.8438-2.3672-6.1562-4.2617-10.418-4.2617-8.0508 0-14.207 6.1562-14.207 14.207 0 8.0508 6.1562 14.207 14.207 14.207 7.1055 0 13.262-5.2109 14.207-11.84h60.145l30.781 62.039c-3.3125 2.3711-5.6836 6.6328-5.6836 11.367 0 8.0508 6.1562 14.207 14.207 14.207 8.0508 0 14.207-6.1562 14.207-14.207v-1.4219l91.875-26.047 32.676 21.785c-0.94531 1.4219-1.418 3.7891-1.418 5.6836 0 8.0508 6.1562 14.207 14.207 14.207 8.0508 0 14.207-6.1562 14.207-14.207s-6.1562-14.207-14.207-14.207l-4.2617-25.574 105.14-29.836c2.3672 4.7344 7.1055 8.0508 12.785 8.0508 8.0508 0 14.207-6.1562 14.207-14.207 0-8.0508-6.1562-14.207-14.207-14.207zm-364.66 11.84c-0.47266-1.4219-0.94531-2.3672-1.4219-3.7891l43.098-28.414 16.102 32.203zm97.082 63.934c-0.94531 0-1.4219 0.47266-1.8945 0.47266l-29.836-59.672h31.73zm0-63.934h-34.098l-17.523-34.57 51.621-34.57zm0-74.824-53.516 35.52-49.25-98.508c1.4219-0.94531 2.8398-2.3672 3.7891-4.2617l98.977 39.781zm0-32.68-97.559-38.832c0.47656-0.94922 0.47656-1.8945 0.47656-2.8438 0-1.8945-0.47266-3.7891-1.4219-5.6836l90.453-60.145c2.3672 2.3672 4.7344 3.7891 8.0508 4.2617zm14.684-109.87 163.39 65.355c-0.47656 0.94922-0.47656 1.8945-0.47656 2.8398 0 2.8398 0.94531 5.6836 2.8398 8.0508l-26.52 26.523-26.52-26.52c1.8945-2.3672 2.8398-5.2109 2.8398-8.0508 0-8.0508-6.1562-14.207-14.207-14.207s-14.207 6.1562-14.207 14.207c0 1.8945 0.47266 4.2617 1.4219 5.6836l-43.098 28.414-49.25-98.508c1.418-0.94531 2.8398-2.3672 3.7891-3.7891zm47.355 107.03 43.57-28.887c2.8398 2.3672 6.1562 4.2617 10.418 4.2617l8.0508 49.727-19.891 19.891-24.625-9.9453zm11.367 32.203-37.414-14.68 22.258-15.156zm27.469 16.574-9.4727 9.4727-8.5234-16.574zm4.7344 1.8945 24.152 9.9453 14.207 85.246-8.0508 2.3672-42.621-85.246zm3.7891-3.7891 16.102-15.629 3.7891 23.68zm18.469-26.047-7.5781-46.41c1.4219-0.47266 2.8398-0.94531 3.7891-1.8945l26.047 26.047zm-123.13-121.23c0.47266-0.47266 1.4219-0.47266 1.4219-0.47266l49.727 99.453-25.574 17.051-25.574-10.418zm0 110.34 20.836 8.5234-20.836 14.207zm-0.47656 28.887 26.52-17.523 45.465 17.996 11.367 22.73-39.309 39.309c-2.3672-1.8906-5.207-2.8398-8.0508-2.8398-7.1055 0-13.262 5.2109-14.207 11.84v0.47266h-21.785zm10.895 143.5c-1.8945-4.2617-5.6836-7.1055-10.418-8.0508v-59.199h21.309c1.4219 6.6289 7.1055 11.84 14.207 11.84 4.2617 0 7.5781-1.8945 10.418-4.7344l52.094 35.047zm37.887-63.934c0.94531-1.4219 1.4219-3.7891 1.4219-5.6836 0-2.8398-1.4219-5.6836-2.8398-8.0508l37.887-38.832 41.676 82.875-22.734 6.6328zm89.98 60.617-29.363-19.891 19.891-5.6836 11.84 23.68c-0.47266 0.47656-1.4219 0.94922-2.3672 1.8945zm-4.2617-26.992 6.6289-1.8945 3.7891 23.207zm114.61-39.309v1.4219l-104.19 30.309-13.734-81.93 118.39 47.359c-0.47266 0.94531-0.47266 1.8945-0.47266 2.8398zm2.3672-7.5781-121.23-48.305-5.2109-29.836 24.625-24.625 102.29 102.29c-0.47266 0-0.47266 0.47266-0.47266 0.47266zm-98.504-106.08 26.52-26.52c2.3672 1.8945 5.2109 2.8398 8.0508 2.8398 1.4219 0 2.8398 0 4.2617-0.47266l62.984 125.97z"/>
      </svg>
    </symbol>
    <symbol id="ecstasy">
      <svg xmlns="http://www.w3.org/2000/svg" version="1.1" id="Layer_1" x="0px" y="0px" viewBox="0 0 512 512"
           enable-background="new 0 0 512 512" xml:space="preserve">
    <g>
        <path fill="#2E628C"
              d="M232.9,217.3c114.1-71.7,230.4-96.2,274.6-60.9c-1.2-5.3-3.2-10.4-6.1-14.9c-32.4-51.6-160.2-29.7-285.4,49   C90.9,269.1,15.7,374.7,48.1,426.3c2.9,4.6,6.5,8.5,10.8,11.9C46.3,383.1,118.8,289,232.9,217.3z"/>
      <path fill="#2E628C"
            d="M320.2,212.7c71.7,114.1,96.2,230.4,60.9,274.6c5.3-1.2,10.3-3.2,14.9-6.1c51.6-32.4,29.7-160.2-49-285.3   C268.4,70.7,162.8-4.5,111.2,28c-4.6,2.9-8.5,6.5-11.9,10.8C154.4,26.1,248.5,98.6,320.2,212.7z"/>
      <path fill="#0FB0F5"
            d="M320.3,356.4C206.2,428.1,88.2,453.2,44,417.9c1.2,5.3,4.1,10.6,7,15.1c32.4,51.6,161,28.9,286.2-49.7   C462.3,304.6,533.9,201,505.4,147.1c-2.5-4.7-7-11-11.3-14.4C506.8,187.8,434.4,284.7,320.3,356.4z"/>
      <path fill="#0579F7"
            d="M191.9,152.2c114.1-71.7,230.4-96.2,274.6-60.9c-1.2-5.3-3.2-10.3-6.1-14.9c-32.4-51.6-160.2-29.7-285.4,49   C49.9,204-25.3,309.6,7.2,361.2c2.9,4.5,6.5,8.5,10.8,11.9C5.3,317.9,77.8,223.9,191.9,152.2z"/>
      <path fill="#0FB0F5"
            d="M181.1,300.1C109.4,186,84.3,68,119.7,23.8c-5.3,1.2-10.6,4.1-15.1,7c-51.6,32.4-28.9,161,49.8,286.2   c78.7,125.2,182.3,196.7,236.2,168.3c4.7-2.5,11-7,14.4-11.3C349.7,486.6,252.8,414.3,181.1,300.1z"/>
      <path fill="#06D4FB"
            d="M279.4,291.2C165.2,363,47.2,388,3,352.7c1.2,5.3,4.1,10.6,7,15.1c32.4,51.6,161,28.9,286.2-49.8   c125.2-78.7,196.7-182.3,168.3-236.2c-2.5-4.7-7-11-11.3-14.4C465.8,122.6,393.5,219.5,279.4,291.2z"/>
    </g>
    </svg>
    </symbol>

    <symbol id="up-down-icon">
      <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" class="bi bi-arrow-down-up" viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M11.5 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L11 2.707V14.5a.5.5 0 0 0 .5.5zm-7-14a.5.5 0 0 1 .5.5v11.793l3.146-3.147a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 .708-.708L4 13.293V1.5a.5.5 0 0 1 .5-.5z"/>
      </svg>
    </symbol>

    <symbol id="list-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-list"
           viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"/>
      </svg>
    </symbol>

    <symbol id="gear-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-gear"
           viewBox="0 0 16 16">
        <path
            d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z"/>
        <path
            d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115l.094-.319z"/>
      </svg>
    </symbol>

    <symbol id="journals-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-journals"
           viewBox="0 0 16 16">
        <path
            d="M5 0h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2 2 2 0 0 1-2 2H3a2 2 0 0 1-2-2h1a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1H1a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v9a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1H3a2 2 0 0 1 2-2z"/>
        <path
            d="M1 6v-.5a.5.5 0 0 1 1 0V6h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1H1zm0 3v-.5a.5.5 0 0 1 1 0V9h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1H1zm0 2.5v.5H.5a.5.5 0 0 0 0 1h2a.5.5 0 0 0 0-1H2v-.5a.5.5 0 0 0-1 0z"/>
      </svg>
    </symbol>

    <symbol id="warning-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
           class="bi bi-exclamation-triangle" viewBox="0 0 16 16">
        <path
            d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.146.146 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.163.163 0 0 1-.054.06.116.116 0 0 1-.066.017H1.146a.115.115 0 0 1-.066-.017.163.163 0 0 1-.054-.06.176.176 0 0 1 .002-.183L7.884 2.073a.147.147 0 0 1 .054-.057zm1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566z"/>
        <path
            d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995z"/>
      </svg>
    </symbol>

    <symbol id="bar-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-align-start"
           viewBox="0 0 16 16">
        <path fill-rule="evenodd" d="M1.5 1a.5.5 0 0 1 .5.5v13a.5.5 0 0 1-1 0v-13a.5.5 0 0 1 .5-.5z"/>
        <path d="M3 7a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7z"/>
      </svg>
    </symbol>

    <symbol id="radios-grid-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-ui-radios-grid"
           viewBox="0 0 16 16">
        <path
            d="M3.5 15a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zm9-9a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zm0 9a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5zM16 3.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0zm-9 9a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0zm5.5 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zm-9-11a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm0 2a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/>
      </svg>
    </symbol>

    <symbol id="logout" viewBox="0 0 16 16">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-box-arrow-right"
           viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M10 12.5a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-9a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v2a.5.5 0 0 0 1 0v-2A1.5 1.5 0 0 0 9.5 2h-8A1.5 1.5 0 0 0 0 3.5v9A1.5 1.5 0 0 0 1.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-2a.5.5 0 0 0-1 0v2z"/>
        <path fill-rule="evenodd"
              d="M15.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 0 0-.708.708L14.293 7.5H5.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3z"/>
      </svg>
    </symbol>

    <symbol id="node-plus" viewBox="0 0 16 16">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-node-plus"
           viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M11 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM6.025 7.5a5 5 0 1 1 0 1H4A1.5 1.5 0 0 1 2.5 10h-1A1.5 1.5 0 0 1 0 8.5v-1A1.5 1.5 0 0 1 1.5 6h1A1.5 1.5 0 0 1 4 7.5h2.025zM11 5a.5.5 0 0 1 .5.5v2h2a.5.5 0 0 1 0 1h-2v2a.5.5 0 0 1-1 0v-2h-2a.5.5 0 0 1 0-1h2v-2A.5.5 0 0 1 11 5zM1.5 7a.5.5 0 0 0-.5.5v1a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-1z"/>
      </svg>
    </symbol>

    <symbol id="splitter" viewBox="0 0 16 16">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-diagram-3-fill"
           viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5v-1zm-6 8A1.5 1.5 0 0 1 1.5 10h1A1.5 1.5 0 0 1 4 11.5v1A1.5 1.5 0 0 1 2.5 14h-1A1.5 1.5 0 0 1 0 12.5v-1zm6 0A1.5 1.5 0 0 1 7.5 10h1a1.5 1.5 0 0 1 1.5 1.5v1A1.5 1.5 0 0 1 8.5 14h-1A1.5 1.5 0 0 1 6 12.5v-1zm6 0a1.5 1.5 0 0 1 1.5-1.5h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5v-1z"/>
      </svg>
    </symbol>

    <symbol id="building" viewBox="0 0 16 16">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-building-fill"
           viewBox="0 0 16 16">
        <path
            d="M3 0a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h3v-3.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V16h3a1 1 0 0 0 1-1V1a1 1 0 0 0-1-1H3Zm1 2.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1Zm3 0a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1Zm3.5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5ZM4 5.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1ZM7.5 5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5Zm2.5.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1ZM4.5 8h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5Zm2.5.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1Zm3.5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5Z"/>
      </svg>
    </symbol>

    <symbol id="people" viewBox="0 0 16 16">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-people-fill"
           viewBox="0 0 16 16">
        <path
            d="M7 14s-1 0-1-1 1-4 5-4 5 3 5 4-1 1-1 1H7Zm4-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm-5.784 6A2.238 2.238 0 0 1 5 13c0-1.355.68-2.75 1.936-3.72A6.325 6.325 0 0 0 5 9c-4 0-5 3-5 4s1 1 1 1h4.216ZM4.5 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"/>
      </svg>
    </symbol>

  </svg>

</template>

<style scoped>

</style>