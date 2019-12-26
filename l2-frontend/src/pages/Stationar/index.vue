<template>
  <div ref="root" class="root">
    <div class="sidebar">
      <div class="sidebar-top">
        <input type="text" class="form-control" v-model="pk" @keyup.enter="load" autofocus
               placeholder="Номер истории"/>
        <button class="btn btn-blue-nb" @click="load" :disabled="pk === ''">Загрузить</button>
      </div>
      <div class="sidebar-content">
        <div class="inner" v-if="direction !== null && patient !== null">
          <div class="inner-card">
            История болезни №{{direction}}
          </div>
          <patient-card :patient="patient" class="inner-card" />
          <div class="sidebar-btn-wrapper"
               v-for="(title, key) in menuItems"
               :key="key">
            <button class="btn btn-blue-nb sidebar-btn">
              {{title}}
            </button>
            <button class="btn btn-blue-nb sidebar-btn"
                    v-if="menuNeedPlus[key]"
            >
              <i class="fa fa-plus"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="content">
      <div class="top">

      </div>
      <div class="inner">

      </div>
    </div>
  </div>
</template>

<script>
    import {mapGetters} from 'vuex'
    import menuMixin from './mixins/menu'
    import * as action_types from '../../store/action-types'
    import stationar_point from '../../api/stationar-point'
    import PatientCard from './PatientCard'
    import Patient from '../../types/patient'

    export default {
        mixins: [menuMixin],
        components: {PatientCard},
        data() {
            return {
                pk: '',
                direction: null,
                patient: null
            }
        },
        watch: {
            pk() {
                this.pk = this.pk.replace(/\D/g,'')
            }
        },
        methods: {
            async load() {
                this.$store.dispatch(action_types.INC_LOADING).then()
                const {ok, data, message} = await stationar_point.load(this, ['pk']);
                if (ok) {
                  this.pk = '';
                  this.direction = data.direction;
                  this.patient = new Patient(data.patient);
                } else {
                    errmessage(message)
                }
                this.$store.dispatch(action_types.DEC_LOADING).then()
            },
        },
        computed: {
            ...mapGetters({
                user_data: 'user_data',
                researches: 'researches',
            }),
        }
    }
</script>

<style scoped lang="scss">
  .root {
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;

    & > div {
      align-self: stretch;
    }
  }

  .sidebar {
    width: 260px;
    border-right: 1px solid #b1b1b1;
    display: flex;
    flex-direction: column;
  }

  .content {
    display: flex;
    flex-direction: column;
    width: calc(100% - 260px);
    border: none;

    .top {
      border-bottom: 1px solid #b1b1b1;
      height: 63px;
      padding: 5px;
    }

    .inner {
      height: calc(100% - 63px);
      overflow-y: auto;
      overflow-x: hidden;
    }
  }

  .sidebar-top {
    flex: 0 0 34px;
    display: flex;
    flex-direction: row;
    align-items: stretch;
    flex-wrap: nowrap;
    justify-content: stretch;

    input, button {
      align-self: stretch;
      border: none;
      border-radius: 0;
    }

    input {
      border-bottom: 1px solid #b1b1b1;
      width: 166px !important;
      flex: 2 166px;
    }

    button {
      flex: 3 94px;
      width: 94px
    }
  }

  .sidebar-content {
    position: relative;
    height: calc(100% - 34px);

    .inner {
      height: 100%;
      overflow-y: auto;
      overflow-x: hidden;
      &-card {
        width: 100%;
        background: #fff;
        border-bottom: 1px solid #b1b1b1!important;
        padding: 4px 12px;
      }
    }
  }

  .sidebar-btn {
    border-radius: 0;
    text-align: left;
    border-top: none!important;
    border-right: none!important;
    border-left: none!important;
    padding: 0 12px;
    height: 24px;

    &:not(:hover) {
      background-color: rgba(#000, .02)!important;
      color: #000;
      border-bottom: 1px solid #b1b1b1!important;
    }
  }

  .sidebar-btn-wrapper {
    display: flex;
    flex-direction: row;

    .sidebar-btn:first-child {
      flex: 1 1 auto;
    }
  }
</style>
