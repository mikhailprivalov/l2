<template>
  <div v-if="card_pk === -1" class="empty">
    <div>Пациент не выбран</div>
  </div>
  <div v-else class="root">
    <div class="col-form mid">
      <div class="form-row sm-header">
        Данные из картотеки<span v-if="!loaded" class="loading-text loading-sm">&nbsp;загрузка</span>
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
      <div class="row">
        <div class="col-xs-6 col-form left" style="padding-bottom: 0">
          <div class="form-row sm-f" style="border-top: none">
            <div class="row-t">Участок</div>
            <select v-model="card.district" class="form-control">
              <option v-for="c in card.districts" :value="c.id">
                {{c.title}}
              </option>
            </select>
          </div>
        </div>
        <div class="col-xs-6 col-form right" style="padding-bottom: 0">
          <div class="form-row sm-f" style="border-top: none">
            <div class="row-t">Телефон</div>
            <input class="form-control" v-model="card.phone" v-mask="'8 999 9999999'">
          </div>
        </div>
      </div>
      <div class="form-row sm-header">
        Данные вызова
      </div>
      <div class="row">
        <div class="col-xs-6 col-form left" style="padding-bottom: 0">
          <div class="form-row sm-f" style="border-top: none">
            <div class="row-t">Дата</div>
            <input class="form-control" readonly type="date" v-model="date" :min="td">
          </div>
        </div>
        <div class="col-xs-6 col-form right" style="padding-bottom: 0">
          <div class="form-row sm-f" style="border-top: none">
            <div class="row-t">Больница</div>
            <treeselect class="treeselect-noborder"
              :multiple="false" :disable-branch-nodes="true" :options="card.hospitals"
              :append-to-body="true" placeholder="Больница не выбрана" v-model="card.hospital"
            />
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col-xs-6 col-form left" style="padding-bottom: 0">
          <div class="form-row sm-f border-right" style="border-top: none">
            <div class="row-t">Цель вызова</div>
            <select v-model="card.purpose" class="form-control">
              <option v-for="c in card.purposes" :value="c.id">
                {{c.label}}
              </option>
            </select>
          </div>
          <div class="form-row sm-f border-right">
            <div class="row-t">Лечащий врач</div>
            <treeselect class="treeselect-noborder"
              :multiple="false" :disable-branch-nodes="true" :options="card.docs"
              :append-to-body="true" placeholder="Врач не выбран" v-model="card.doc"
            />
          </div>
        </div>
        <div class="col-xs-6 col-form right" style="padding-bottom: 0">
          <div class="form-row sm-f" style="border-top: none">
            <div class="row-t">Комментарий</div>
            <textarea class="form-control" v-model="comment"></textarea>
          </div>
        </div>
      </div>
      <template v-if="researches.length > 0">
        <div class="form-row sm-header" style="justify-content: space-between">
          <span>Услуги</span>
          <label style="margin-bottom: 0;"><input type="checkbox" v-model="asExecuted" /> отметить как "выполнено"</label>
        </div>
        <div class="researches">
          <research-display v-for="(res, idx) in disp_researches" :simple="true"
                            :no_tooltip="true"
                            :key="res.pk"
                            :title="res.title" :pk="res.pk" :n="idx"
                            :nof="disp_researches.length"/>
        </div>
        <div class="controls">
          <button class="btn btn-primary-nb btn-blue-nb" type="button" @click="save">Создать записи для обращения
          </button>
        </div>
      </template>
      <div v-else style="padding: 10px;color: gray;text-align: center">
        Услуги не выбраны
      </div>

      <div class="rows" v-if="rows_count > 0">
        <table class="table table-bordered table-condensed table-sm-pd"
               style="table-layout: fixed; font-size: 12px; margin-top: 0;">
          <colgroup>
            <col width="75">
            <col />
            <col width="120"/>
            <col />
            <col width="70"/>
            <col width="75"/>
          </colgroup>
          <thead>
          <tr>
            <th>Дата</th>
            <th>Услуга</th>
            <th>Комментарий</th>
            <th>Адрес, телефон</th>
            <th>Участок</th>
            <th>Статус</th>
          </tr>
          </thead>
          <tbody>
            <tr v-for="r in rows_mapped" :class="{'cancel-row':  r.cancel}">
              <td>{{r.date}}</td>
              <td>
                {{r.service}}
                <template v-if="r.doc"><br />{{r.doc}}</template>
                <template v-if="r.purpose"><br />{{r.purpose}}</template>
                <template v-if="r.hospital"><br />{{r.hospital}}</template>
              </td>
              <td style="white-space: pre-wrap">{{r.comment}}</td>
              <td>{{r.address}}<br/>{{r.phone}}</td>
              <td>{{r.district}}</td>
              <td>
                <button type="button" class="btn btn-blue-nb btn-xs" @click="cancel_doc_call(r.pk)">Отменить</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
  import TypeAhead from 'vue2-typeahead'
  import * as action_types from "@/store/action-types";
  import api from "@/api";
  import patients_point from "@/api/patients-point";
  import moment from "moment";
  import ResearchDisplay from "@/ui-cards/ResearchDisplay";
  import Treeselect from "@riophae/vue-treeselect";
  import '@riophae/vue-treeselect/dist/vue-treeselect.css'

  export default {
    name: "CallDoctor",
    components: {
      ResearchDisplay,
      TypeAhead,
      Treeselect,
    },
    props: {
      card_pk: {
        required: true,
      },
      researches: {
        type: Array,
      },
      visible: {
        type: Boolean,
      },
    },
    data() {
      return {
        card: {
          fact_address: "",
          districts: [],
          district: -1,
          docs: [],
          doc: -1,
          purposes: [],
          purpose: -1,
          hospitals: [],
          hospital: -1,
          phone: "",
        },
        loaded: true,
        asExecuted: false,
        date: moment().format('YYYY-MM-DD'),
        td: moment().format('YYYY-MM-DD'),
        comment: '',
        rows: [],
      };
    },
    mounted() {
      this.$root.$on('update_card_data', () => this.load_data());
    },
    watch: {
      rows_count: {
        handler() {
          this.$root.$emit('call-doctor:rows-count', this.rows_count);
        },
        immediate: true,
      },
      card_pk: {
        handler() {
          this.rows = []
          this.load_data();
        },
        immediate: true,
      },
      visible: {
        handler() {
          this.load_data();
        },
      },
    },
    methods: {
      getResponse(resp) {
        return [...resp.data.data]
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
      async load_data() {
        if (this.card_pk === -1) {
          return;
        }
        if (!this.visible) {
          this.rows = await api('doctor-call/actual-rows', this, 'card_pk')
          return;
        }
        this.loaded = false
        await this.$store.dispatch(action_types.INC_LOADING)
        const [card, {docs, purposes, hospitals, hospitalId}, rows] = await Promise.all([
          patients_point.getCard(this, 'card_pk'),
          api('actual-districts', this, 'card_pk'),
          api('doctor-call/actual-rows', this, 'card_pk'),
        ])
        this.card = card
        this.card.doc = -1
        this.card.docs = docs
        this.card.purpose = (purposes.find(p => p.label === 'Другое') || {id: purposes[0].id}).id
        this.card.purposes = purposes
        this.card.hospital = hospitalId
        this.card.hospitals = hospitals
        this.rows = rows;
        this.loaded = true
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      async save() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const result = await api(
          'doctor-call/create', this,
          ['card_pk', 'researches', 'date', 'comment', 'asExecuted'],
          {
            fact_address: this.card.fact_address,
            district: this.card.district,
            doc: this.card.doc,
            purpose: this.card.purpose,
            hospital: this.card.hospital,
            phone: this.card.phone,
          }
        )
        if (result.ok) {
          okmessage('Записи для вызова на дом созданы');
          this.date = this.td = moment().format('YYYY-MM-DD');
          this.comment = '';
          this.asExecuted = false;
          this.$root.$emit('researches-picker:clear_all');
        }
        await this.load_data();
        await this.$store.dispatch(action_types.DEC_LOADING);
      },
      async cancel_doc_call(pk) {
        await this.$store.dispatch(action_types.INC_LOADING)
        await api(
          'doctor-call/cancel-row',
          {
            pk: pk,
          }
        )
        await this.load_data();
        await this.$store.dispatch(action_types.DEC_LOADING)
      }
    },
    computed: {
      disp_researches() {
        return this.researches.map(id => {
          return this.$store.getters.researches_obj[id];
        })
      },
      rows_count() {
        return this.rows.length;
      },
      purposes() {
        return this.card.purposes.reduce((a, b) => ({...a, [b.id]: b.label}), {});
      },
      rows_mapped() {
        return this.rows.map(r => ({
          pk: r.pk,
          date: moment(r.exec_at).format('DD.MM.YYYY'),
          service: r.research__title,
          address: r.address,
          district: r.district__title,
          doc: r.doc_assigned__fio && `${r.doc_assigned__fio}, ${r.doc_assigned__podrazdeleniye__title}`,
          purpose: (this.purposes || {})[r.purpose],
          hospital: r.hospital__short_title || r.hospital__title,
          comment: r.comment,
          phone: r.phone,
          cancel: r.cancel
        }));
      },
    },
  }
</script>

<style scoped lang="scss">
  .root, .empty {
    position: absolute;
    top: 0 !important;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .empty {
    color: gray;
    display: flex;
    justify-content: center;

    div {
      align-self: center;
    }
  }

  .root {
    overflow-x: hidden;
    overflow-y: auto;
  }

  .col-form {
    padding-bottom: 10px;
  }

  .researches, .controls {
    padding: 5px;
  }

  .controls {
    padding-top: 0;
  }

  .rows {
    margin-top: 5px;
  }

  .cancel-row {
    td, th {
      opacity: .6;
      text-decoration: line-through;
    }
  }
</style>
