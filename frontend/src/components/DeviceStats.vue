<template>
  <!--  CPU-->
<div>
  <div style="padding: 7px 13px;">
    <svg
        v-bind:fill="stats.cpu?value_color(Math.max(...stats.cpu.util)):'grey'"
        class="bi bi-cpu" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" width="30" height="30">
      <path d="M5 0a.5.5 0 0 1 .5.5V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2A2.5 2.5 0 0 1 14 4.5h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14a2.5 2.5 0 0 1-2.5 2.5v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14A2.5 2.5 0 0 1 2 11.5H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2A2.5 2.5 0 0 1 4.5 2V.5A.5.5 0 0 1 5 0zm-.5 3A1.5 1.5 0 0 0 3 4.5v7A1.5 1.5 0 0 0 4.5 13h7a1.5 1.5 0 0 0 1.5-1.5v-7A1.5 1.5 0 0 0 11.5 3h-7zM5 6.5A1.5 1.5 0 0 1 6.5 5h3A1.5 1.5 0 0 1 11 6.5v3A1.5 1.5 0 0 1 9.5 11h-3A1.5 1.5 0 0 1 5 9.5v-3zM6.5 6a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3z"/>
    </svg>
    <span v-if="stats.cpu"> cpu {{stats.cpu.util.join(', ')}}%</span>
    <span v-else> cpu -</span>
  </div>
</div>

  <!--  RAM-->
<div>
  <div style="padding: 7px 13px;">
    <svg
        v-bind:fill="stats.ram?value_color(stats.ram.util):'grey'"
        class="bi bi-memory" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" width="30" height="30" >
      <path d="M1 3a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h4.586a1 1 0 0 0 .707-.293l.353-.353a.5.5 0 0 1 .708 0l.353.353a1 1 0 0 0 .707.293H15a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H1Zm.5 1h3a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-4a.5.5 0 0 1 .5-.5Zm5 0h3a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-4a.5.5 0 0 1 .5-.5Zm4.5.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-4ZM2 10v2H1v-2h1Zm2 0v2H3v-2h1Zm2 0v2H5v-2h1Zm3 0v2H8v-2h1Zm2 0v2h-1v-2h1Zm2 0v2h-1v-2h1Zm2 0v2h-1v-2h1Z"/>
    </svg>
    <span v-if="stats.ram"> ram {{stats.ram.util}}%</span>
    <span v-else> ram -</span>
  </div>
</div>

  <!--  FLASH-->
<div>
  <div style="padding: 7px 13px;">
    <svg v-bind:fill="stats.flash?value_color(stats.flash.util):'grey'"
        class="bi bi-sd-card-fill" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="{0}" >
      <path d="M12.5 0H5.914a1.5 1.5 0 0 0-1.06.44L2.439 2.853A1.5 1.5 0 0 0 2 3.914V14.5A1.5 1.5 0 0 0 3.5 16h9a1.5 1.5 0 0 0 1.5-1.5v-13A1.5 1.5 0 0 0 12.5 0Zm-7 2.75a.75.75 0 0 1 .75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 .75-.75Zm2 0a.75.75 0 0 1 .75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 .75-.75Zm2.75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 1.5 0Zm1.25-.75a.75.75 0 0 1 .75.75v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 1 .75-.75Z"/>
    </svg>
    <span v-if="stats.flash"> flash {{stats.flash.util}}%</span>
    <span v-else> flash -</span>
  </div>
</div>

  <!--  TEMP-->
<div>
  <div v-if="stats.temp" style="padding: 7px 13px;">
    <!--LOW-->
    <svg v-if="stats.temp.status === 'low'"
        xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="#0d6efd" class="bi bi-thermometer" viewBox="0 0 16 16">
      <path d="M8 14a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/>
      <path d="M8 0a2.5 2.5 0 0 0-2.5 2.5v7.55a3.5 3.5 0 1 0 5 0V2.5A2.5 2.5 0 0 0 8 0zM6.5 2.5a1.5 1.5 0 1 1 3 0v7.987l.167.15a2.5 2.5 0 1 1-3.333 0l.166-.15V2.5z"/>
    </svg>

    <!--NORMAL-->
    <svg v-else-if="stats.temp.status === 'normal'"
        xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="#198754" class="bi bi-thermometer-low" viewBox="0 0 16 16">
      <path d="M9.5 12.5a1.5 1.5 0 1 1-2-1.415V9.5a.5.5 0 0 1 1 0v1.585a1.5 1.5 0 0 1 1 1.415z"/>
      <path d="M5.5 2.5a2.5 2.5 0 0 1 5 0v7.55a3.5 3.5 0 1 1-5 0V2.5zM8 1a1.5 1.5 0 0 0-1.5 1.5v7.987l-.167.15a2.5 2.5 0 1 0 3.333 0l-.166-.15V2.5A1.5 1.5 0 0 0 8 1z"/>
    </svg>

    <!--MEDIUM-->
    <svg v-else-if="stats.temp.status === 'medium'"
        xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="#ff9836" class="bi bi-thermometer-half" viewBox="0 0 16 16">
      <path d="M9.5 12.5a1.5 1.5 0 1 1-2-1.415V6.5a.5.5 0 0 1 1 0v4.585a1.5 1.5 0 0 1 1 1.415z"/>
      <path d="M5.5 2.5a2.5 2.5 0 0 1 5 0v7.55a3.5 3.5 0 1 1-5 0V2.5zM8 1a1.5 1.5 0 0 0-1.5 1.5v7.987l-.167.15a2.5 2.5 0 1 0 3.333 0l-.166-.15V2.5A1.5 1.5 0 0 0 8 1z"/>
    </svg>

    <!--HIGH-->
    <svg v-else-if="stats.temp.status === 'high'"
        xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="#dc3545" class="bi bi-thermometer-high" viewBox="0 0 16 16">
      <path d="M9.5 12.5a1.5 1.5 0 1 1-2-1.415V2.5a.5.5 0 0 1 1 0v8.585a1.5 1.5 0 0 1 1 1.415z"/>
      <path d="M5.5 2.5a2.5 2.5 0 0 1 5 0v7.55a3.5 3.5 0 1 1-5 0V2.5zM8 1a1.5 1.5 0 0 0-1.5 1.5v7.987l-.167.15a2.5 2.5 0 1 0 3.333 0l-.166-.15V2.5A1.5 1.5 0 0 0 8 1z"/>
    </svg>
    {{stats.temp.value+'℃' || "-"}}
  </div>

  <div v-else style="padding: 7px 13px;">
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="grey" class="bi bi-thermometer" viewBox="0 0 16 16">
      <path d="M8 14a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/>
      <path d="M8 0a2.5 2.5 0 0 0-2.5 2.5v7.55a3.5 3.5 0 1 0 5 0V2.5A2.5 2.5 0 0 0 8 0zM6.5 2.5a1.5 1.5 0 1 1 3 0v7.987l.167.15a2.5 2.5 0 1 1-3.333 0l.166-.15V2.5z"/>
    </svg>
    temp -
  </div>

</div>
</template>

<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
      stats: {
        required: true,
        type: {
            cpu: { util: [ Number, ] },
            ram: { util: Number },
            flash: { util: Number },
            temp: { value: Number, status: String }
        },
        default: {}
      }
  },
  methods: {
    value_color: function (value) {
      if (!value) return "grey"
      if (value < 30) return "#198754";
      if (value < 80) return "#ff9836";
      return  "#dc3545";
    }
  }
})
</script>