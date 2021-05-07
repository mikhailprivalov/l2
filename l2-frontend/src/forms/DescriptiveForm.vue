<template>
  <div>
    <visibility-group-wrapper :group="group"
                              :groups="groups"
                              :patient="patient"
                              :key="group.pk"
                              v-for="group in research.groups">
      <div class="group">
        <div class="group-title" v-if="group.title !== ''">{{group.title}}</div>
        <div class="fields">
          <visibility-field-wrapper :formula="field.visibility" :group="group" :groups="research.groups"
                                    :patient="patient"
                                    :key="field.pk"
                                    v-for="field in group.fields">

            <div class="wide-field-title" v-if="field.title !== '' && research.wide_headers">
              <template v-if="field.title.endsWith('?')">{{field.title}}</template>
              <template v-else>{{field.title}}:</template>
            </div>
            <div :class="{disabled: confirmed,
            empty: notFilled.includes(field.pk),
            required: field.required}" :title="field.required && 'обязательно для заполнения'"
                 v-on="{
                  mouseenter: enter_field(field.values_to_input.length > 0),
                  mouseleave: leave_field(field.values_to_input.length > 0),
                 }" class="field">
              <div class="field-title" v-if="field.title !== '' && !research.wide_headers">
                {{field.title}}
              </div>
              <longpress :confirm-time="0"
                         :duration="400"
                         :on-confirm="clear_val" :value="field"
                         action-text="×" class="btn btn-default btn-field" pressing-text="×"
                         v-if="!confirmed && ![3, 10, 12, 15, 16, 17, 18, 19, 21, 24, 25, 26, 27].includes(field.field_type)">
                ×
              </longpress>
              <FastTemplates
                :update_value="updateValue(field)"
                :value="field.value"
                :values="field.values_to_input"
                :confirmed="confirmed"
                :field_type="field.field_type"
                :field_title="field.title"
              />
              <div class="field-value" v-if="field.field_type === 0">
                <textarea :readonly="confirmed" :rows="field.lines" class="form-control"
                          v-if="field.lines > 1" v-model="field.value"></textarea>
                <input :readonly="confirmed" class="form-control" v-else v-model="field.value"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 1">
                <input :readonly="confirmed" class="form-control" style="width: 160px" type="date"
                       v-model="field.value"/>
              </div>
              <div class="field-value mkb10" v-else-if="field.field_type === 2 && !confirmed">
                <MKBFieldForm :short="false" @input="change_mkb(field)" v-model="field.value"/>
              </div>
              <div class="field-value mkb10" v-else-if="field.field_type === 3">
                <FormulaField :fields="research.groups.reduce((a, b) => a.concat(b.fields), [])"
                              :formula="field.default_value"
                              :patient="patient"
                              v-model="field.value"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 2 && confirmed">
                <input :readonly="true" class="form-control" v-model="field.value"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 10">
                <SelectField
                  :disabled="confirmed" :variants="field.values_to_input" class="form-control fw"
                  v-model="field.value"
                />
              </div>
              <div class="field-value" v-else-if="field.field_type === 11">
                <SearchFractionValueField :readonly="confirmed"
                                          :fraction-pk="field.default_value"
                                          :client-pk="patient.card_pk"
                                          v-model="field.value"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 12">
                <RadioField
                  :disabled="confirmed" :variants="field.values_to_input"
                  v-model="field.value"
                />
              </div>
              <div class="field-value" v-else-if="field.field_type === 13 || field.field_type === 14 || field.field_type === 23">
                <SearchFieldValueField :readonly="confirmed"
                                       :field-pk="field.default_value"
                                       :client-pk="patient.card_pk"
                                       :lines="field.lines"
                                       :raw="field.field_type === 14 || field.field_type === 23"
                                       :not_autoload_result="field.field_type === 23"
                                       :iss_pk="pk"
                                       v-model="field.value"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 15">
                <RichTextEditor :readonly="confirmed"
                                :disabled="confirmed"
                                v-model="field.value"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 16 && pk">
                <AggregateLaboratory :pk="pk" extract v-model="field.value" :disabled="confirmed"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 17 && pk && hospital_r_type">
                <AggregateDesc
                  :pk="pk"
                  extract
                  :r_type="hospital_r_type"
                  v-model="field.value"
                />
              </div>
              <div class="field-value" v-else-if="field.field_type === 18">
                <NumberField v-model="field.value" :disabled="confirmed" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 19">
                <NumberRangeField :variants="field.values_to_input" v-model="field.value" :disabled="confirmed" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 20">
                <input :readonly="confirmed" class="form-control" style="width: 110px" type="time"
                       v-model="field.value"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 21">
                <AnesthesiaProcess :fields="field.values_to_input" :iss="pk" :field_pk="field.pk" :disabled="confirmed"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 22">
                <TextareaAutocomplete
                  :disabled="confirmed"
                  v-model="field.value"
                />
              </div>
              <div class="field-value" v-else-if="field.field_type === 24">
                <LaboratoryPreviousResults v-model="field.value" :disabled="confirmed"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 25">
                <DiagnosticPreviousResults v-model="field.value" :disabled="confirmed"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 26">
                <DocReferralPreviousResults v-model="field.value" :disabled="confirmed"/>
              </div>
              <div class="field-value" v-else-if="field.field_type === 27">
                <TableField :variants="field.values_to_input" v-model="field.value" :disabled="confirmed" />
              </div>
              <div :title="field.helper" class="field-helper" v-if="field.helper"
                   v-tippy="{
                    placement: 'left',
                    arrow: true,
                    interactive: true,
                    theme: 'dark longread',
                  }">
                <i class="fa fa-question"/>
              </div>
            </div>
          </visibility-field-wrapper>
        </div>
      </div>
    </visibility-group-wrapper>
  </div>
