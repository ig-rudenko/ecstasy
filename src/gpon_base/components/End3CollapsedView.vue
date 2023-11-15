<template>

<template v-for="(line, index) in customerLines">

  <div :class="getCustomerLineClasses(index)">

    <div class="col-md-2 fw-bold">
      <a :href="'/gpon/tech-data/end3/' + line.id">
        {{ customerLineTypeName(line.type) }} {{ index + 1 }}
      </a>
    </div>
    <div class="col-auto">
        {{ getFullAddress(line.address) }}
        <br>
        Локация: {{ line.location }}.
    </div>
    <div class="col-auto">{{ customerLineNumbers(line) }}</div>
    <div class="col-auto">
        <button v-if="line.detailInfo" @click="$emit('deleteInfo', index)" class="btn btn-outline-warning rounded-5 py-1">
          close
        </button>
        <button v-else @click="$emit('getInfo', index)" class="btn btn-outline-primary rounded-5 py-1">
          detail
        </button>
    </div>
  </div>

  <div v-if="line.errorStatus" class="alert alert-danger">Ошибка при загрузке данных.
    <br> {{line.errorMessage||''}} <br> Статус: {{line.errorStatus}}
  </div>

  <div v-if="line.detailInfo" class="card px-3 rounded-0" style="border-top: none; margin-bottom: 10px">
    <div v-for="part in line.detailInfo" class="align-items-center row py-1">
      <div class="col-1">{{part.number}}</div>
        <div class="col-2">
          <TechCapabilityBadge :status="part.status"/>
        </div>
      <div class="col-auto">
        <div class="d-flex" v-for="subscriber in part.subscribers">
          <div class="me-2">{{subscriber.name}}</div>
          <div>{{ subscriber.transit }}</div>
        </div>
        <div class="text-muted" v-if="!part.subscribers.length">
          нет абонента
        </div>
      </div>
    </div>
  </div>

</template>
</template>

<script>
import TechCapabilityBadge from "./TechCapabilityBadge.vue";
import formatAddress from "../../helpers/address";

export default {
  name: "End3CollapsedView",
  components: {TechCapabilityBadge},
  props: {
    customerLines: {required: true, type: Array},
  },

  methods: {
    getCustomerLineClasses(index){
      let class_list = ['py-2', 'row', 'align-items-center']
      if (index % 2 === 0) class_list.push('grey-back');
      return class_list
    },

    customerLineTypeName(type) {
      if (type === "splitter") {
        return "Сплиттер"
      } else if (type === "rizer") {
        return "Райзер"
      } else {
        return type
      }
    },

    customerLineNumbers(line) {
      if (line.type === "splitter") {
        return `${line.capacity} портов`
      } else if (line.type === "rizer") {
        return `${line.capacity} волокон`
      } else {
        return line
      }
    },

    getFullAddress(address) {
      return formatAddress(address)
    },
  }
}
</script>

<style scoped>
.grey-back {
  background-color: #ebebeb;
}
</style>