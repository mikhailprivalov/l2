<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="680px" width="100%"
         marginLeftRight="auto" margin-top>
    <span slot="header">Регистратура L2</span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <form autocomplete="off" class="row" onsubmit.prevent>
        <input type="hidden" autocomplete="off" />
        <div class="col-xs-6 col-form left">
          <div class="form-row">
            <div class="row-t">Фамилия</div>
            <TypeAhead :delayTime="100" :getResponse="getResponse"
                       :highlighting="highlighting" :limit="10"
                       name="f"
                       :minChars="1" :onHit="onHit('family')" :selectFirst="true" maxlength="36"
                       ref="f" src="/api/autocomplete?value=:keyword&type=family" v-model="card.family"
            />
          </div>
          <div class="form-row">
            <div class="row-t">Имя</div>
            <TypeAhead :delayTime="100" :getResponse="getResponse" :highlighting="highlighting"
                       :limit="10"
                       name="n"
                       :minChars="1" :onHit="onHit('name')" :selectFirst="true" maxlength="36"
                       ref="n" src="/api/autocomplete?value=:keyword&type=name" v-model="card.name"
            />
          </div>
          <div class="form-row">
            <div class="row-t">Отчество</div>
            <TypeAhead :delayTime="100" :getResponse="getResponse"
                       :highlighting="highlighting" :limit="10"
                       name="pn"
                       :minChars="1" :onHit="onHit('patronymic')" :selectFirst="true" maxlength="36"
                       ref="pn" src="/api/autocomplete?value=:keyword&type=patronymic" v-model="card.patronymic"
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
            <radio-field v-model="card.sex" :variants="GENDERS" fullWidth/>
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
          <div class="info-row" v-if="loading">
            Поиск пациентов в L2<template v-if="l2_tfoms"> и в ТФОМС</template>...
          </div>
          <div class="info-row" v-else>
            Найдено физлиц в L2<template v-if="l2_tfoms"> и ТФОМС</template>: {{individuals.length}}
          </div>
        </div>
        <div class="col-xs-12"
             v-if="!card.new_individual && individuals.map(i => i.l2_cards.length).reduce((a, b) => a + b, 0) > 0">
          <div class="alert-warning" style="padding: 10px">
            <strong>Внимание:</strong> найдены существующие карты или созданы автоматически.<br />
            Выберите подходящую, нажав на номер карты или продолжайте создание новой при необходимости
            или не совпадении физ. лиц
          </div>
        </div>
        <div class="col-xs-12" v-if="!card.new_individual && individuals.length > 0">
          <div @click="select_individual(i.pk)" class="info-row individual" v-for="i in individuals" :key="i.pk">
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
              <tr v-for="d in i.docs" :key="`${d.type_title}_${d.serial}_${d.number}`">
                <td>{{d.type_title}}</td>
                <td>{{d.serial}}</td>
                <td>{{d.number}}</td>
              </tr>
              <tr v-if="i.l2_cards.length > 0">
                <th>Активные карты L2</th>
                <td colspan="2">
                  <div v-for="c in i.l2_cards" :key="c.pk">
                    <a :href="`/mainmenu/directions?card_pk=${c.pk}&base_pk=${base_pk}&open_edit=true`" class="a-under c-pointer"
                        title="Открыть существующую карту" v-tippy>
                      <strong>{{c.number}}</strong>
                    </a>
                  </div>
                </td>
              </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="row" v-else>
        <div class="col-xs-6" v-if="l2_tfoms">
          <div class="info-row">
            <template v-if="card.tfoms_idp || card.tfoms_enp">Есть связь с ТФОМС</template>
            <template v-else>Не связано с ТФОМС</template>
            <template v-if="time_tfoms_last_sync">({{time_tfoms_last_sync}})</template>
            <a href="#" class="a-under" @click.prevent="sync_tfoms" tabindex="-1">сверка</a>
          </div>
        </div>
        <div class="text-right" :class="{'col-xs-6': l2_tfoms, 'col-xs-12': !l2_tfoms}">
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
                         name="ar"
                         :minChars="4" :onHit="onHit('main_address', true)" :selectFirst="true" maxlength="110"
                         ref="ar" :src="`/api/autocomplete?value=:keyword&type=fias`" v-model="card.main_address"
              />
            </div>
            <div class="form-row sm-f">
              <div class="row-t">Адрес проживания</div>
              <TypeAhead :delayTime="400" :getResponse="getResponse"
                         :highlighting="highlighting" :limit="10"
                         name="af"
                         :minChars="4" :onHit="onHit('fact_address', true)" :selectFirst="true" maxlength="110"
                         ref="af" :src="`/api/autocomplete?value=:keyword&type=fias`" v-model="card.fact_address"
              />
            </div>
            <div class="form-row sm-f">
              <div class="row-t">Участок</div>
              <select v-model="card.district" class="form-control">
                <option v-for="c in card.districts" :value="c.id" :key="c.id">
                  {{c.title}}
                </option>
              </select>
            </div>
            <div class="form-row sm-f" v-if="card.sex === 'ж'">
              <div class="row-t">Гинекологический участок</div>
              <select v-model="card.ginekolog_district" class="form-control">
                <option v-for="c in card.gin_districts" :value="c.id" :key="c.id">
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
                           style="height: auto;flex: 0 23px;"/>
                    Место работы
                  </div>
                  <TypeAhead v-if="card.custom_workplace"
                             :delayTime="100" :getResponse="getResponse"
                             :highlighting="highlighting" :limit="10"
                             :minChars="1" :onHit="onHit('work_place')" :selectFirst="true" maxlength="128"
                             ref="wp" src="/api/autocomplete?value=:keyword&type=work_place" v-model="card.work_place"
                  />
                  <div style="width: 55%;" v-else>
                    <treeselect class="treeselect-noborder treeselect-26px"
                                :multiple="false" :disable-branch-nodes="true" :append-to-body="true" :zIndex="99999"
                                :options="companiesTreeselect(card.av_companies)" placeholder="НЕ ВЫБРАНО"
                                v-model="card.work_place_db"
                    />
                  </div>
                </div>
              </div>
              <div class="col-xs-6" style="padding-left: 0">
                <div class="form-row nbt-i sm-f">
                  <div class="row-t">Должность</div>
                  <TypeAhead :delayTime="100" :getResponse="getResponse"
                             :highlighting="highlighting" :limit="10"
                             :minChars="1" :onHit="onHit('work_position')" :selectFirst="true" maxlength="128"
                             ref="wpos" src="/api/autocomplete?value=:keyword&type=work_position"
                             v-model="card.work_position"
                  />
                </div>
              </div>
            </div>
            <div class="form-row sm-f">
              <div class="row-t">Основной диагноз</div>
              <TypeAhead :delayTime="100" :getResponse="getResponse"
                         :highlighting="highlighting" :limit="10"
                         :minChars="1" :onHit="onHit('main_diagnosis')" :selectFirst="true" maxlength="36"
                         ref="md" src="/api/autocomplete?value=:keyword&type=main_diagnosis"
                         v-model="card.main_diagnosis"
              />
            </div>
          </div>
        </div>
        <table class="table table-bordered table-condensed table-sm-pd">
          <colgroup>
            <col width="70"/>
            <col/>
            <col/>
            <col/>
            <col/>
            <col/>
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
          <tr v-for="d in card.docs" :title="d.who_give" :key="d.id"
              :class="{nonPrior: card.main_docs[d.document_type] !== d.id,
            prior: card.main_docs[d.document_type] === d.id}">
            <td>
              <input type="radio" :name="`card-doc${d.document_type}`"
                     @click="update_cdu(d.id)"
                     :checked="card.main_docs[d.document_type] === d.id"/>
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
              <span v-else>импорт</span>
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
            <col width="70"/>
            <col width="120"/>
            <col/>
            <col width="150"/>
            <col width="40"/>
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
          <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
          <tr v-for="t in card.agent_types" v-if="!card.excluded_types.includes(t.key)" :key="t.key"
              :class="{nonPrior: card.who_is_agent !== t.key, prior: card.who_is_agent === t.key}">
            <td>
              <input type="radio" name="agent"
                     @click="update_wia(t.key)" v-if="!card.excluded_types.includes(t.key)"
                     :checked="card.who_is_agent === t.key"/>
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
                     :checked="card.who_is_agent === ''"/>
            </td>
            <td colspan="4">НЕ ВЫБРАНО</td>
          </tr>
          <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
          <tr v-for="t in card.agent_types" :key="t.key" class="prior" v-if="card.excluded_types.includes(t.key)">
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
                         :minChars="1" :onHit="onHit('harmful')" :selectFirst="true" maxlength="255"
                         ref="n" src="/api/autocomplete?value=:keyword&type=harmful" v-model="card.harmful"
              />
            </div>
          </div>
        </div>
        <div class="input-group" style="margin-bottom: 10px" v-if="can_change_owner_directions">
          <div class="input-group-btn">
            <button type="button" class="btn btn-blue-nb nbr" @click="change_directions_owner()">
              Перенести все услуги в другую карту
              <i class="glyphicon glyphicon-arrow-right"></i>
            </button>
          </div>
          <input type="text" class="form-control" placeholder="Введите номер карты" v-model="new_card_num">
        </div>
      </div>
      <modal v-if="document_to_edit > -2" ref="modalDocEdit" @close="hide_modal_doc_edit" show-footer="true"
             white-bg="true" max-width="710px" width="100%" marginLeftRight="auto" margin-top>
        <!-- eslint-disable-next-line max-len -->
        <span slot="header">Редактор документов (карта {{card.number}} пациента {{card.family}} {{card.name}} {{card.patronymic}})</span>
        <div slot="body" style="min-height: 200px;padding: 10px" class="registry-body">
          <div class="form-group">
            <label>Тип документа:</label>
            <select v-if="document_to_edit === -1" v-model="document.document_type">
              <option v-for="dt in card.doc_types" :value="dt.pk" :key="dt.pk">{{dt.title}}</option>
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
                       :minChars="1" :onHit="onHitDocWhoGive" :selectFirst="true" maxlength="128"
                       ref="dwg" :src="`/api/autocomplete?value=:keyword&type=who_give:` + document.document_type"
                       v-model="document.who_give"
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
      <modal v-if="agent_to_edit" ref="modalAgentEdit" @close="hide_modal_agent_edit" show-footer="true" white-bg="true"
             max-width="710px" width="100%" marginLeftRight="auto" margin-top>
        <!-- eslint-disable-next-line max-len -->
        <span slot="header">Редактор – {{agent_type_by_key(agent_to_edit)}} (карта {{card.number}} пациента {{card.family}} {{card.name}} {{card.patronymic}})</span>
        <div slot="body" style="min-height: 140px" class="registry-body">
          <div v-show="!agent_clear">
            <div style="height: 110px">
              <patient-small-picker v-model="agent_card_selected" :base_pk="base_pk"/>
            </div>
            <div class="form-group" v-if="agent_need_doc(agent_to_edit)" style="padding: 10px">
              <label for="ae-f2">Документ-основание:</label>
              <input class="form-control" id="ae-f2" v-model="agent_doc">
            </div>
          </div>
          <div class="checkbox" style="padding-left: 35px;padding-top: 10px" v-if="!!card[agent_to_edit]">
            <label>
              <input type="checkbox" v-model="agent_clear"> очистить представителя
              ({{agent_type_by_key(agent_to_edit)}})
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
              <button :disabled="!valid_agent" @click="save_agent()" class="btn btn-primary-nb btn-blue-nb"
                      type="button">
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
              <li v-for="f in forms" :key="f.url">
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
import TypeAhead from 'vue2-typeahead';
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { normalizeNamePart, swapLayouts, validateSnils } from '@/utils';
import { GENDERS } from '@/constants';
import api from '@/api';
import _ from 'lodash';
import patientsPoint from '../api/patients-point';
import Modal from '../ui-cards/Modal.vue';
import forms from '../forms';
import RadioField from '../fields/RadioField.vue';
import * as actions from '../store/action-types';
import PatientSmallPicker from '../ui-cards/PatientSmallPicker.vue';

