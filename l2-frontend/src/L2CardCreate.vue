<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="680px" width="100%" marginLeftRight="auto" margin-top>
    <span slot="header">Регистратура L2</span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <form autocomplete="off" class="row" onsubmit="return false;">
        <div class="col-xs-6 col-form left">
          <div class="form-row">
            <div class="row-t">Фамилия</div>
            <TypeAhead :delayTime="100" :getResponse="getResponse"
                       :highlighting="highlighting" :limit="10"
                       :minChars="1" :onHit="onHitFamily" :selectFirst="true" maxlength="36"
                       ref="f" src="/api/autocomplete?value=:keyword&type=family" v-model="card.family"
            />
          </div>
          <div class="form-row">
            <div class="row-t">Имя</div>
            <TypeAhead :delayTime="100" :getResponse="getResponse" :highlighting="highlighting"
                       :limit="10"
                       :minChars="1" :onHit="onHitName" :selectFirst="true" maxlength="36"
                       ref="n" src="/api/autocomplete?value=:keyword&type=name" v-model="card.name"
            />
          </div>
          <div class="form-row">
            <div class="row-t">Отчество</div>
            <TypeAhead :delayTime="100" :getResponse="getResponse"
                       :highlighting="highlighting" :limit="10"
                       :minChars="1" :onHit="onHitPatronymic" :selectFirst="true" maxlength="36"
                       ref="n" src="/api/autocomplete?value=:keyword&type=patronymic" v-model="card.patronymic"
            />
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
            <div class="row-t">Дата рождения</div>
            <input class="form-control" type="date" v-model="card.birthday">
          </div>
          <div class="form-row">
            <div class="row-t">Пол</div>
            <input class="form-control" maxlength="2" type="text" v-model="card.sex">
          </div>
        </div>
      </form>
      <div class="row" v-if="card_pk < 0">
        <div class="col-xs-6">
          <label class="info-row" style="cursor: pointer">
            <input :checked="card.new_individual || individuals.length === 0" @click="toggleNewIndividual"
                   type="checkbox"/> – новое физлицо
          </label>
        </div>
        <div class="col-xs-6">
          <div class="info-row">
            Найдено физлиц: {{individuals.length}}
          </div>
        </div>
        <div class="col-xs-12" v-if="!card.new_individual && individuals.length > 0">
          <div @click="select_individual(card.individual_pk)" class="info-row individual" v-for="i in individuals">
            <input :checked="i.pk === card.individual_pk" type="checkbox"/> {{i.fio}}<br/>
            <table class="table table-bordered table-condensed">
              <thead>
              <tr>
                <th>Тип</th>
                <th>Серия</th>
                <th>Номер</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="d in i.docs">
                <td>{{d.type_title}}</td>
                <td>{{d.serial}}</td>
                <td>{{d.number}}</td>
              </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="row" v-else>
        <div class="col-xs-12">
          <div class="info-row">
            Связь с РМИС – {{card.has_rmis_card ? 'ЕСТЬ' : 'НЕТ'}} <strong v-if="card.has_rmis_card">{{card.rmis_uid}}</strong>
          </div>
        </div>
      </div>
      <div class="row" v-if="card_pk < 0">
        <div class="col-xs-12 text-center">
          Для настройки документов сохраните карту
        </div>
      </div>
      <div v-else>
        <table class="table table-bordered table-condensed">
          <thead>
          <tr>
            <th>Тип документа</th>
            <th>Серия</th>
            <th>Номер</th>
            <th>Действие</th>
            <th></th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="d in card.docs">
            <td>
              {{d.type_title}}
            </td>
            <td>
              {{d.serial}}
            </td>
            <td>
              {{d.number}}
            </td>
            <td>
              {{d.is_active ? 'действ.' : 'не действителен'}}
            </td>
            <td>
              <a @click.prevent="edit_document(d.id)" href="#" v-if="!d.from_rmis"><i class="fa fa-pencil"></i></a>
              <span v-else>РМИС</span>
            </td>
          </tr>
          <tr>
            <td class="text-center" colspan="5">
              <a @click.prevent="edit_document(-1)" href="#">добавить документ</a>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
      <modal v-if="document_to_edit > -2" ref="modalDocEdit" @close="hide_modal_doc_edit" show-footer="true" white-bg="true" max-width="710px" width="100%" marginLeftRight="auto" margin-top>
        <span slot="header">Редактор документов (карта {{card.number}} пациента {{card.family}} {{card.name}} {{card.patronymic}})</span>
        <div slot="body" style="min-height: 200px;padding: 10px" class="registry-body">
          <div class="form-group">
            <label>Тип документа:</label>
            <select v-if="document_to_edit === -1" v-model="document.document_type">
              <option v-for="dt in card.doc_types" :value="dt.pk">{{dt.title}}</option>
            </select>
            <span v-else>{{document.type_title}}</span>
          </div>
          <div class="form-group">
            <label for="de-f2">Серия (при наличии):</label>
            <input class="form-control" id="de-f2" v-model="document.serial">
          </div>
          <div class="form-group">
            <label for="de-f3">Номер:</label>
            <input class="form-control" id="de-f3" v-model="document.number">
          </div>
          <div class="checkbox" style="padding-left: 15px;">
            <label>
              <input type="checkbox" v-model="document.is_active"> действителен
            </label>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button @click="hide_modal_doc_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
                Отмена
              </button>
            </div>
            <div class="col-xs-4">
              <button :disabled="!valid_doc" @click="save_doc()" class="btn btn-primary-nb btn-blue-nb" type="button">
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </modal>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button @click="hide_modal" class="btn btn-primary-nb btn-blue-nb" type="button">
            Отмена
          </button>
        </div>
        <div class="col-xs-4">
          <button :disabled="!valid" @click="save()" class="btn btn-primary-nb btn-blue-nb" type="button">
            Сохранить
          </button>
        </div>
        <div class="col-xs-4">
          <button :disabled="!valid" @click="save_hide_modal" class="btn btn-primary-nb btn-blue-nb" type="button">
            Сохранить и закрыть
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
  import TypeAhead from 'vue2-typeahead'
  import moment from 'moment'

  function capitalizeFirstLetter(string) {
    string = SwapLayouts(string)
    return (string.charAt(0).toUpperCase() + string.slice(1)).trim()
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
    components: {Modal, TypeAhead},
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
          birthday: moment().format('YYYY-MM-DD'),
          individual_pk: -1,
          new_individual: false,
          docs: [],
          docs_to_delete: [],
          rmis_uid: null,
          doc_types: [],
        },
        individuals: [],
        document_to_edit: -2,
        document: {
          number: ''
        }
      }
    },
    created() {
      this.load_data()
    },
    computed: {
      family() {
        return this.card.family
      },
      name() {
        return this.card.name
      },
      patronymic() {
        return this.card.patronymic
      },
      sex() {
        return this.card.sex
      },
      valid() {
        return this.card.family.length > 0 && this.card.name.length > 0 && this.card.birthday.match(/\d{4}-\d{2}-\d{2}/gm)
      },
      birthday() {
        return this.card.birthday
      },
      valid_doc() {
        return this.document.number.length > 0;
      }
    },
    watch: {
      sex() {
        let s = SwapLayouts(this.card.sex.toLowerCase())
        if (s.length > 1) {
          s = s[0]
        }
        if (s !== 'м' && s !== 'ж') {
          s = 'м'
        }
        this.card.sex = s
        this.individuals_search()
      },
      family() {
        this.card.family = capitalizeFirstLetter(this.card.family)
        this.individuals_search()
        this.individual_sex('family', this.card.family)
      },
      name() {
        this.card.name = capitalizeFirstLetter(this.card.name)
        this.individuals_search()
        this.individual_sex('name', this.card.name)
      },
      patronymic() {
        this.card.patronymic = capitalizeFirstLetter(this.card.patronymic)
        this.individuals_search()
        this.individual_sex('patronymic', this.card.patronymic)
      },
      birthday() {
        this.individuals_search()
      },
      individuals: {
        deep: true,
        handler(nv) {
          if (nv.length === 0) {
            this.card.new_individual = true
          }
        },
      }
    },
    methods: {
      select_individual(invpk) {
        this.card.individual_pk = invpk
      },
      toggleNewIndividual() {
        this.card.new_individual = !this.card.new_individual
      },
      hide_modal() {
        this.$root.$emit('hide_l2_card_create')
        this.$refs.modal.$el.style.display = 'none'
      },
      save_hide_modal() {
        this.save(true)
      },
      save(hide_after = false) {
        if (!this.valid) {
          return
        }
        let vm = this;
        (async () => {
          await vm.$store.dispatch(action_types.INC_LOADING)
          const data = await patients_point.sendCard(this.card_pk, this.card.family, this.card.name,
            this.card.patronymic, this.card.birthday, this.card.sex,
            this.card.individual_pk, this.card.new_individual, this.base_pk)
          if (data.result !== 'ok') {
            return
          }
          if (hide_after) {
            this.hide_modal()
          }
          this.card.pk = data.card_pk
          this.card.individual_pk = data.individual_pk
          this.$root.$emit('select_card', {
            card_pk: data.card_pk,
            base_pk: this.base_pk,
            hide: hide_after,
          })
        })().then().finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      getResponse(resp) {
        return [...resp.data.data]
      },
      onHitFamily(item) {
        this.card.family = item
      },
      onHitName(item) {
        this.card.name = item
      },
      onHitPatronymic(item) {
        this.card.patronymic = item
      },
      highlighting: (item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`),
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
      individuals_search() {
        if (!this.valid) {
          return
        }
        patients_point.individualsSearch(this.card.family, this.card.name,
          this.card.patronymic, this.card.birthday, this.card.sex).then(({result}) => {
          this.individuals = result
          this.card.individual_pk = result.length === 0 ? -1 : result[0].pk
          this.card.new_individual = result.length === 0
        })
      },
      individual_sex(t, v) {
        if (this.card_pk >= 0) {
          return
        }
        patients_point.individualSex(t, v).then(({sex}) => {
          this.card.sex = sex
        })
      },
      edit_document(pk) {
        this.document = {
          document_type: this.card.doc_types[0].pk,
          is_active: true,
          number: "",
          serial: "",
          type_title: null,
          ...(this.card.docs.find(x => x.id === pk) || {})
        };
        this.document_to_edit = pk
      },
      hide_modal_doc_edit() {
        this.$refs.modalDocEdit.$el.style.display = 'none'
        this.document_to_edit = -2
      },
      save_doc() {
        if (!this.valid_doc) {
          return
        }
        let vm = this;
        (async () => {
          await vm.$store.dispatch(action_types.INC_LOADING)
          const data = await patients_point.editDoc(this.document_to_edit,
            this.document.document_type, this.document.serial,
            this.document.number, this.document.is_active, this.card.individual_pk)
          this.load_data();
          this.document = {
            number: ''
          };
          this.hide_modal_doc_edit();
        })().then().finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      }
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
      padding-right: 0!important;

      .row-t, input, .row-v, /deep/ input {
        border-right: 1px solid #434a54 !important;
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

  .individual {
    cursor: pointer;

    &:hover {
      background-color: rgba(0, 0, 0, .15);
    }
  }
</style>
