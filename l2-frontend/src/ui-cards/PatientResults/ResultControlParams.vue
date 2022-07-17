<template>
  <div v-frag>
    <a
      v-tippy="{
        html: `#${tippyId}`,
        reactive: true,
        interactive: true,
        arrow: true,
        animation: 'fade',
        duration: 0,
        theme: 'light',
        placement: 'bottom',
        trigger: 'click mouseenter',
        zIndex: 104999,
        popperOptions: {
          modifiers: {
            preventOverflow: {
              boundariesElement: 'window',
            },
            hide: {
              enabled: false,
            },
          },
        },
      }"
      href="#"
      class="main-link"
      @click.prevent
    >
      <i
        class="fa fa-key"
        style="color: #6f6f72"
      />
    </a>

    <div
      :id="tippyId"
      class="tp"
    >
      <div class="tp-inner">
        <table class="table">
          <colgroup>
            <col width="60">
            <col width="60">
            <col width="300">
            <col width="80">
          </colgroup>
          <tbody>
            <tr>
              <td colspan="4">
                <button
                  class="btn btn-blue-nb add-row btn-xs nbr"
                  @click="set_current_year"
                >
                  Текущий год
                </button>
                <button
                  v-tippy="{ placement: 'bottom' }"
                  class="btn btn-blue-nb btn-xs nbr"
                  title="Год назад"
                  @click="minus_year('startYear')"
                >
                  <i
                    class="glyphicon glyphicon-arrow-left"
                    style="padding-bottom: 5px"
                  />
                </button>
                {{ start_year }}
                <button
                  v-tippy="{ placement: 'bottom' }"
                  class="btn btn-blue-nb btn-xs nbr"
                  title="Год вперед"
                  @click="plus_year('startYear')"
                >
                  <i
                    class="glyphicon glyphicon-arrow-right nbr"
                    style="padding-bottom: 5px"
                  />
                </button>
                &ensp;&mdash;&ensp;
                <button
                  v-tippy="{ placement: 'bottom' }"
                  class="btn btn-blue-nb btn-xs nbr"
                  title="Год назад"
                  @click="minus_year('endYear')"
                >
                  <i
                    class="glyphicon glyphicon-arrow-left"
                    style="padding-bottom: 5px"
                  />
                </button>
                {{ end_year }}
                <button
                  v-tippy="{ placement: 'bottom' }"
                  class="btn btn-blue-nb btn-xs nbr"
                  title="Год вперед"
                  @click="plus_year('endYear')"
                >
                  <i
                    class="glyphicon glyphicon-arrow-right nbr"
                    style="padding-bottom: 5px"
                  />
                </button>
                <div class="title-control-param">
                  <a
                    href="#"
                    title="Настроить"
                    @click.prevent="edit_pk=3"
                  >
                    <i class="fa fa-cog" />
                  </a>
                  Ключевые показатели здоровья
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <br>
        <table class="table table-bordered table-condensed table-striped table-fixed sticky-table">
          <tbody>
            <tr
              v-for="row in data"
              :key="row.id"
            >
              <td>
                {{ row.title }}
              </td>
              <td>
                {{ row.purposeValue }}
              </td>
              <td
                v-for="(value, key, index) in row.dates"
                :key="index"
                class="fixed-td"
              >
                <div v-if="row.title==='Параметр'">
                  {{ key }}
                </div>
                <div v-else>
                  <span
                    v-for="(jval, jkey, jindex) in value"
                    :key="jindex"
                  >
                    <span
                      v-for="k in jval"
                      :key="k.id"
                    >
                      <a
                        href="#"
                        :title="`№${k.dir} от ${jkey}`"
                        @click.prevent="print_result(k.dir)"
                      >{{ k.value }}; </a>
                    </span>
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div
      class="dreg-flt"
      style="z-index: 105999"
    >
      <Modal
        v-if="edit_pk > -2"
        ref="modalEdit"
        show-footer="true"
        white-bg="true"
        max-width="710px"
        width="100%"
        margin-left-right="auto"
        margin-top
        @close="hide_edit"
      >
        <span
          v-if="edit_pk > -1"
          slot="header"
        >Настройка контролируемых показателей пациента</span>
        <div
          slot="body"
          class="registry-body p10"
        >
          <div class="radio-button-object radio-button-groups">
            <label>Настройка контролируемых показателей</label>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="hide_edit"
              >
                Отмена
              </button>
            </div>
            <div class="col-xs-4">
              <button
                :disabled="!valid_reg"
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="save()"
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import Modal from '@/ui-cards/Modal.vue';

