<template>
  <fragment>
    <a href="#" class="main-link" @click.prevent
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
                zIndex: 4999,
                popperOptions: {
                  modifiers: {
                    preventOverflow: {
                      boundariesElement: 'window'
                    },
                    hide: {
                      enabled: false
                    }
                  }
                },
             }">

      <i v-if="isDocReferral" class="fa fa-user-md" style="color: #046f8f"></i>
      <i v-if="isParaclinic" class="fa fa-file-medical-alt" style="color: #6d0493"></i>
      <i v-if="isLab" class="fa fa-vials" style="color: #a5005a"></i>
    </a>

    <div :id="tippyId" class="tp">
      <div class="tp-inner">
        <table class="table">
          <colgroup>
            <col width='50'/>
            <col width='80'/>
            <col width='300'/>
            <col width='80'/>
          </colgroup>
          <tbody>
          <tr>
            <td>
              <a href="#" @click.prevent="set_current_year" style="padding-left: 5px" v-tippy="{ placement: 'bottom'}"
                 title="Текущий год"><i class="fa fa-circle"></i></a>
            </td>
            <td>
              <a href="#" @click.prevent="minus_year"><i class="fa fa-angle-double-left"></i></a>
              <a href="#">{{ current_year }}</a>
              <a href="#" @click.prevent="plus_year"><i class="fa fa-angle-double-right"></i></a>
            </td>
            <td></td>
            <td></td>
          </tr>
          <tr v-for="row in data">
            <td>
              <ResultDetails :direction="row.dir"
                             :isLab="isLab" :isDocReferral="isDocReferral" :isParaclinic="isParaclinic"/>
            </td>
            <td>
              {{ row.date }}
            </td>
            <td>
              {{ row.researches.join('; ') }}
            </td>
            <td>
              <a href="#" @click.prevent="plus_year"><i class="fa fa-print"></i></a>
              <a href="#" @click.prevent="sendToProtocol(row.dir)" v-tippy="{ placement: 'bottom'}"
                 title="Перенести в протокол"><i class="fa fa-file-import"></i>
              </a>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </fragment>
</template>

<script>
import api from '@/api'
import moment from "moment";
import ResultDetails from "./ResultDetails";


export default {
  name: "ResultsLaboratory",
  components: {ResultDetails},
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
    }
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
  mounted() {
    this.load();
  },
  methods: {
    async load() {
      const result = await api('directions/result-patient-year', this, ['card_pk', 'current_year',
        'isLab', 'isDocReferral', 'isParaclinic']);
      this.data = result.results;
    },
    print_med_certificate(type_form, direction) {
      window.open(`/medical_certificates/pdf?type=${type_form}&dir=${direction}`, '_blank')
    },
    plus_year() {
      this.current_year = moment(this.current_year).add(1, 'year').format('YYYY');
    },
    minus_year() {
      this.current_year = moment(this.current_year).subtract(1, 'year').format('YYYY');
    },
    set_current_year() {
      this.current_year = moment().format('YYYY')
      this.load()
    },
    sendToProtocol(direction){
      this.$root.$emit('protocol:laboratoryResult', direction)
    }
  },
  watch: {
    current_year() {
      this.load()
    }
  }
}
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

  max-height: 600px;
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
</style>
