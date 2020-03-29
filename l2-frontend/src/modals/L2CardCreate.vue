<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="680px" width="100%" marginLeftRight="auto" margin-top>
    <span slot="header">Регистратура L2</span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <form autocomplete="off" class="row" onsubmit.prevent>
        <div class="col-xs-6 col-form left">
          <div class="form-row">
            <div class="row-t">Фамилия</div>
            <TypeAhead :delayTime="100" :getResponse="getResponse"
                       :highlighting="highlighting" :limit="10"
                       :minChars="1" :onHit="onHit('family')" :selectFirst="true" maxlength="36"
                       ref="f" src="/api/autocomplete?value=:keyword&type=family" v-model="card.family"
            />
          </div>
          <div class="form-row">
            <div class="row-t">Имя</div>
            <TypeAhead :delayTime="100" :getResponse="getResponse" :highlighting="highlighting"
                       :limit="10"
                       :minChars="1" :onHit="onHit('name')" :selectFirst="true" maxlength="36"
                       ref="n" src="/api/autocomplete?value=:keyword&type=name" v-model="card.name"
            />
          </div>
          <div class="form-row">
            <div class="row-t">Отчество</div>
            <TypeAhead :delayTime="100" :getResponse="getResponse"
                       :highlighting="highlighting" :limit="10"
                       :minChars="1" :onHit="onHit('patronymic')" :selectFirst="true" maxlength="36"
                       ref="n" src="/api/autocomplete?value=:keyword&type=patronymic" v-model="card.patronymic"
            />
          </div>
        </div>
        <div class="col-xs-6 col-form">
          <div class="form-row">
            <div class="row-t">Карта</div>
            <div class="row-v" style="font-weight: bold;">
              {{card_pk >= 0 ? (card.id ? card.number : 'загрузка') : 'НОВАЯ'}}
            </div>
          </div>
          <div class="form-row">
            <div class="row-t">Дата рождения</div>
            <input class="form-control" type="date" v-model="card.birthday">
          </div>
          <div class="form-row">
            <div class="row-t">Пол</div>
            <radio-field v-model="card.sex" :variants="sexes" fullWidth />
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
          <div @click="select_individual(card.individual)" class="info-row individual" v-for="i in individuals">
            <input :checked="i.pk === card.individual" type="checkbox"/> {{i.fio}}<br/>
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
              <tr v-if="i.l2_cards.length > 0">
                <th>Активные карты L2</th>
                <td colspan="2">
                  <div v-for="c in i.l2_cards"><strong>{{c}}</strong></div>
                </td>
              </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="row" v-else>
        <div class="col-xs-12">
          <div class="info-row">
            Связь с РМИС – {{card.has_rmis_card ? 'ЕСТЬ' : 'НЕТ'}}
            <strong v-if="card.has_rmis_card">{{card.rmis_uid}}</strong>
            <a href="#" class="a-under" @click.prevent="sync_rmis" tabindex="-1">синхронизировать</a>
          </div>
        </div>
      </div>
      <div class="row" v-if="card_pk < 0">
        <div class="col-xs-12 text-center">
          Для настройки документов и других параметров сохраните карту
        </div>
      </div>
      <div v-else>
        <div class="row" style="margin-bottom: 10px">
          <div class="col-xs-12 col-form mid">
            <div class="form-row sm-f">
                <div class="row-t">Адрес регистрации</div>
                <TypeAhead :delayTime="400" :getResponse="getResponse"
                           :highlighting="highlighting" :limit="10"
                           :minChars="4" :onHit="onHit('main_address', true)" :selectFirst="true" maxlength="110"
                           ref="ar" :src="`/api/autocomplete?value=:keyword&type=fias`" v-model="card.main_address"
                />
            </div>
            <div class="form-row sm-f">
              <div class="row-t">Адрес проживания</div>
              <TypeAhead :delayTime="400" :getResponse="getResponse"
                         :highlighting="highlighting" :limit="10"
                         :minChars="4" :onHit="onHit('fact_address', true)" :selectFirst="true" maxlength="110"
                         ref="af" :src="`/api/autocomplete?value=:keyword&type=fias`" v-model="card.fact_address"
              />
            </div>
            <div class="form-row sm-f">
              <div class="row-t">Участок</div>
              <select v-model="card.district" class="form-control"
                      style="width: 65%;border: none;height: 26px;">
                <option v-for="c in card.districts" :value="c.id">
                  {{c.title}}
                </option>
              </select>
            </div>
            <div class="form-row sm-f" v-if="card.sex === 'ж'">
              <div class="row-t">Гинекологический участок</div>
              <select v-model="card.ginekolog_district" class="form-control"
                      style="width: 65%;border: none;height: 26px;">
                <option v-for="c in card.gin_districts" :value="c.id">
                  {{c.title}}
                </option>
              </select>
            </div>
            <div class="row">
              <div class="col-xs-6" style="padding-right: 0">
                <div class="form-row nbt-i sm-f">
                  <div class="row-t" style="display: flex;width: 45%;flex: 0 45%;">
                    <input type="checkbox" v-model="card.custom_workplace" title="Ручной ввод названия"
                           v-tippy="{ placement : 'bottom', arrow: true }"
                           style="height: auto;flex: 0 23px;" />
                    Место работы
                  </div>
                  <TypeAhead v-if="card.custom_workplace"
                             :delayTime="100" :getResponse="getResponse"
                             :highlighting="highlighting" :limit="10"
                             :minChars="1" :onHit="onHit('work_place')" :selectFirst="true" maxlength="36"
                             ref="wp" src="/api/autocomplete?value=:keyword&type=work_place" v-model="card.work_place"
                  />
                  <select v-else v-model="card.work_place_db" class="form-control"
                          style="width: 55%;border: none;height: 26px;">
                    <option v-for="c in card.av_companies" :value="c.id">
                      {{c.short_title === '' ? c.title : c.short_title}}
                    </option>
                  </select>
                </div>
              </div>
              <div class="col-xs-6" style="padding-left: 0">
                <div class="form-row nbt-i sm-f">
                  <div class="row-t">Должность</div>
                  <TypeAhead :delayTime="100" :getResponse="getResponse"
                             :highlighting="highlighting" :limit="10"
                             :minChars="1" :onHit="onHit('work_position')" :selectFirst="true" maxlength="36"
                             ref="wp" src="/api/autocomplete?value=:keyword&type=work_position" v-model="card.work_position"
                  />
                </div>
              </div>
            </div>
            <div class="form-row sm-f">
              <div class="row-t">Основной диагноз</div>
              <TypeAhead :delayTime="100" :getResponse="getResponse"
                         :highlighting="highlighting" :limit="10"
                         :minChars="1" :onHit="onHit('main_diagnosis')" :selectFirst="true" maxlength="36"
                         ref="md" src="/api/autocomplete?value=:keyword&type=main_diagnosis" v-model="card.main_diagnosis"
              />
            </div>
          </div>
        </div>
        <table class="table table-bordered table-condensed table-sm-pd">
          <colgroup>
            <col width="70" />
            <col />
            <col />
            <col />
            <col />
            <col />
          </colgroup>
          <thead>
          <tr>
            <th>ПРИОР.</th>
            <th>Тип документа</th>
            <th>Серия</th>
            <th>Номер</th>
            <th>Действие</th>
            <th></th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="d in card.docs" :title="d.who_give"
              :class="{nonPrior: card.main_docs[d.document_type] !== d.id,
            prior: card.main_docs[d.document_type] === d.id}">
            <td>
              <input type="radio" :name="`card-doc${d.document_type}`"
                     @click="update_cdu(d.id)"
                     :checked="card.main_docs[d.document_type] === d.id" />
            </td>
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
            <td class="text-center" colspan="6">
              <a @click.prevent="edit_document(-1)" href="#">добавить документ</a>
            </td>
          </tr>
          </tbody>
        </table>
        <table class="table table-bordered table-condensed table-sm-pd">
          <colgroup>
            <col width="70" />
            <col width="120" />
            <col />
            <col width="150" />
            <col width="40" />
          </colgroup>
          <thead>
          <tr>
            <th>ВЫБОР</th>
            <th>Статус</th>
            <th>ФИО</th>
            <th>Докум.-основание</th>
            <th></th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="t in card.agent_types" :class="{nonPrior: card.who_is_agent !== t.key,
            prior: card.who_is_agent === t.key}" v-if="!card.excluded_types.includes(t.key)">
            <td>
              <input type="radio" name="agent"
                     @click="update_wia(t.key)" v-if="!card.excluded_types.includes(t.key)"
                     :checked="card.who_is_agent === t.key" />
            </td>
            <td>
              {{t.title}}
            </td>
            <td :colspan="agent_need_doc(t.key) ? 1 : 2">{{card[t.key]}}</td>
            <td v-if="agent_need_doc(t.key)">{{card[`${t.key}_doc_auth`]}}</td>
            <td>
              <a @click.prevent="edit_agent(t.key)" href="#"><i class="fa fa-pencil"></i></a>
            </td>
          </tr>
          <tr :class="{nonPrior: card.who_is_agent !== '',
            prior: card.who_is_agent === ''}">
            <td>
              <input type="radio" name="agent"
                     @click="update_wia('')"
                     :checked="card.who_is_agent === ''" />
            </td>
            <td colspan="4">НЕ ВЫБРАНО</td>
          </tr>
          <tr v-for="t in card.agent_types" class="prior" v-if="card.excluded_types.includes(t.key)">
            <td>
            </td>
            <td>
              {{t.title}}
            </td>
            <td :colspan="agent_need_doc(t.key) ? 1 : 2">{{card[t.key]}}</td>
            <td v-if="agent_need_doc(t.key)">{{card[`${t.key}_doc_auth`]}}</td>
            <td>
              <a @click.prevent="edit_agent(t.key)" href="#"><i class="fa fa-pencil"></i></a>
            </td>
          </tr>
          </tbody>
        </table>
        <div class="row" style="margin-bottom: 10px">
          <div class="col-xs-12 col-form mid">
            <div class="form-row sm-f">
                <div class="row-t">Телефон</div>
                <input class="form-control" v-model="card.phone" v-mask="'8 999 9999999'">
            </div>
          </div>
        </div>
        <div class="row" style="margin-bottom: 10px">
          <div class="col-xs-12 col-form mid">
            <div class="form-row sm-f">
                <div class="row-t">Номер карты ТФОМС</div>
                <input class="form-control" v-model="card.number_poli" maxlength="20">
            </div>
          </div>
        </div>
        <div class="row" style="margin-bottom: 10px">
          <div class="col-xs-12 col-form mid">
            <div class="form-row sm-f">
                <div class="row-t">Фактор вредности</div>
                <TypeAhead :delayTime="100" :getResponse="getResponse"
                           :highlighting="highlighting" :limit="10"
                           :minChars="1" :onHit="onHit('harmful')" :selectFirst="true" maxlength="32"
                           ref="n" src="/api/autocomplete?value=:keyword&type=harmful" v-model="card.harmful"
                />
            </div>
          </div>
        </div>
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
          <div class="form-group" v-show="doc_edit_fields.serial">
            <label for="de-f2">Серия (при наличии):</label>
            <input class="form-control" id="de-f2" v-model="document.serial">
          </div>
          <div class="form-group" v-show="is_snils">
            <label for="de-f3">Номер СНИЛС:</label>
            <input class="form-control" id="de-f3" v-model="document.number" v-if="is_snils"
                   v-mask="doc_edit_fields.masks.number">
          </div>
          <div class="form-group" v-show="!is_snils">
            <label for="de-f3-2">Номер:</label>
            <input class="form-control" id="de-f3-2" v-model="document.number">
          </div>
          <div class="form-group" v-show="doc_edit_fields.dates">
            <label for="de-f4">Дата выдачи:</label>
            <input class="form-control" type="date" id="de-f4" v-model="document.date_start">
          </div>
          <div class="form-group" v-show="doc_edit_fields.dates">
            <label for="de-f5">Дата окончания:</label>
            <input class="form-control" type="date" id="de-f5" v-model="document.date_end">
          </div>
          <div class="form-group str" v-show="doc_edit_fields.who_give">
            <label>Выдал:</label>
            <TypeAhead :delayTime="100" :getResponse="getResponse"
                       :highlighting="highlighting" :limit="10"
                       :minChars="1" :onHit="onHitDocWhoGive" :selectFirst="true" maxlength="36"
                       ref="dwg" :src="`/api/autocomplete?value=:keyword&type=who_give:` + document.document_type" v-model="document.who_give"
            />
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
      <modal v-if="agent_to_edit" ref="modalAgentEdit" @close="hide_modal_agent_edit" show-footer="true" white-bg="true" max-width="710px" width="100%" marginLeftRight="auto" margin-top>
        <span slot="header">Редактор – {{agent_type_by_key(agent_to_edit)}} (карта {{card.number}} пациента {{card.family}} {{card.name}} {{card.patronymic}})</span>
        <div slot="body" style="min-height: 140px" class="registry-body">
          <div v-show="!agent_clear">
            <div style="height: 110px">
              <patient-small-picker v-model="agent_card_selected" :base_pk="base_pk" />
            </div>
            <div class="form-group" v-if="agent_need_doc(agent_to_edit)" style="padding: 10px">
              <label for="ae-f2">Документ-основание:</label>
              <input class="form-control" id="ae-f2" v-model="agent_doc">
            </div>
          </div>
          <div class="checkbox" style="padding-left: 35px;padding-top: 10px" v-if="!!card[agent_to_edit]">
            <label>
              <input type="checkbox" v-model="agent_clear"> очистить представителя ({{agent_type_by_key(agent_to_edit)}})
            </label>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button @click="hide_modal_agent_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
                Отмена
              </button>
            </div>
            <div class="col-xs-4">
              <button :disabled="!valid_agent" @click="save_agent()" class="btn btn-primary-nb btn-blue-nb" type="button">
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </modal>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-3">
          <div class="dropup" v-if="card_pk >= 0">
            <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                    style="width: 100%">
              Печатн. формы <span class="caret"></span>
            </button>
            <ul class="dropdown-menu">
              <li v-for="f in forms">
                <a :href="f.url" target="_blank" class="ddm">{{f.title}}</a>
              </li>
            </ul>
          </div>
        </div>
        <div class="col-xs-2">
          <button @click="hide_modal" class="btn btn-primary-nb btn-blue-nb" type="button">
            Закрыть
          </button>
        </div>
        <div class="col-xs-3">
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
  import Modal from '../ui-cards/Modal'
  import patients_point from '../api/patients-point'
  import PatientSmallPicker from '../ui-cards/PatientSmallPicker'
  import * as action_types from '../store/action-types'
  import RadioField from '../fields/RadioField'
  import TypeAhead from 'vue2-typeahead'
  import moment from 'moment'
  import forms from '../forms'

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
    components: {Modal, TypeAhead, PatientSmallPicker, RadioField},
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
        sexes: [
            'м',
            'ж',
        ],
        card: {
          number: '',
          number_poli: '',
          main_address: "",
          fact_address: "",
          work_place: "",
          work_position: "",
          family: "",
          patronymic: "",
          name: "",
          main_diagnosis: "",
          sex: "м",
          has_rmis_card: false,
          birthday: moment().format('YYYY-MM-DD'),
          individual: -1,
          new_individual: false,
          custom_workplace: false,
          docs: [],
          docs_to_delete: [],
          rmis_uid: null,
          work_place_db: null,
          doc_types: [],
          av_companies: [],
          main_docs: {},
          districts: [],
          district: -1,
          gin_districts: [],
          ginekolog_district: -1,
          agent_types: [],
          agent_need_doc: [],
          excluded_types: [],
          who_is_agent: "",
          mother: null,
          mother_pk: null,
          father: null,
          father_pk: null,
          curator: null,
          curator_doc: null,
          curator_pk: null,
          agent: null,
          agent_doc: null,
          agent_pk: null,
          phone: '',
          harmful: '',
        },
        individuals: [],
        document_to_edit: -2,
        document: {
          number: ''
        },
        agent_to_edit: null,
        agent_card_selected: null,
        agent_doc: '',
        agent_clear: false,
      }
    },
    created() {
      this.load_data()
      this.$root.$on('reload_editor', () => {
        this.load_data()
      })
    },
    computed: {
      doc_edit_type_title() {
        const t = this.document.document_type;
        if (!t)
          return '';
        return (this.card.doc_types.find(x => x.pk === t) || {}).title || '';
      },
      is_snils() {
        const tt = this.doc_edit_type_title;
        return tt === 'СНИЛС'
      },
      doc_edit_fields() {
        const tt = this.doc_edit_type_title;
        return {
          serial: tt !== 'СНИЛС',
          dates: tt !== 'СНИЛС',
          who_give: tt !== 'СНИЛС',
          masks: {
            number: tt === 'СНИЛС' ? '999-999-999 99' : undefined,
          }
        };
      },
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
        if (!this.card.family || !this.card.name || !this.card.birthday) {
          return false;
        }
        return !!(this.card.family.length > 0
          && this.card.name.length > 0 && this.card.birthday.match(/\d{4}-\d{2}-\d{2}/gm));
      },
      birthday() {
        return this.card.birthday
      },
      valid_doc() {
        if (this.doc_edit_type_title === 'СНИЛС') {
          return /^\d\d\d-\d\d\d-\d\d\d \d\d$/gm.test(this.document.number) && validateSnils(this.document.number);
        }
        return this.document.number.length > 0;
      },
      valid_agent() {
        if (this.agent_clear)
          return true;
        return this.agent_card_selected && this.agent_card_selected !== this.card_pk;
      },
      forms() {
        return forms.map(f => {
          return {...f, url: f.url.kwf({
              card: this.card_pk,
              individual: this.card.individual,
            })}
        });
      },
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
      agent_type_by_key(key) {
        for (const t of this.card.agent_types) {
          if (t.key === key) {
            return t.title;
          }
        }
        return 'НЕ ВЫБРАНО';
      },
      agent_need_doc(key) {
        return this.card.agent_need_doc.includes(key);
      },
      select_individual(invpk) {
        this.card.individual = invpk
      },
      toggleNewIndividual() {
        this.card.new_individual = !this.card.new_individual
      },
      hide_modal() {
        this.$root.$emit('hide_l2_card_create')
        if (this.$refs.modal) {
          this.$refs.modal.$el.style.display = 'none'
        }
      },
      save_hide_modal() {
        this.save(true)
      },
      save(hide_after = false) {
        if (!this.valid) {
          return
        }
        (async () => {
          await this.$store.dispatch(action_types.INC_LOADING)
          const data = await patients_point.sendCard(this.card,
            ['family', 'name', 'patronymic', 'birthday', 'sex', 'new_individual', 'base_pk',
              'fact_address', 'main_address', 'work_place', 'main_diagnosis', 'work_position', 'work_place_db',
              'custom_workplace', 'district', 'phone', 'number_poli', 'harmful'], {
              card_pk: this.card_pk, individual_pk: this.card.individual, gin_district: this.card.ginekolog_district,
              base_pk: this.base_pk,
            })
          if (data.result !== 'ok') {
              errmessage('Сохранение прошло не удачно')
            return
          }
          if (Array.isArray(data.messages)) {
              for (const msg of data.messages) {
                  wrnmessage('Warning', msg)
              }
          }
          okmessage('Данные сохранены')
          if (hide_after) {
            this.hide_modal()
          }
          this.$root.$emit('select_card', {
            card_pk: data.card_pk,
            base_pk: this.base_pk,
            hide: hide_after,
          })
        })().then().finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      update_cdu(doc) {
        (async () => {
          await this.$store.dispatch(action_types.INC_LOADING)
          await patients_point.updateCdu({card_pk: this.card_pk, doc})
          this.load_data();
          okmessage('Изменения сохранены');
        })().then().finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      update_wia(key) {
        (async () => {
          await this.$store.dispatch(action_types.INC_LOADING)
          await patients_point.updateWIA({card_pk: this.card_pk, key})
          this.load_data();
          okmessage('Изменения сохранены');
        })().then().finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      edit_agent(key) {
        this.agent_card_selected = this.card[`${key}_pk`]
        this.agent_doc = this.card[`${key}_doc_auth`] || ''
        this.agent_clear = false
        this.agent_to_edit = key;
      },
      sync_rmis() {
        (async () => {
          await this.$store.dispatch(action_types.INC_LOADING)
          await patients_point.syncRmis(this, 'card_pk')
          this.load_data();
        })().then().finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      getResponse(resp) {
        return [...resp.data.data]
      },
      onHitDocWhoGive(item) {
        if (!item) {
          return
        }
        this.document.who_give = item
      },
      onHit(name, no_next) {
        return (item, t) => {
          if (t.$el) {
            if (no_next) {
              $('input', t.$el).focus();
            } else {
              let index = $('input', this.$el).index($('input', t.$el)) + 1;
              $('input', this.$el).eq(index).focus();
            }
          }
          if (!item) {
            return;
          }
          this.card[name] = item;
        }
      },
      highlighting: (item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`),
      load_data() {
        if (this.card_pk === -1) {
          return;
        }
        this.loaded = false
        this.$store.dispatch(action_types.INC_LOADING).then()
        patients_point.getCard(this, 'card_pk').then(data => {
          this.card = data
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
          this.loaded = true
        })
      },
      individuals_search() {
        if (!this.valid) {
          return
        }
        patients_point.individualsSearch(this.card, ['family', 'name', 'patronymic', 'birthday', 'sex'])
          .then(({result}) => {
          this.individuals = result
          this.card.individual = result.length === 0 ? -1 : result[0].pk
          this.card.new_individual = result.length === 0
        })
      },
      individual_sex(t, v) {
        if (this.card_pk >= 0) {
          return
        }
        patients_point.individualSex({t, v}).then(({sex}) => {
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
          date_start: null,
          date_end: null,
          who_give: null,
          ...(this.card.docs.find(x => x.id === pk) || {})
        };
        this.document_to_edit = pk
      },
      hide_modal_doc_edit() {
        if (this.$refs.modalDocEdit) {
          this.$refs.modalDocEdit.$el.style.display = 'none'
        }
        this.document_to_edit = -2
      },
      hide_modal_agent_edit() {
        if (this.$refs.modalAgentEdit) {
          this.$refs.modalAgentEdit.$el.style.display = 'none';
        }
        this.agent_to_edit = null;
      },
      save_doc() {
        if (!this.valid_doc) {
          return
        }
        (async () => {
          await this.$store.dispatch(action_types.INC_LOADING)
          await patients_point.editDoc(this.document,
            ['serial', 'number', 'is_active', 'date_start', 'date_end', 'who_give'],
            {
              card_pk: this.card_pk,
              pk: this.document_to_edit,
              type: this.document.document_type,
              individual_pk: this.card.individual,
            })
          this.load_data();
          this.document = {
            number: ''
          };
          this.hide_modal_doc_edit();
        })().then().finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      save_agent() {
        if (!this.valid_agent) {
          return
        }
        (async () => {
          await this.$store.dispatch(action_types.INC_LOADING)
          await patients_point.editAgent({
            key: this.agent_to_edit,
            parent_card_pk: this.card_pk,
            card_pk: this.agent_card_selected,
            doc: this.agent_doc,
            clear: this.agent_clear,
          })
          this.load_data();
          this.hide_modal_agent_edit();
        })().then().finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
        })
      }
    }
  }
</script>

<style scoped lang="scss">
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
      padding-right: 0!important;

      .row-t, input, .row-v, /deep/ input {
        border-right: 1px solid #434a54 !important;
      }

      .form-row .input-group {
        width: 65%;
      }
    }
    &:not(.left):not(.mid) {
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
  .str /deep/ .input-group {
    width: 100%;
  }

  .lst {
    margin: 0;
    line-height: 1;
  }
</style>
