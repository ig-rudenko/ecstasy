<script setup lang="ts">
const props = defineProps({
  condition: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update']);

</script>

<template>
  <div v-if="props.condition" class="text-muted-color text-help flex items-center gap-1 p-1">
    <i class="pi pi-spin pi-spinner"/>
    <div>Обновление</div>
  </div>
  <span v-else @click="() => emit('update')" class="text-muted-color text-help p-1 !cursor-pointer">Обновить</span>
</template>
