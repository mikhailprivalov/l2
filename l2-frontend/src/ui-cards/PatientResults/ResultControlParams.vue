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
            <col width="50">
            <col width="80">
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
                  @click="minus_year"
                >
                  <i
                    class="glyphicon glyphicon-arrow-left"
                    style="padding-bottom: 5px"
                  />
                </button>
                {{ current_year }}
                <button
                  v-tippy="{ placement: 'bottom' }"
                  class="btn btn-blue-nb btn-xs nbr"
                  title="Год вперед"
                  @click="plus_year"
                >
                  <i
                    class="glyphicon glyphicon-arrow-right nbr"
                    style="padding-bottom: 5px"
                  />
                </button>
              </td>
            </tr>
            <tr>
              <td colspan="4">
                <DatePicker
                  :key="DATE_RANGE"
                  v-model="dateRange"
                  mode="date"
                  :masks="masks"
                  is-range
                  :max-date="new Date()"
                  :rows="2"
                  :step="1"
                >
                  <template #default="{ inputValue, inputEvents }">
                    <div class="input-group">
                      <span class="input-group-addon">Дата:</span>
                      <input
                        class="form-control"
                        :value="inputValue.start"
                        v-on="inputEvents.start"
                      >
                      <span
                        class="input-group-addon"
                        style="background-color: #fff;color: #000; height: 34px"
                      >&mdash;</span>
                      <input
                        class="form-control"
                        :value="inputValue.end"
                        v-on="inputEvents.end"
                      >
                    </div>
                  </template>
                </DatePicker>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
// @ts-ignore
import DatePicker from 'v-calendar/lib/components/date-picker.umd';

export default {
  name: 'ResultControlParams',
  components: {
    DatePicker,
  },
  props: {
    card_pk: {
      type: Number,
      required: true,
    },
    isDocReferral: {
      type: Boolean,
      default: false,
    },
    isParaclinic: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      data: '',
      DATE_RANGE: 'DATE_RANGE',
      current_year: moment().format('YYYY'),
      dateRange: {
        start: new Date(),
        end: new Date(),
      },
      masks: {
        iso: 'DD.MM.YYYY',
        data: ['DD.MM.YYYY'],
        input: ['DD.MM.YYYY'],
      },
    };
  },
  computed: {
    tippyId() {
      const parts = [
        'results',
        'preview',
        this.isLab && 'lab',
        this.isDocReferral && 'docReferral',
        this.isParaclinic && 'paraclinic',
      ];

      return parts.filter(Boolean).join('-');
    },
  },
  watch: {
    current_year() {
      this.load();
    },
  },
  mounted() {
    this.load();
  },
  methods: {
    async load() {
      const result = await this.$api('directions/result-patient-year', this, [
        'card_pk',
        'current_year',
        'isLab',
        'isDocReferral',
        'isParaclinic',
      ]);
      this.data = result.results;
    },
    print_med_certificate(typeForm, direction) {
      window.open(`/medical_certificates/pdf?type=${typeForm}&dir=${direction}`, '_blank');
    },
    plus_year() {
      this.current_year = moment(this.current_year)
        .add(1, 'year')
        .format('YYYY');
    },
    minus_year() {
      this.current_year = moment(this.current_year)
        .subtract(1, 'year')
        .format('YYYY');
    },
    set_current_year() {
      this.current_year = moment().format('YYYY');
      this.load();
    },
    sendToProtocol(direction) {
      if (this.isLab) {
        this.$root.$emit('protocol:laboratoryResult', direction);
      } else if (this.isParaclinic) {
        this.$root.$emit('protocol:paraclinicResult', direction);
      } else if (this.isDocReferral) {
        this.$root.$emit('protocol:docReferralResults', direction);
      }
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
  width: 700px;
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

.right-buttons {
  text-align: right;
}
</style>
