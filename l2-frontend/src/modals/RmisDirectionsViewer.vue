<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" min-width="85%" margin-top
         :no-close="selected_direction !== -1">
    <span slot="header">Направления из РМИС. Пациент: {{card.family}} {{card.name}} {{card.twoname}},
      {{card.birthday}} ({{card.age}})</span>
    <div slot="body" style="min-height: 200px" class="directions-manage" v-if="loaded">
      <div class="directions-sidebar">
        <div @click="select_direction(d.pk)" class="direction"
             :class="{active: d.pk === selected_direction}"
             :key="d.pk"
             v-for="d in rows">
          <div>РМИС-направление №{{d.pk}} от {{d.referralDate}}</div>
          <div>Направляющая организация: {{d.referralOrganization}}</div>
          <hr/>
          <ol>
            <li v-for="s in d.services" :key="`${s.code}_${s.title}`">
              <span class="s-code" v-if="s.code">{{s.code}}</span>
              {{s.title}}
            </li>
          </ol>
        </div>
        <div v-if="rows.length === 0" class="text-center" style="padding: 10px">
          Направлений из РМИС, не зарегистрированных в L2, не найдено
        </div>
      </div>
      <div class="directions-content" v-if="selected_direction !== -1">
        <div class="direction-data">
          <h4>РМИС-направление №{{direction_data.pk}} от {{direction_data.referralDate}}</h4>
          Организация: {{direction_data.referralOrganization}}<br/>
          <div v-if="direction_data.diagnosis">Диагноз: {{direction_data.diagnosis}}
            ({{direction_data.diagnosisName}})
          </div>
          <hr/>
          <div class="direction-service">
            <div class="service-rmis">
              <div class="s-title"><strong>Исследование в РМИС</strong></div>
            </div>
            <div class="service-l2"><strong>Исследование в L2</strong></div>
          </div>
          <div class="direction-service"
               :class="{wrn: s.selected_local_service === -1 && !s.exclude_direction, cancel: s.exclude_direction}"
               :key="`${s.code}_${s.title}`"
               v-for="s in direction_data.services">
            <div class="service-rmis">
              <div class="s-code">{{s.code}}</div>
              <div class="s-title">{{s.title}}</div>
            </div>
            <div class="service-l2" v-if="s.local_services.length === 1 && s.selected_local_service !== -1">
              <div class="service-department">
                {{departments[research_data(s.selected_local_service).department_pk].title}}
              </div>
              {{research_data(s.selected_local_service).title}}
              <div class="no-attach">
                <label><input type="checkbox" v-model="s.exclude_direction"> не назначать</label>
              </div>
            </div>
            <div class="service-l2" v-else-if="s.local_services.length > 1">
              <div class="l2-notice">Найдено несколько исследований с таким кодом</div>
              <ul>
                <li v-for="rs in s.local_services" :key="rs">
                  <label class="fwn">
                    <input type="radio" :value="rs" v-model="s.selected_local_service">
                    <span class="service-department">
                      {{departments[research_data(rs).department_pk].title}}
                    </span>
                    {{research_data(rs).title}}
                  </label>
                </li>
              </ul>
              <div class="no-attach">
                <label><input type="checkbox" v-model="s.exclude_direction"> не назначать</label>
              </div>
            </div>
            <div class="service-l2" v-else>
              <div class="l2-notice">Исследований с таким кодом не найдено</div>
              <div v-if="s.selected_local_service !== -1">
                Будет произведена замена на:
                <div class="service-department">
                  {{departments[research_data(s.selected_local_service).department_pk].title}}
                </div>
                {{research_data(s.selected_local_service).title}}
              </div>
              <div :id="'template-' + s.pk">
                <div style="width: 666px;height: 280px;text-align: left;">
                  <researches-picker v-model="s.selected_local_service" autoselect="none" :hidetemplates="true"
                                     :oneselect="true"/>
                </div>
              </div>
              <button class="btn btn-primary-nb btn-blue-nb btn-sm" style="margin-top: 3px"
                      v-tippy="{
                        html: '#template-' + s.pk,
                        reactive : true,
                        interactive : true,
                        theme: 'light',
                        animateFill: false,
                        trigger: 'click'
                      }">
                Заменить исследование
              </button>
              <div class="no-attach">
                <label><input type="checkbox" v-model="s.exclude_direction"> не назначать</label>
              </div>
            </div>
          </div>
        </div>
        <div class="direction-control">
          <button class="btn btn-primary-nb btn-blue-nb" @click="cancel">Отмена</button>
          <button class="btn btn-primary-nb btn-blue-nb" :disabled="!valid" @click="generateDirections">Создать
            направления в L2
          </button>
        </div>
      </div>
      <div class="directions-content" style="line-height: 200px;text-align: center;color:grey" v-else>
        Направление не выбрано
      </div>
    </div>
    <div slot="body" style="line-height: 200px;text-align: center" v-else>
      Загрузка данных...
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button type="button" @click="load_data" class="btn btn-primary-nb btn-blue-nb"
                  :disabled="selected_direction !== -1">Перезагрузить
          </button>
        </div>
        <div class="col-xs-4">
        </div>
        <div class="col-xs-4">
          <button type="button" @click="hide_modal" class="btn btn-primary-nb btn-blue-nb"
                  :disabled="selected_direction !== -1">Закрыть
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
import Modal from '../ui-cards/Modal.vue';
import directionsPoint from '../api/directions-point';
import * as actions from '../store/action-types';
import ResearchesPicker from '../ui-cards/ResearchesPicker.vue';

