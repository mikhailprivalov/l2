<template>
  <modal ref="modal" @close="hide_plan_operations" show-footer="true" white-bg="true" max-width="680px" width="100%"
         marginLeftRight="auto" margin-top>
    <span slot="header">Планирование операции</span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <div class="form-row">
        <div class="row-t">Пациент (карта)</div>
      </div>
      <div class="form-row">
        <div class="row-t">История</div>
      </div>
      <div class="form-row">
        <div class="row-t">Дата операции</div>
      </div>
      <div class="form-row">
        <div class="row-t">Врач-хирург</div>
      </div>
      <div class="form-row">
        <div class="row-t">Вид операции</div>
      </div>
        <div class="form-row">
          <div class="col-xs-12">
            <div class="col-xs-3" style="float: right">
              <button class="btn btn-primary-nb btn-blue-nb btn-sm" type="button">
                Сохранить в план
              </button>
            </div>
            <div class="col-xs-3" style="float: right">
              <button class="btn btn-primary-nb btn-blue-nb btn-sm" type="button" style="float: right">
                Удалить из плана
              </button>
            </div>
          </div>
        </div>
      <div class="form-group sidebar-history">
        <div style="background-color: white">
          <v-select :clearable="false" label="label" :options="dirs_options"
                    :searchable="true" placeholder="Выберите историю болезни"/>
        </div>

      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-5" style="float: right">
          <button @click="hide_plan_operations" class="btn btn-primary-nb btn-blue-nb" type="button">
            Выйти
          </button>
        </div>


      </div>
    </div>
  </modal>
</template>

<script>
  import Modal from '../ui-cards/Modal'
  import patients_point from '../api/patients-point'
  import PatientSmallPicker from '../ui-cards/PatientSmallPicker'
  import * as action_types from '../store/action-types'
  import RadioField from '../fields/RadioField'
  import TypeAhead from 'vue2-typeahead'
  import moment from 'moment'
  import forms from '../forms'
  import vSelect from 'vue-select'
  import 'vue-select/dist/vue-select.css';

  import directions_point from '../api/directions-point'

  function validateSnils(snils, error = {}) {
    let result = false
    if (typeof snils === 'number') {
      snils = snils.toString();
    } else if (typeof snils !== 'string') {
      snils = '';
    }
    snils = snils.replace(/-/g, '').replace(/ /g, '')
    if (!snils.length) {
      error.code = 1;
      error.message = 'СНИЛС пуст';
    } else if (/[^0-9]/.test(snils)) {
      error.code = 2;
      error.message = 'СНИЛС может состоять только из цифр';
    } else if (snils.length !== 11) {
      error.code = 3;
      error.message = 'СНИЛС может состоять только из 11 цифр';
    } else {
      let sum = 0
      for (let i = 0; i < 9; i++) {
        sum += parseInt(snils[i]) * (9 - i);
      }
      let checkDigit = 0
      if (sum < 100) {
        checkDigit = sum;
      } else if (sum > 101) {
        checkDigit = parseInt(sum % 101);
        if (checkDigit === 100) {
          checkDigit = 0;
        }
      }
      if (checkDigit === parseInt(snils.slice(-2))) {
        result = true;
      } else {
        error.code = 4;
        error.message = 'Неправильное контрольное число';
      }
    }
    return result;
  }

  function capitalizeFirstLetter(string) {
    string = SwapLayouts(string).replace(/  +/g, ' ');
    const r = []
    for (const s of string.split(' ')) {
      let v = [];

      for (const si of s.split('-')) {
        v.push(si.charAt(0).toUpperCase() + si.slice(1).toLowerCase())
      }

      r.push(v.join('-'))
    }
    return r.join(' ').trim();
  }

  function SwapLayouts(str) {
    const replacer = {
      'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г',
      'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы',
      'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л', 'l': 'д',
      ';': 'ж', '\'': 'э', 'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и',
      'n': 'т', 'm': 'ь', ',': 'б', '.': 'ю', '/': '.'
    }

    for (let i = 0; i < str.length; i++) {
      if (replacer[str[i].toLowerCase()]) {
        let replace
        if (str[i] === str[i].toLowerCase()) {
          replace = replacer[str[i].toLowerCase()]
        } else if (str[i] === str[i].toUpperCase()) {
          replace = replacer[str[i].toLowerCase()].toUpperCase()
        }

        str = str.replace(str[i], replace)
      }
    }

    return str
  }

  export default {
    name: 'l2-card-create',
    components: {Modal, vSelect},
    props: {
      card_pk: {
        type: Number,
        required: true
      },
      base_pk: {
        type: Number,
        required: true
      },
    },
    data() {
      return {
        cards: [],
        individuals: [],
        dirs_options: ['члх', 'нейрохирургия', 'ОПН','травматология','Пульмунология',]
      }
    },
    created() {
      this.load_data()
      this.$root.$on('reload_editor', () => {
        this.load_data()
      })
    },
    updated() {
      // Костыль, что бы не вылезал автокомплит полей от браузера
      const {f, n, pn, ar, af} = this.$refs;
      setTimeout(() => {
        for (const r of [f, n, pn, ar, af]) {
          if (r) {
            const inp = $('input', r.$el);
            inp.attr('autocomplete', 'new-password')
          }
        }
      }, 100);
    },
    methods: {
      hide_plan_operations() {
        this.$root.$emit('hide_plan_operations')
        if (this.$refs.modal) {
          this.$refs.modal.$el.style.display = 'none'
        }
      }
    },
    load_stationar_research() {
      return ''
    }
  }