export default {
  name: 'l2-card-create',
  components: {
    Modal, TypeAhead, PatientSmallPicker, RadioField, Treeselect,
  },
  props: {
    card_pk: {
      type: Number,
      required: true,
    },
    base_pk: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      GENDERS,
      card: {
        number: '',
        number_poli: '',
        main_address: '',
        fact_address: '',
        work_place: '',
        work_position: '',
        family: '',
        patronymic: '',
        name: '',
        main_diagnosis: '',
        sex: GENDERS[0],
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
        who_is_agent: '',
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
        tfoms_idp: null,
        tfoms_enp: null,
        time_tfoms_last_sync: null,
      },
      individuals: [],
      document_to_edit: -2,
      document: {
        number: '',
      },
      agent_to_edit: null,
      agent_card_selected: null,
      agent_doc: '',
      agent_clear: false,
      loading: false,
      new_card_num: '',
    };
  },
  created() {
    this.load_data();
    this.$root.$on('reload_editor', () => {
      this.load_data();
    });
  },
  updated() {
    // Костыль, что бы не вылезал автокомплит полей от браузера
    const {
      f, n, pn, ar, af,
    } = this.$refs;
    setTimeout(() => {
      for (const r of [f, n, pn, ar, af]) {
        if (r) {
          const inp = window.$('input', r.$el);
          inp.attr('autocomplete', 'new-password');
        }
      }
    }, 100);
  },
  computed: {
    l2_tfoms() {
      return this.$store.getters.modules.l2_tfoms;
    },
    doc_edit_type_title() {
      const t = this.document.document_type;
      if (!t) return '';
      return (this.card.doc_types.find((x) => x.pk === t) || {}).title || '';
    },
    is_snils() {
      const tt = this.doc_edit_type_title;
      return tt === 'СНИЛС';
    },
    doc_edit_fields() {
      const tt = this.doc_edit_type_title;
      return {
        serial: tt !== 'СНИЛС',
        dates: tt !== 'СНИЛС',
        who_give: tt !== 'СНИЛС',
        masks: {
          number: tt === 'СНИЛС' ? '999-999-999 99' : undefined,
        },
      };
    },
    family() {
      return this.card.family;
    },
    name() {
      return this.card.name;
    },
    patronymic() {
      return this.card.patronymic;
    },
    sex() {
      return this.card.sex;
    },
    new_individual() {
      return this.card.new_individual;
    },
    time_tfoms_last_sync() {
      return this.card.time_tfoms_last_sync && moment(this.card.time_tfoms_last_sync).format('HH:mm DD.MM.YY');
    },
    valid() {
      if (!this.card.family || !this.card.name || !this.card.birthday) {
        return false;
      }
      return !!(this.card.family.length > 0
          && this.card.name.length > 0 && this.card.birthday.match(/\d{4}-\d{2}-\d{2}/gm));
    },
    birthday() {
      return this.card.birthday;
    },
    valid_doc() {
      if (this.doc_edit_type_title === 'СНИЛС') {
        return /^\d\d\d-\d\d\d-\d\d\d \d\d$/gm.test(this.document.number) && validateSnils(this.document.number);
      }
      return this.document.number.length > 0;
    },
    valid_agent() {
      if (this.agent_clear) return true;
      return this.agent_card_selected && this.agent_card_selected !== this.card_pk;
    },
    forms() {
      return forms.map((f) => ({
        ...f,
        url: f.url.kwf({
          card: this.card_pk,
          individual: this.card.individual,
        }),
      }));
    },
    can_change_owner_directions() {
      return (this.$store.getters.user_data.groups || []).includes('Управление иерархией истории');
    },
  },
  watch: {
    sex() {
      let s = swapLayouts(this.card.sex.toLowerCase());
      if (s.length > 1) {
        // eslint-disable-next-line prefer-destructuring
        s = s[0];
      }
      if (s !== 'м' && s !== 'ж') {
        s = 'м';
      }
      this.card.sex = s;
      this.individuals_search();
    },
    family() {
      this.card.family = normalizeNamePart(this.card.family);
      this.individuals_search();
      this.individual_sex('family', this.card.family);
    },
    name() {
      this.card.name = normalizeNamePart(this.card.name);
      this.individuals_search();
      this.individual_sex('name', this.card.name);
    },
    patronymic() {
      this.card.patronymic = normalizeNamePart(this.card.patronymic);
      this.individuals_search();
      this.individual_sex('patronymic', this.card.patronymic);
    },
    birthday() {
      this.individuals_search();
    },
    new_individual() {
      this.individuals_search();
    },
    individuals: {
      deep: true,
      handler(nv) {
        if (nv.length === 0) {
          this.card.new_individual = true;
        }
      },
    },
  },
  methods: {
    companiesTreeselect(companies) {
      return companies.map((c) => ({ id: c.id, label: c.short_title || c.title }));
    },
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
      this.card.individual = invpk;
    },
    toggleNewIndividual() {
      this.card.new_individual = !this.card.new_individual;
    },
    hide_modal() {
      this.$root.$emit('hide_l2_card_create');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    save_hide_modal() {
      this.save(true);
    },
    async save(hide_after = false) {
      if (!this.valid) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await patientsPoint.sendCard(this.card,
        ['family', 'name', 'patronymic', 'birthday', 'sex', 'new_individual', 'base_pk',
          'fact_address', 'main_address', 'work_place', 'main_diagnosis', 'work_position', 'work_place_db',
          'custom_workplace', 'district', 'phone', 'number_poli', 'harmful'], {
          card_pk: this.card_pk,
          individual_pk: this.card.individual,
          gin_district: this.card.ginekolog_district,
          base_pk: this.base_pk,
        });
      if (data.result !== 'ok') {
        window.errmessage('Сохранение прошло не удачно');
        return;
      }
      if (Array.isArray(data.messages)) {
        for (const msg of data.messages) {
          window.wrnmessage('Warning', msg);
        }
      }
      window.okmessage('Данные сохранены');
      this.$root.$emit('update_card_data');
      if (hide_after) {
        this.hide_modal();
      }
      this.update_card(hide_after, data);
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    update_card(hide_after = false, data = null) {
      if (this.card_pk < 0) {
        return;
      }
      this.$root.$emit('select_card', {
        card_pk: data ? data.card_pk : this.card_pk,
        base_pk: this.base_pk,
        hide: hide_after,
      });
    },
    async update_cdu(doc) {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.updateCdu({ card_pk: this.card_pk, doc });
      await this.load_data();
      window.okmessage('Изменения сохранены');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async update_wia(key) {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.updateWIA({ card_pk: this.card_pk, key });
      await this.load_data();
      window.okmessage('Изменения сохранены');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    edit_agent(key) {
      this.agent_card_selected = this.card[`${key}_pk`];
      this.agent_doc = this.card[`${key}_doc_auth`] || '';
      this.agent_clear = false;
      this.agent_to_edit = key;
    },
    async sync_rmis() {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.syncRmis(this, 'card_pk');
      await this.load_data();
      this.update_card();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async sync_tfoms() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { updated } = await patientsPoint.syncTfoms(this, 'card_pk');
      await this.load_data();
      this.update_card();
      window.okmessage('Сверка проведена');
      if (updated && updated.length > 0) {
        window.okmessage('Обновлены данные', updated.join(', '));
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    getResponse(resp) {
      return [...resp.data.data];
    },
    onHitDocWhoGive(item) {
      if (!item) {
        return;
      }
      this.document.who_give = item;
    },
    onHit(name, no_next) {
      return (item, t) => {
        if (t.$el) {
          if (no_next) {
            window.$('input', t.$el).focus();
          } else {
            const index = window.$('input', this.$el).index(window.$('input', t.$el)) + 1;
            window.$('input', this.$el).eq(index).focus();
          }
        }
        if (!item) {
          return;
        }
        this.card[name] = item;
      };
    },
    highlighting: (item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`),
    load_data() {
      if (this.card_pk === -1) {
        return Promise.resolve({});
      }
      this.loaded = false;
      this.$store.dispatch(actions.INC_LOADING);
      return patientsPoint.getCard(this, 'card_pk').then((data) => {
        this.card = data;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.loaded = true;
      });
    },
    individuals_search: _.debounce(function () { this.individuals_search_main(); }, 500),
    async individuals_search_main() {
      if (!this.valid || this.card_pk !== -1
            || this.card.family === '' || this.card.name === '' || this.card.new_individual) {
        return;
      }

      this.loading = true;

      const {
        result, forced_gender,
      } = await patientsPoint.individualsSearch(this.card, ['family', 'name', 'patronymic', 'birthday']);

      this.individuals = result;
      this.card.individual = result.length === 0 ? -1 : result[0].pk;
      this.card.new_individual = result.length === 0;
      if (forced_gender) {
        this.card.sex = forced_gender;
      }

      this.loading = false;
    },
    individual_sex(t, v) {
      if (this.card_pk >= 0) {
        return;
      }
      patientsPoint.individualSex({ t, v }).then(({ sex }) => {
        this.card.sex = sex;
      });
    },
    edit_document(pk) {
      this.document = {
        document_type: this.card.doc_types[0].pk,
        is_active: true,
        number: '',
        serial: '',
        type_title: null,
        date_start: null,
        date_end: null,
        who_give: null,
        ...(this.card.docs.find((x) => x.id === pk) || {}),
      };
      this.document_to_edit = pk;
    },
    hide_modal_doc_edit() {
      if (this.$refs.modalDocEdit) {
        this.$refs.modalDocEdit.$el.style.display = 'none';
      }
      this.document_to_edit = -2;
    },
    hide_modal_agent_edit() {
      if (this.$refs.modalAgentEdit) {
        this.$refs.modalAgentEdit.$el.style.display = 'none';
      }
      this.agent_to_edit = null;
    },
    async save_doc() {
      if (!this.valid_doc) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.editDoc(this.document,
        ['serial', 'number', 'is_active', 'date_start', 'date_end', 'who_give'],
        {
          card_pk: this.card_pk,
          pk: this.document_to_edit,
          type: this.document.document_type,
          individual_pk: this.card.individual,
        });
      await this.load_data();
      this.document = {
        number: '',
      };
      this.hide_modal_doc_edit();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async save_agent() {
      if (!this.valid_agent) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.editAgent({
        key: this.agent_to_edit,
        parent_card_pk: this.card_pk,
        card_pk: this.agent_card_selected,
        doc: this.agent_doc,
        clear: this.agent_clear,
      });
      await this.load_data();
      this.hide_modal_agent_edit();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async change_directions_owner() {
      const { ok, individual_fio } = await api('patients/is-card', {
        number: this.new_card_num,
      });
      if (!ok) {
        window.errmessage('Карта не найдена');
        return;
      }
      try {
        // eslint-disable-next-line max-len
        await this.$dialog.confirm(`Перенести все услуги из карты № ${this.card.number}-${this.card.family} ${this.card.name} ${this.card.patronymic}) в карту № ${this.new_card_num} -${individual_fio} ?`);
      } catch (e) {
        // pass
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await api('directions/change-owner-direction', {
        old_card_number: this.card.number,
        new_card_number: this.new_card_num,
      });
      window.okmessage('Направления успешно перенесены');
      window.okmessage('Номера: ', data.directions);
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
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

  ::v-deep .panel-flt {
    margin: 41px;
    align-self: stretch !important;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  ::v-deep .panel-body {
    flex: 1;
    padding: 0;
    height: calc(100% - 91px);
    min-height: 200px;
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

  .str ::v-deep .input-group {
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
