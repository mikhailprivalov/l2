<template>
  <div class="root">
    <div class="top-editor">
      <div class="left">
        <div class="input-group">
          <span class="input-group-addon">Полное наименование</span>
          <input type="text" class="form-control" v-model="title">
        </div>
        <div class="input-group">
          <span class="input-group-addon">Краткое <small>(при необходимости)</small></span>
          <input type="text" class="form-control" v-model="short_title">
        </div>
      </div>
      <div class="right">
        <div class="input-group">
          <span class="input-group-addon">Код</span>
          <input type="text" class="form-control" v-model="code">
        </div>
        <div class="input-group">
          <label class="input-group-addon" style="height: 34px;text-align: left;">
            <input type="checkbox" v-model="hide"/> Скрытие исследования
          </label>
        </div>
      </div>
    </div>
    <div class="content-editor">
      <div class="input-group">
        <span class="input-group-addon">Подготовка, кабинет</span>
        <input type="text" class="form-control" v-model="info">
      </div>
    </div>
    <div class="footer-editor">
      <button class="btn btn-blue-nb" @click="cancel">Отмена</button>
      <button class="btn btn-blue-nb" :disabled="!valid" @click="save">Сохранить</button>
    </div>
  </div>
</template>

<script>
  import construct_point from '../api/construct-point'
  import * as action_types from '../store/action-types'

  export default {
    name: 'paraclinic-research-editor',
    props: {
      pk: {
        type: Number,
        required: true
      },
      department: {
        type: Number,
        required: true
      },
    },
    created() {
      this.load()
    },
    data() {
      return {
        title: '',
        short_title: '',
        code: '',
        info: '',
        hide: false,
        cancel_do: false,
        loaded_pk: -2
      }
    },
    watch: {
      pk() {
        this.load()
      }
    },
    computed: {
      valid() {
        return this.norm_title.length > 0 && !this.cancel_do
      },
      norm_title() {
        return this.title.trim()
      }
    },
    methods: {
      load() {
        this.title = ''
        this.short_title = ''
        this.code = ''
        this.info = ''
        this.hide = false
        if (this.pk >= 0) {
          let vm = this
          vm.$store.dispatch(action_types.INC_LOADING).then()
          construct_point.researchDetails(vm.pk).then(data => {
            vm.title = data.title
            vm.short_title = data.short_title
            vm.code = data.code
            vm.info = data.info
            vm.hide = data.hide
            vm.loaded_pk = vm.pk
          }).finally(() => {
            vm.$store.dispatch(action_types.DEC_LOADING).then()
          })
        }
      },
      cancel() {
        this.cancel_do = true
        this.$root.$emit('research-editor:cancel')
      },
      save() {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        construct_point.updateResearch(vm.pk, vm.department, vm.title, vm.short_title, vm.code, vm.info, vm.hide).then(() => {
          okmessage('Сохранено')
          this.cancel()
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      }
    }
  }
</script>

<style scoped lang="scss">
  .top-editor {
    display: flex;
    flex: 0 0 68px;

    .left, .right {
      flex: 0 0 50%
    }

    .left {
      border-right: 1px solid #96a0ad;
    }

    .input-group-addon {
      border-top: none;
      border-left: none;
      border-radius: 0;
    }

    .form-control {
      border-top: none;
      border-radius: 0;
    }

    .input-group > .form-control:last-child {
      border-right: none;
    }
  }

  .content-editor {
    height: 100%;
  }

  .footer-editor {
    flex: 0 0 34px;
    display: flex;
    justify-content: flex-end;
    background-color: #f4f4f4;

    .btn {
      border-radius: 0;
    }
  }

  .top-editor, .content-editor, .footer-editor {
    align-self: stretch;
  }

  .root {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    align-content: stretch;
  }

  .content-editor {
    padding: 5px;
    overflow-y: auto;
  }
</style>
