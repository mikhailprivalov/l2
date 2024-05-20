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
        v-if="isDocReferral"
        class="fa fa-user-md"
        style="color: #6f6f72"
      />
      <i
        v-if="isParaclinic"
        class="fa fa-file-medical-alt"
        style="color: #6f6f72"
      />
      <i
        v-if="isLab"
        class="fa fa-vials"
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
            <tr
              v-for="row in data"
              :key="row.dir"
            >
              <td>
                <ResultDetails
                  :direction="row.dir"
                  :is-lab="isLab"
                  :is-doc-referral="isDocReferral"
                  :is-paraclinic="isParaclinic"
                />
              </td>
              <td>
                {{ row.date }}
              </td>
              <td>
                {{ row.researches.join('; ') }}
              </td>
              <td class="right-buttons">
                <a
                  v-if="row.pacsLink"
                  v-tippy="{ placement: 'bottom' }"
                  :href="`http://${row.pacsLink}`"
                  target="_blank"
                  title="Снимок"
                ><i class="fa fa-camera" /></a>
                <a
                  v-tippy="{ placement: 'bottom' }"
                  href="#"
                  title="Печать результата"
                  @click.prevent="print_result(row.dir)"
                ><i class="fa fa-print" /></a>
                <a
                  v-tippy="{ placement: 'bottom' }"
                  href="#"
                  title="Перенести в протокол"
                  @click.prevent="sendToProtocol(row.dir)"
                ><i class="fa fa-file-import" />
                </a>
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

import ResultDetails from './ResultDetails.vue';

export default {
  name: 'ResultsLaboratory',
  components: { ResultDetails },
  props: {
    card_pk: {
      type: Number,
      required: true,
    },
    isLab: {
      type: Boolean,
      required: false,
      default: false,
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
      current_year: moment().format('YYYY'),
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
  min-height: 300px;
  text-align: left;
  padding: 1px;

  table {
    margin: 0;
  }

  max-height: 500px;
  width: 500px;
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
