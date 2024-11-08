<template>
  <div class="header">
    <div class="text-2xl font-semibold py-3">{{ title }}</div>

    <!-- ДЕЙСТВИЯ -->
    <div class="flex gap-2 py-2">
      <Button @click="exitURL" class="back-button dark:!text-gray-300" text>
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
          <path
              d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/>
        </svg>
        <span v-if="!isMobile">Выйти</span>
      </Button>

      <!-- Режим редактирования -->
      <Button v-if="editMode" @click="editMode = false" class="view-button" text>
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
          <path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/>
          <path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/>
        </svg>
        <span v-if="!isMobile">Просмотр</span>
      </Button>

      <!-- Режим просмотра -->
      <template v-else>
        <Button @click="$emit('print')" class="print-button" text>
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
            <path
                d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2H5zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1z"/>
            <path
                d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2V7zm2.5 1a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
          </svg>
          <span v-if="!isMobile">Печать</span>
        </Button>

        <Button v-if="hasPermissionToEdit" @click="editMode = true" class="edit-button" text>
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
            <path
                d="M12.854.146a.5.5 0 0 0-.707 0L10.5 1.793 14.207 5.5l1.647-1.646a.5.5 0 0 0 0-.708l-3-3zm.646 6.061L9.793 2.5 3.293 9H3.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.207l6.5-6.5zm-7.468 7.468A.5.5 0 0 1 6 13.5V13h-.5a.5.5 0 0 1-.5-.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.5-.5V10h-.5a.499.499 0 0 1-.175-.032l-.179.178a.5.5 0 0 0-.11.168l-2 5a.5.5 0 0 0 .65.65l5-2a.5.5 0 0 0 .168-.11l.178-.178z"/>
          </svg>
          <span v-if="!isMobile">Редактировать</span>
        </Button>
      </template>


    </div>
  </div>
</template>

<script>
export default {
  name: "ViewPrintEditButtons",
  props: {
    title: {required: true, type: String},
    isMobile: {required: true, type: Boolean},
    hasPermissionToEdit: {required: true, type: Boolean},
    exitButtonURL: {required: true, type: String},
  },

  data() {
    return {
      __editMode: false,
    }
  },

  computed: {
    editMode: {
      get() {
        return this.__editMode
      },
      set(value) {
        this.__editMode = value
        this.$emit("changeMode", value)
      }
    }
  },

  methods: {

    exitURL() {
      window.location.href = this.exitButtonURL
    },

  },
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.print-button {
  border-radius: 12px;
  color: #6D5BD0;
  border: 1px #6D5BD0 solid;
}

.print-button:hover {
  box-shadow: 0 0 3px #6D5BD0;
}

.edit-button {
  border-radius: 12px;
  color: #ff802a;
  border: 1px #ff802a solid;
}

.edit-button:hover {
  box-shadow: 0 0 3px #ff802a;
}

.view-button {
  border-radius: 12px;
  color: #2a4dff;
  border: 1px #2a4dff solid;
}

.view-button:hover {
  box-shadow: 0 0 3px #2a4dff;
}

.back-button {
  border-radius: 12px;
  color: #4a4a4a;
  border: 1px #4a4a4a solid;
}

.back-button:hover {
  box-shadow: 0 0 3px #4a4a4a;
}

@media (max-width: 835px) {

  .header {
    justify-content: center;
    flex-wrap: wrap;
    padding: 0 40px;
  }

}

</style>