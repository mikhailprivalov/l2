<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="680px" width="100%" marginLeftRight="auto" margin-top>
    <span slot="header">Регистратура L2</span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <div class="row">
        <div class="col-xs-6 col-form left">
          <div class="form-row">
            <div class="row-t">Фамилия</div>
            <input type="text" class="form-control" v-model="card.family" :readonly="card.has_rmis_card">
          </div>
          <div class="form-row">
            <div class="row-t">Имя</div>
            <input type="text" class="form-control" v-model="card.name" :readonly="card.has_rmis_card">
          </div>
          <div class="form-row">
            <div class="row-t">Отчество</div>
            <input type="text" class="form-control" v-model="card.patronymic" :readonly="card.has_rmis_card">
          </div>
        </div>
        <div class="col-xs-6 col-form">
          <div class="form-row">
            <div class="row-t">Карта</div>
            <div class="row-v">
              {{card_pk >= 0 ? (card.id ? card.number : 'загрузка') : 'НОВАЯ'}}
            </div>
          </div>
          <div class="form-row">
            <div class="row-t">Пол</div>
            <input type="text" class="form-control" v-model="card.sex" maxlength="1" :readonly="card.has_rmis_card">
          </div>
          <div class="form-row">
            <div class="row-t">Дата рождения</div>
            <input type="date" class="form-control" v-model="card.birthday" :readonly="card.has_rmis_card">
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col-xs-12">
          <div class="info-row">
            Связь с РМИС – {{card.has_rmis_card ? "ЕСТЬ" : "НЕТ"}}
          </div>
        </div>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-8">
        </div>
        <div class="col-xs-4">
          <button type="button" @click="hide_modal" class="btn btn-primary-nb btn-blue-nb">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
  import Modal from './ui-cards/Modal'
  import patients_point from './api/patients-point'
  import * as action_types from './store/action-types'

  export default {
    name: 'l2-card-create',
    components: {Modal},
    props: {
      card_pk: {
        type: Number,
        required: true
      }
    },
    data() {
      return {
        card: {
          number: '',
          main_address: "",
          fact_address: "",
          family: "",
          patronymic: "",
          name: "",
          main_diagnosis: "",
          sex: "м",
          has_rmis_card: false,
        }
      }
    },
    created() {
      this.load_data()
    },
    methods: {
      hide_modal() {
        this.$root.$emit('hide_l2_card_create')
        this.$refs.modal.$el.style.display = 'none'
      },
      load_data() {
        if (this.card_pk === -1) {
          return;
        }
        let vm = this
        vm.loaded = false
        vm.$store.dispatch(action_types.INC_LOADING).then()
        patients_point.getCard(vm.card_pk).then(data => {
          vm.card = data
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
          vm.loaded = true
        })
      },
    }
  }
</script>

<style scoped lang="scss">
  .modal-mask {
    align-items: stretch !important;
    justify-content: stretch !important;
  }

  /deep/ .panel-flt {
    margin: 41px;
    align-self: stretch !important;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  /deep/ .panel-body {
    flex: 1;
    padding: 0;
    height: calc(100% - 91px);
    min-height: 200px;
  }

  .form-row {
    width: 100%;
    display: flex;
    border-bottom: 1px solid #434a54;
    &:first-child {
      border-top: 1px solid #434a54;
    }
    justify-content: stretch;
    .row-t {
      background-color: #AAB2BD;
      padding: 7px 0 0 10px;
      width: 35%;
      flex: 0 35%;
      color: #fff;
    }
    input, .row-v {
      background: #fff;
      border: none;
      border-radius: 0;
      width: 65%;
      flex: 0 65%;
      height: 34px;
    }
    .row-v {
      padding: 7px 0 0 10px;
    }
  }
  .col-form {
    &.left {
      padding-right: 0!important;
      .row-t, input, .row-v {
        border-right: 1px solid #434a54;
      }
    }
    &:not(.left) {
      padding-left: 0!important;
      .row-t {
        border-right: 1px solid #434a54;
      }
    }
  }
  .info-row {
    padding: 7px;
  }
</style>
