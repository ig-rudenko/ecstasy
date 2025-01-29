<template>
  <div class="solution-status">
    <!--Возвращено в начальное состояние-->
    <div v-if="status === 'reversed'"
         v-tooltip="'Было успешно выполнено, но далее случилась ошибка и данное действие было отменено'">
      <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="#fd7e14" viewBox="0 0 16 16">
        <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
        <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
      </svg>
    </div>
    <!--ДОСТУПНО-->
    <div v-else-if="status === 'done'"
         v-tooltip="'Успешно выполнено'">
      <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="#198754" viewBox="0 0 16 16">
        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
        <path
            d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"></path>
      </svg>
    </div>
    <!--НЕДОСТУПНО-->
    <div v-else v-tooltip="errorMessage">
      <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="red" viewBox="0 0 16 16">
        <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"></path>
      </svg>
    </div>
  </div>
</template>

<script>
export default {
  name: "SolutionStatus",
  props: {
    status: {required: true},
    error: {required: true}
  },
  computed: {
    errorMessage() {
      if (this.error) return this.error;
      return ""
    }
  }
}
</script>

<style scoped>
.solution-status {
  margin: 5px 10px 0 0;
}
</style>
