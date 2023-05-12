<template>
<div class="list-group">

  <template v-for="dev in points">
    <div :class="['port', 'bottom'].concat(portStatusClass(dev, dev.port_to_prev_dev))" :title="dev.port_to_prev_dev.status">
<!--      Предыдущее оборудование-->
      <span>{{dev.port_to_prev_dev.name}}</span>
    </div>

    <div class="rounded-4 list-group-item list-group-item-action d-flex gap-3 py-3" aria-current="true">
      <div class="d-flex gap-2 w-100 justify-content-between">

<!--        НЕ ОПРЕДЕЛЕНО-->
        <svg v-if="dev.available === null" xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="gray" class="bi bi-question-circle" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path><path d="M5.255 5.786a.237.237 0 0 0 .241.247h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-.977 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286zm1.557 5.763c0 .533.425.927 1.01.927.609 0 1.028-.394 1.028-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94z"></path></svg>
<!--        ДОСТУПНО-->
        <svg v-else-if="dev.available === true" xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="#198754" class="bi bi-check-circle" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path><path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"></path></svg>
<!--        НЕДОСТУПНО-->
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="red" class="bi bi-x-circle-fill" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"></path></svg>

        <div>
          <span>{{dev.name}}</span>
        </div>

        <div>
          <span class="badge bg-primary">{{dev.ip}}</span>
        </div>

      </div>
    </div>

    <div :class="['port', 'top'].concat(portStatusClass(dev, dev.port_to_next_dev))" :title="dev.port_to_next_dev.status">
<!--      Следующее оборудование-->
      <span>{{dev.port_to_next_dev.name}}</span>
    </div>
    <div class="port-line"></div>

  </template>

</div>
</template>

<script>
export default {
  name: "RingView",
  props: {
    points: {
      required: true,
      type: [
        {
          name: String,
          ip: String,
          available: Boolean,
          port_to_prev_dev: {
            name: String,
            status: String,
            description: String,
          },
          port_to_next_dev: {
            name: String,
            status: String,
            description: String,
          },
        },
      ],
      default: [],
    }
  },
  methods: {
    portStatusClass(device, port) {
      if (!device.available) return ["port-unknown"];
      if (port.status === "up") return ["port-up"];
      if (port.status === "down") return ["port-down"];
      return ["port-admin-down"]
    }
  },
}
</script>

<style scoped>
.port {
    box-sizing: border-box;
    position: relative;
    width: 20px;
    height: 20px;
    left: calc(50% - 20px/2 + 1px);
    border-radius: 20px;
    z-index: 10;
    justify-content: flex-start;
    display: flex;
    align-items: center;
}

.port span {
    font-size: 14px;
    position: relative;
    left: 30px;
}

.top {
    top: -12px;
}

.bottom {
    top: 12px;
}

.port-up {
    border: 1px solid #747474;
    background: #3FCC4D;
}

.port-down {
    border: 1px solid #000000;
    background: #828282;
}

.port-unknown {
    border: 1px solid #000000;
    background: #ffffff;
}

.port-admin-down {
    border: 1px solid #000000;
    background: #cc3f3f;
}

.port-line {
    left: calc(50% - 24px);
    position: relative;
    border: 2px solid #747474;
    transform: rotate(90deg);
    width: 50px;
}

</style>