<script lang="ts">
import {defineComponent} from 'vue'

export default defineComponent({
  name: "Snow",
  computed: {
    range() {
      let r = []
      for (let i = 0; i < 50; i++) {
        r.push(i)
      }
      return r
    }
  }
})
</script>

<template>
  <div class="sticky top-0">
    <img style="z-index: 9999" v-for="i in range" :key="i"
         class="snowflake pi-spinn" width="24" height="24" src="/img/weather/snow.png" alt="snowflake"/>
  </div>
</template>

<style lang="scss">

.snowflake {
  --size: 1vw;
  width: var(--size);
  height: var(--size);
  border-radius: 50%;
  position: absolute;
  top: -5vh;
}

@keyframes snowfall {
  0% {
    transform: translate3d(var(--left-ini), 0, 0);
  }
  100% {
    transform: translate3d(var(--left-end), 103vh, 0);
  }
}

@for $i from 1 through 50 {
  .snowflake:nth-child(#{$i}) {
    --size: #{random(5) * 0.2}vw;
    --left-ini: #{random(20) - 10}vw;
    --left-end: #{random(20) - 10}vw;
    left: #{random(90)}vw;
    animation: snowfall #{5 + random(10)}s linear infinite;
    animation-delay: -#{random(10)}s;
  }
}
</style>