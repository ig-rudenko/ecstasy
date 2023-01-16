<template>
<div class="btn-group" role="group">
  <div class="col-auto blockquote" style="margin: 5px 10px;">
      {{ interface.Interface }}
  </div>
  <div v-if="permissionLevel >= 2" class="btn-group-vertical" role="group">

<!--     ВКЛЮЧИТЬ ПОРТ -->
      <button type="button" class="btn text-success" style="height: 16px; font-size: 10px; padding: 0"
             @click="portAction('up', interface.Interface, interface.Description)">
          <span data-bs-toggle="modal" data-bs-target="#modal" style="padding: 2px 12px 6px 12px">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-up-fill" viewBox="0 0 16 16">
              <path d="m7.247 4.86-4.796 5.481c-.566.647-.106 1.659.753 1.659h9.592a1 1 0 0 0 .753-1.659l-4.796-5.48a1 1 0 0 0-1.506 0z"></path>
            </svg>
          </span>
      </button>

<!--     ВЫКЛЮЧИТЬ ПОРТ -->
      <button type="button" class="btn text-danger" style="height: 16px; font-size: 10px; padding: 0"
             @click="portAction('down', interface.Interface, interface.Description)">
          <span data-bs-toggle="modal" data-bs-target="#modal" style="height: 16px">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-down-fill" viewBox="0 0 16 16">
              <path d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"></path>
            </svg>
          </span>
      </button>
  </div>

  <div class="btn-group" role="group">

<!--     ПЕРЕЗАГРУЗКА ПОРТА -->
      <span v-if="permissionLevel >= 1" data-bs-toggle="modal" data-bs-target="#modal">
      <button type="button" class="btn" style="padding: 6px 6px 2px 6px"
              @click="portAction('reload', interface.Interface, interface.Description)">

        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="black" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
          <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"></path>
          <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"></path>
        </svg>
      </button>
      </span>

<!--     Посмотреть порт -->
      <a v-if="showPortEnterLink" class="btn" style="padding: 6px 6px 2px 6px"
         :href="'/device/port?device='+deviceName+'&port='+interface.Interface+'&desc='+interface.Description">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box" viewBox="0 0 16 16">
          <path d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5 8.186 1.113zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923l6.5 2.6zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464L7.443.184z"></path>
        </svg>
      </a>
  </div>
</div>
</template>


<script>
import {defineComponent} from "vue";

export default defineComponent({
  props: {
    permissionLevel: {
      required: true,
      type: Number
    },
    showPortEnterLink: {
      required: false,
      type: Boolean,
      default: false
    },
    deviceName: {
      required: true,
      type: String
    },
    interface: {
      required: true,
      type: Object
    },
    portAction: {
      required: true,
      type: Function
    }
  }
})
</script>