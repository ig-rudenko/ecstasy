<template>
  <div>
    <template v-for="(dev, index) in ringsPoints" :key="dev.name">
      <div v-if="index !== 0" :class="['port', 'bottom'].concat(portStatusClass(dev, dev.port_to_prev_dev))"
           v-tooltip.left="dev.port_to_prev_dev.status">
        <span class="font-mono">{{ dev.port_to_prev_dev.name }}</span>
      </div>

      <div class="ring-node first:!bg-indigo-100 last:!bg-indigo-100 dark:first:!bg-indigo-900/60 dark:last:!bg-indigo-900/60">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex items-center gap-4">
            <div class="shrink-0">
              <svg v-if="dev.available === null" xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="#9ca3af" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path d="M5.255 5.786a.237.237 0 0 0 .241.247h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-.977 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286zm1.557 5.763c0 .533.425.927 1.01.927.609 0 1.028-.394 1.028-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94z"/>
              </svg>
              <svg v-else-if="dev.available === true" xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="#22c55e" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="#ef4444" viewBox="0 0 16 16">
                <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"/>
              </svg>
            </div>

            <div>
              <router-link class="point-name hover:text-indigo-600 dark:hover:text-indigo-300" :to="getURLForDevice(dev.name)" target="_blank">
                {{ dev.name }}
              </router-link>
              <div class="mt-1 font-mono text-sm text-gray-500 dark:text-gray-400">{{ dev.ip }}</div>
            </div>
          </div>

          <Badge severity="secondary">{{ dev.ip }}</Badge>
        </div>
      </div>

      <template v-if="index !== ringsPoints.length - 1">
        <div :class="portStatusClass(dev, dev.port_to_next_dev)" class="port top"
             v-tooltip.left="dev.port_to_next_dev.status">
          <span class="font-mono">{{ dev.port_to_next_dev.name }}</span>
        </div>
        <div class="port-line"></div>
      </template>
    </template>
  </div>
</template>

<script>
export default {
  name: "RingView",
  props: {
    portsColorAlways: {required: false, default: true},
    copyHeadToTail: {required: false, default: false},
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

  computed: {
    ringsPoints() {
      if (this.copyHeadToTail) {
        return [...this.points, this.points[0]]
      }
      return this.points
    },
  },

  methods: {
    portStatusClass(device, port) {
      if (this.portsColorAlways && !device.available) return "port-unknown";
      if (port.status === "admin down") return "port-admin-down";
      if (port.status === "down") return "port-down";
      return "port-up"
    },
    getURLForDevice(device_name) {
      return `/device/${device_name}`
    }
  },
}
</script>

<style scoped>
.ring-node {
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 24px;
  padding: 18px 22px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(10px);
}

.dark .ring-node {
  background: rgba(15, 23, 42, 0.45);
  border-color: rgba(71, 85, 105, 0.45);
}

.point-name {
  display: inline-block;
  font-weight: 600;
}

.port {
  box-sizing: border-box;
  position: relative;
  width: 20px;
  height: 20px;
  left: calc(50% - 20px / 2 + 1px);
  border-radius: 999px;
  z-index: 10;
  justify-content: flex-start;
  display: flex;
  align-items: center;
}

.port span {
  font-size: 14px;
  position: relative;
  left: 30px;
  color: rgb(55 65 81);
}

.dark .port span {
  color: rgb(229 231 235);
}

.top {
  top: -12px;
}

.bottom {
  top: 12px;
}

.port-up {
  border: 1px solid #1f2937;
  background: #22c55e;
}

.port-down {
  border: 1px solid #111827;
  background: #9ca3af;
}

.port-unknown {
  border: 1px solid #111827;
  background: #ffffff;
}

.port-admin-down {
  border: 1px solid #111827;
  background: #ef4444;
}

.port-line {
  left: calc(50% - 24px);
  position: relative;
  border: 2px solid rgba(107, 114, 128, 0.85);
  transform: rotate(90deg);
  width: 50px;
}
</style>