export default {
  name: 'ResultControlParams',
  components: { Modal },
  props: {
    card_pk: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      start_year: moment().format('YYYY'),
      end_year: moment().format('YYYY'),
      data: '',
      edit_pk: -3,
      selectedParams: {},
    };
  },
  computed: {
    tippyId() {
      const parts = [
        'results',
        'preview',
      ];

      return parts.filter(Boolean).join('-');
    },
  },
  watch: {
    start_year() {
      this.load();
    },
    end_year() {
      this.load();
    },
  },
  mounted() {
    this.load();
  },
  methods: {
    async load() {
      const result = await this.$api('patients/individuals/load-control-param', this, [
        'card_pk',
        'start_year',
        'end_year',
      ]);
      this.data = result.results;
    },
    async loadSelectedControlParams() {
      const result = await this.$api('patients/individuals/load-selected-control-params', this, [
        'card_pk',
      ]);
      this.selectedParams = result.results;
    },
    async savePatientControlParams() {
      const result = await this.$api('patients/individuals/save-patient-control-params', this, [
        'card_pk',
        'selectedParams',
      ]);
      this.selectedParams = result.results;
    },
    hide_edit() {
      if (this.$refs.modalEdit) {
        this.$refs.modalEdit.$el.style.display = 'none';
      }
      this.edit_pk = -2;
    },
    plus_year(typeYear) {
      if (typeYear === 'startYear') {
        this.start_year = moment(this.start_year)
          .add(1, 'year')
          .format('YYYY');
      } else {
        this.end_year = moment(this.end_year)
          .add(1, 'year')
          .format('YYYY');
      }
    },
    minus_year(typeYear) {
      if (typeYear === 'startYear') {
        this.start_year = moment(this.start_year)
          .subtract(1, 'year')
          .format('YYYY');
      } else {
        this.end_year = moment(this.end_year)
          .subtract(1, 'year')
          .format('YYYY');
      }
    },
    set_current_year() {
      this.start_year = moment().format('YYYY');
      this.end_year = moment().format('YYYY');
      this.load();
    },
    print_result(pk) {
      this.$root.$emit('print:results', [pk]);
    },
  },
};
</script>

<style scoped lang="scss">
i {
  vertical-align: middle;
  display: inline-block;
  margin-right: 3px;
}

.tp {
  min-height: 400px;
  text-align: left;
  padding: 1px;

  table {
    margin: 0;
  }

  max-height: 700px;
  width: 900px;
  overflow-y: auto;

  &-inner {
    overflow: visible;
  }
}

.main-link {
  display: inline-block;

  i {
    padding-left: 1px;
  }
}

.sticky-table {
  td:first-child {
    position: sticky;
    background-color: white;
    left: 0;
    z-index: 5;
    table-layout: fixed;
    overflow: scroll;
    width: 230px;
    word-wrap: break-word;
    border-right: 1px solid #eeeeee;
  }
  tr:first-child {
    position: sticky;
    background-color: white;
    top: 0;
    z-index: 2;
  }
  :not(td:nth-child(1)) {
    table-layout: fixed;
    width: 110px;
    word-wrap: break-word;
  }
  tr:hover {
    background: #37bc9b;
    color: black;
    opacity: 0.8;
   }
}

a {
  text-decoration: none;
  color: black;
}

a:hover {
  text-decoration: underline;
  color: white;
}

.title-control-param {
  color: #16a085;
  float: right;
  font-size: 18px;

  i {
    color: #aab2bd;
  }
}

</style>
