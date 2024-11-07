<template>
  <!--  <h6>Число волокон в модуле</h6>-->
  <div>
    <div class="fiber-group">
      <div>
        <span class="circle blue me-2"></span>Синий
      </div>
      <div>
        <span class="circle orange me-2"></span>Оранжевый
      </div>
      <div>
        <span class="circle green me-2"></span>Зеленый
      </div>
      <div>
        <span class="circle brown me-2"></span>Коричневый
      </div>
    </div>

    <div v-if="count>=8" class="fiber-group">
      <div>
        <span class="circle grey me-2"></span>Серый
      </div>
      <div>
        <span class="circle white me-2"></span>Белый
      </div>
      <div>
        <span class="circle red me-2"></span>Красный
      </div>
      <div>
        <span class="circle black me-2"></span>Черный
      </div>
    </div>

    <div v-if="count>=12" class="fiber-group">
      <div>
        <span class="circle yellow me-2"></span>Желтый
      </div>
      <div>
        <span class="circle violet me-2"></span>Фиолетовый
      </div>
      <div>
        <span class="circle pink me-2"></span>Розовый
      </div>
      <div>
        <span class="circle aqua me-2"></span>Бирюзовый
      </div>
    </div>

    <!-- С прочерком -->

    <div v-if="count>=16" class="fiber-group">
      <div>
        <span class="circle blue me-2"></span>Синий с меткой
        <span class="ring"></span>
      </div>
      <div>
        <span class="circle orange me-2"></span>Оранжевый с меткой
        <span class="ring"></span>
      </div>
      <div>
        <span class="circle green me-2"></span>Зеленый с меткой
        <span class="ring"></span>
      </div>
      <div>
        <span class="circle brown me-2"></span>Коричневый с меткой
        <span class="ring"></span>
      </div>
    </div>

    <div v-if="count>=24" class="fiber-group">
      <div>
        <span class="circle grey me-2"></span>Серый с меткой
        <span class="ring"></span>
      </div>
      <div>
        <span class="circle white me-2"></span>Белый с меткой
        <span class="ring"></span>
      </div>
      <div>
        <span class="circle red me-2"></span>Красный с меткой
        <span class="ring"></span>
      </div>
      <div>
        <span class="circle natural me-2"></span>Натуральный (прозрачный)
      </div>
      <div>
        <span class="circle yellow me-2"></span>Желтый с меткой
        <span class="ring"></span>
      </div>
      <div>
        <span class="circle violet me-2"></span>Фиолетовый с меткой
        <span class="ring"></span>
      </div>
      <div>
        <span class="circle pink me-2"></span>Розовый с меткой
        <span class="ring"></span>
      </div>
      <div>
        <span class="circle aqua me-2"></span>Бирюзовый с меткой
        <span class="ring"></span>
      </div>
    </div>

  </div>

</template>

<script>
export default {
  name: "RizerFiberColorExample",
  props: {
    count: {required: true, type: Number}
  }
}
</script>

<style scoped>
.circle {
  margin-right: 10px;
  padding: 1px 12px;
  border-radius: 20px;
  border: 1px solid #1f2634FF;
}

.fiber-group div {
  margin: 10px 0;
  text-wrap: nowrap;
}

.blue {
  background-color: #416BB2FF;
}

.orange {
  background-color: #E87C1BFF;
}

.green {
  background-color: #4BB37CFF;
}

.brown {
  background-color: #6C5840FF;
}

.grey {
  background-color: #7B8D9CFF;
}

.white {
  background-color: #FFFFFFFF;
}

.red {
  background-color: #E8491DFF;
}

.black {
  background-color: #2D2D2DFF;
}

.yellow {
  background-color: #F9B11EFF;
}

.violet {
  background-color: #9A43CBFF;
}

.pink {
  background-color: #EC909DFF;
}

.aqua {
  background-color: #15C6C6FF;
}

.natural {
  background-color: #d3d3d3;
}

.ring {
  box-shadow: none;
  display: block;
  position: relative;
  transform: rotate(-45deg);
  background: #000;
  width: 25px;
  height: 2px;
  top: -13px;
}
</style>