export default {
  name: 'rmis-directions-viewer',
  components: { Modal, ResearchesPicker },
  props: {
    card: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      rows: [],
      loaded: false,
      direction_data: {},
      selected_direction: -1,
      post: false,
    };
  },
  created() {
    this.load_data();
  },
  computed: {
    departments() {
      const deps = {};
      for (const dep of this.$store.getters.allDepartments) {
        deps[dep.pk] = dep;
      }
      return deps;
    },
    valid() {
      if (this.selected_direction === -1 || Object.keys(this.direction_data).length === 0) return false;
      let has_n_ex = false;
      for (const r of this.direction_data.services) {
        if (r.selected_local_service === -1 && !r.exclude_direction) {
          return false;
        }
        if (!r.exclude_direction) has_n_ex = true;
      }
      return has_n_ex;
    },
    has_excluded() {
      if (!this.valid) return false;
      for (const r of this.direction_data.services) {
        if (r.exclude_direction) return true;
      }
      return false;
    },
  },
  methods: {
    generateDirections() {
      if (this.post) return;
      const r = {};
      for (const s of this.direction_data.services) {
        if (s.exclude_direction || s.selected_local_service === -1) continue;
        const dep = this.research_data(s.selected_local_service).department_pk;
        if (!(dep in r)) {
          r[dep] = [];
        }
        r[dep].push(s.selected_local_service);
      }

      this.post = true;
      this.$root.$emit('generate-directions', {
        type: 'direction',
        card_pk: this.card.pk,
        fin_source_pk: null,
        diagnos: this.direction_data.diagnosis || '',
        base: null,
        researches: r,
        operator: false,
        ofname: -1,
        history_num: '',
        comments: {},
        for_rmis: true,
        rmis_data: { rmis_number: this.selected_direction, imported_org: this.direction_data.referralOrganizationPk },
        callback: () => {
          this.load_data();
        },
      });
    },
    research_data(pk) {
      if (pk in this.$store.getters.researches_obj) {
        return this.$store.getters.researches_obj[pk];
      }
      return {};
    },
    cancel() {
      this.direction_data = {};
      this.selected_direction = -1;
      this.post = false;
    },
    hide_modal() {
      this.$root.$emit('hide_rmis_directions');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    load_data() {
      this.loaded = false;
      this.$store.dispatch(actions.INC_LOADING);
      this.cancel();
      directionsPoint.getRmisDirections(this.card, ['pk']).then((data) => {
        this.rows = data.rows;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.loaded = true;
      });
    },
    select_direction(pk) {
      if (pk === this.selected_direction) return;
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint.getRmisDirection({ pk }).then((data) => {
        this.direction_data = data;
        this.selected_direction = pk;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
  },
};
</script>

<style scoped lang="scss">
  .modal-mask {
    align-items: stretch !important;
    justify-content: center !important;
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

  .directions-manage {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;
    & > div {
      align-self: stretch;
    }
  }

  .directions-sidebar {
    width: 450px;
    background: rgba(0, 0, 0, .04);
    border-right: 1px solid rgba(0, 0, 0, .16);
    overflow-y: auto;
    overflow-x: hidden;
  }

  .directions-content {
    display: flex;
    flex-direction: column;
    width: calc(100% - 450px);
  }

  .direction-data {
    flex: 1;
    padding: 5px 10px;
    overflow-y: auto;
  }

  .direction-control {
    height: 34px;
    display: flex;
    .btn {
      border-radius: 0;
      &:first-child {
        border-right: 1px solid #fff !important;
      }
    }
  }

  .direction {
    padding: 5px;
    margin: 5px;
    border-radius: 5px;
    border: 1px solid rgba(0, 0, 0, 0.14);
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
    &:not(.active) {
      cursor: pointer;
      transition: all .2s cubic-bezier(.25, .8, .25, 1);
    }
    position: relative;

    &.active {
      background-image: linear-gradient(#6C7A89, #56616c);
      color: #fff;
    }

    hr {
      margin: 3px;
    }

    ol {
      padding-left: 25px;
      li {
        margin-bottom: 3px;
      }
    }

    &:not(.active):hover {
      box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
      z-index: 1;
      transform: scale(1.008);
    }
  }

  .direction-service {
    margin: 5px;
    border-radius: 5px;
    border: 1px solid rgba(0, 0, 0, 0.14);
    overflow: hidden;
    display: flex;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);

    &.wrn {
      border: 1px solid #932a04;
      .s-code {
        background: #932a04;
      }
      .service-rmis {
        border-right: 1px solid #932a04;
      }
    }

    &.cancel {
      border: 1px solid rgba(0, 0, 0, 0.2);
      background: rgba(0, 0, 0, 0.2);
      .s-code {
        background: rgba(0, 0, 0, 0.2);
      }
      .service-rmis {
        border-right: 1px solid rgba(0, 0, 0, 0.2);
      }
    }

    .s-code {
      vertical-align: top;
      border-radius: 0;
      padding: 5px;
      display: block;
      text-align: left;
      font-size: 14px
    }

    .s-title {
      margin: 5px;
      display: block;
    }

    .service-rmis {
      border-right: 1px solid rgba(0, 0, 0, 0.14);
    }

    .service-l2 {
      padding: 5px;
    }

    .service-rmis, .service-l2 {
      flex: 1 50%;
    }
  }

  .service-department {
    display: inline-block;
    background: rgba(0, 0, 0, .08);
    padding: 2px;
    border-radius: 2px;
  }

  .no-attach {
    font-size: 12px;
    label {
      font-weight: 300;
    }
  }

  .fwn {
    font-weight: normal;
  }

  .l2-notice {
    color: #5e5e5e;
    font-weight: bold;
  }
</style>