</template>

<script>
import Longpress from 'vue-longpress';
import VisibilityGroupWrapper from '../components/VisibilityGroupWrapper.vue';
import VisibilityFieldWrapper from '../components/VisibilityFieldWrapper.vue';
import FastTemplates from './FastTemplates.vue';
import { enter_field, leave_field } from './utils';

export default {
  name: 'DescriptiveForm',
  components: {
    FastTemplates,
    VisibilityGroupWrapper,
    VisibilityFieldWrapper,
    Longpress,
    TextareaAutocomplete: () => import('../fields/TextareaAutocomplete'),
    NumberRangeField: () => import('../fields/NumberRangeField'),
    NumberField: () => import('../fields/NumberField'),
    TableField: () => import('../fields/TableField'),
    AggregateDesc: () => import('../fields/AggregateDesc'),
    AggregateLaboratory: () => import('../fields/AggregateLaboratory'),
    RichTextEditor: () => import('../fields/RichTextEditor'),
    SearchFractionValueField: () => import('../fields/SearchFractionValueField'),
    SearchFieldValueField: () => import('../fields/SearchFieldValueField'),
    RadioField: () => import('../fields/RadioField'),
    SelectField: () => import('../fields/SelectField'),
    AnesthesiaProcess: () => import('../fields/AnesthesiaProcess'),
    MKBFieldForm: () => import('../fields/MKBFieldForm'),
    FormulaField: () => import('../fields/FormulaField'),
    LaboratoryPreviousResults: () => import('../fields/LaboratoryPreviousResults'),
    DiagnosticPreviousResults: () => import('../fields/DiagnosticPreviousResults'),
    DocReferralPreviousResults: () => import('../fields/DocReferralPreviousResults'),
  },
  props: {
    research: {
      type: Object,
      required: true,
    },
    pk: {
      type: Number,
      required: false,
    },
    patient: {
      type: Object,
      required: true,
    },
    confirmed: {
      type: Boolean,
      required: true,
    },
    change_mkb: {
      type: Function,
      // eslint-disable-next-line @typescript-eslint/no-empty-function
      default: () => () => {},
      required: false,
    },
    hospital_r_type: {
      type: String,
      required: false,
    },
  },
  data() {
    return {
      prev_scroll: 0,
      prev_scrollHeightTop: 0,
      versionTickTimer: null,
    };
  },
  watch: {
    groups: {
      deep: true,
      handler() {
        this.inc_version();
      },
    },
  },
  mounted() {
    this.versionTickTimer = setInterval(() => this.inc_version(), 2000);
  },
  beforeDestroy() {
    clearInterval(this.versionTickTimer);
  },
  computed: {
    notFilled() {
      const l = [];
      if (this.confirmed) {
        return [];
      }

      for (const g of this.research.groups) {
        for (const f of g.fields) {
          if (f.required && (f.value === '' || f.value === '- Не выбрано' || !f.value)) {
            l.push(f.pk);
          }
        }
      }
      return l;
    },
    groups() {
      return this.research.groups;
    },
  },
  methods: {
    inc_version() {
      this.research.version = (this.research.version || 0) + 1;
    },
    updateValue(field) {
      return (newValue) => {
        // eslint-disable-next-line no-param-reassign
        field.value = newValue;
      };
    },
    clear_val(field) {
      // eslint-disable-next-line no-param-reassign
      field.value = '';
    },
    enter_field(...args) {
      return enter_field.apply(this, args);
    },
    leave_field(...args) {
      return leave_field.apply(this, args);
    },
  },
};
</script>

<style scoped lang="scss">

.title_anesthesia {
  flex: 1 0 70px;
  padding-left: 5px;
  padding-top: 5px;
}

</style>
