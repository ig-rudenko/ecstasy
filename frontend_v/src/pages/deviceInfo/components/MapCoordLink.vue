<template>
  <a target="_blank"
     :href="'https://yandex.ru/maps/959/sevastopol/?mode=search&sll='+coords[0]+'%2C'+coords[1]+'&text='+coords[0]+'%2C'+coords[1]+'&z=17'">
    <Button v-if="coords?.length" text v-tooltip.bottom="'Местоположение'">
      <svg width="30" height="30" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 1a9.002 9.002 0 0 0-6.366 15.362c1.63 1.63 5.466 3.988 5.693 6.465.034.37.303.673.673.673.37 0 .64-.303.673-.673.227-2.477 4.06-4.831 5.689-6.46A9.002 9.002 0 0 0 12 1z"
            fill="#F43"></path>
        <path d="M12 13.079a3.079 3.079 0 1 1 0-6.158 3.079 3.079 0 0 1 0 6.158z" fill="#fff"></path>
      </svg>
    </Button>
  </a>
</template>

<script lang="ts">
import {defineComponent, PropType} from "vue";

export default defineComponent({
  props: {
    coords: {required: true, type: Array as PropType<any[]>}
  }
})
</script>