<template>
  <div class="container flex justify-around">

    <div v-if="!isMobile || currentStep === 1" class="flex flex-col items-center justify-center gap-2">
      <svg v-if="currentStep <= 1" xmlns="http://www.w3.org/2000/svg" width="32" height="32"
           :fill="currentStep===1?'#633BBC':'#E1E1E6'" viewBox="0 0 16 16">
        <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0ZM9.283 4.002H7.971L6.072 5.385v1.271l1.834-1.318h.065V12h1.312V4.002Z"/>
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#36CA4E" viewBox="0 0 16 16">
        <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
      </svg>
      <b>{{ stepsText[0] }}</b>
    </div>

    <div v-if="!isMobile">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-chevron-right"
           viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
      </svg>
    </div>

    <div v-if="!isMobile || currentStep === 2" class="flex flex-col items-center justify-center gap-2">
      <svg v-if="currentStep <= 2" xmlns="http://www.w3.org/2000/svg" width="32" height="32"
           :fill="currentStep===2?'#633BBC':'#E1E1E6'" viewBox="0 0 16 16">
        <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0ZM6.646 6.24c0-.691.493-1.306 1.336-1.306.756 0 1.313.492 1.313 1.236 0 .697-.469 1.23-.902 1.705l-2.971 3.293V12h5.344v-1.107H7.268v-.077l1.974-2.22.096-.107c.688-.763 1.287-1.428 1.287-2.43 0-1.266-1.031-2.215-2.613-2.215-1.758 0-2.637 1.19-2.637 2.402v.065h1.271v-.07Z"/>
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#36CA4E" viewBox="0 0 16 16">
        <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
      </svg>
      <b>{{ stepsText[1] }}</b>
    </div>

    <div v-if="!isMobile">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
        <path fill-rule="evenodd"
              d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
      </svg>
    </div>

    <div v-if="!isMobile || currentStep === 3" class="flex flex-col items-center justify-center gap-2">
      <svg v-if="currentStep <= 3" xmlns="http://www.w3.org/2000/svg" width="32" height="32"
           :fill="currentStep===3?'#633BBC':'#E1E1E6'" viewBox="0 0 16 16">
        <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0Zm-8.082.414c.92 0 1.535.54 1.541 1.318.012.791-.615 1.36-1.588 1.354-.861-.006-1.482-.469-1.54-1.066H5.104c.047 1.177 1.05 2.144 2.754 2.144 1.653 0 2.954-.937 2.93-2.396-.023-1.278-1.031-1.846-1.734-1.916v-.07c.597-.1 1.505-.739 1.482-1.876-.03-1.177-1.043-2.074-2.637-2.062-1.675.006-2.59.984-2.625 2.12h1.248c.036-.556.557-1.054 1.348-1.054.785 0 1.348.486 1.348 1.195.006.715-.563 1.237-1.342 1.237h-.838v1.072h.879Z"/>
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#36CA4E" viewBox="0 0 16 16">
        <path
            d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
      </svg>
      <b>{{ stepsText[2] }}</b>
    </div>

  </div>
</template>

<script>
export default {
  name: "StepMenu",
  props: {
    currentStep: {required: true},
    stepsText: {required: true, type: Array},
    isMobile: {required: false, default: false},
  },
}
</script>

<style scoped>

</style>