</script>

<style scoped lang="scss">
  $sidebar-history-width: 240px;
    .sidebar-history {
    width: $sidebar-history-width;
    height: 420px;
    /*background-color: #AAB2BD;*/
    border-right: 1px solid #56616c;
  }

  select.form-control {
    padding: 0;
    overflow: visible;
  }

  .nonPrior {
    opacity: .7;

    &:hover {
      opacity: 1;
    }
  }

  .prior {
    background-color: rgba(#000, .05);
  }

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

    &:first-child:not(.nbt-i) {
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

    .input-group {
      flex: 0 65%;
    }

    input, .row-v, /deep/ input {
      background: #fff;
      border: none;
      border-radius: 0 !important;
      width: 65%;
      flex: 0 65%;
      height: 34px;
    }

    &.sm-f {
      .row-t {
        padding: 2px 0 0 10px;
      }

      input, .row-v, /deep/ input {
        height: 26px;
      }
    }

    /deep/ input {
      width: 100% !important;
    }

    .row-v {
      padding: 7px 0 0 10px;
    }

    /deep/ .input-group {
      border-radius: 0;
    }

    /deep/ ul {
      width: auto;
      font-size: 13px;
    }

    /deep/ ul li {
      overflow: hidden;
      text-overflow: ellipsis;
      padding: 2px .25rem;
      margin: 0 .2rem;

      a {
        padding: 2px 10px;
      }
    }
  }

  .col-form {
    &.left {
      padding-right: 0 !important;

      .row-t, input, .row-v, /deep/ input {
        border-right: 1px solid #434a54 !important;
      }

      .form-row .input-group {
        width: 65%;
      }
    }

    &:not(.left):not(.mid) {
      padding-left: 0 !important;

      .row-t {
        border-right: 1px solid #434a54;
      }
    }
  }

  .info-row {
    padding: 7px;
  }

  .individual {
    cursor: pointer;

    &:hover {
      background-color: rgba(0, 0, 0, .15);
    }
  }

  .str /deep/ .input-group {
    width: 100%;
  }

  .lst {
    margin: 0;
    line-height: 1;
  }

  .c-pointer {
    &, & strong, &:hover {
      cursor: pointer!important;
    }
  }
</style>
