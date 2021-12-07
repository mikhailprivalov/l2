<template>
  <div>
    <visibility-group-wrapper :group="group" :groups="groups" :patient="patient" :key="group.pk" v-for="group in research.groups">
      <div class="group">
        <div class="group-title" v-if="group.title !== ''">{{ group.title }}</div>
        <div class="fields">
          <visibility-field-wrapper
            :formula="field.visibility"
            :group="group"
            :groups="research.groups"
            :patient="patient"
            :key="field.pk"
            v-for="field in group.fields"
          >
            <div class="wide-field-title" v-if="field.title !== '' && research.wide_headers">
              <template v-if="field.title.endsWith('?')">{{ field.title }}</template>
              <template v-else>{{ field.title }}:</template>
            </div>
            <div
              :class="{
                disabled: confirmed,
                empty: notFilled.includes(field.pk),
                'field-vertical-simple': [16, 17].includes(field.field_type) && pk,
                required: field.required,
              }"
              :title="field.required && 'обязательно для заполнения'"
              v-on="{
                mouseenter: enter_field(field.values_to_input.length > 0),
                mouseleave: leave_field(field.values_to_input.length > 0),
              }"
              class="field"
              :key="`field-${field.pk}`"
            >
              <div class="field-title" v-if="field.title !== '' && !research.wide_headers">
                {{ field.title }}
              </div>
              <LPress
                v-if="
                  !confirmed &&
                    !{
                      3: 1,
                      10: 1,
                      12: 1,
                      15: 1,
                      16: 1,
                      17: 1,
                      18: 1,
                      19: 1,
                      21: 1,
                      24: 1,
                      25: 1,
                      26: 1,
                      27: 1,
                      28: 1,
                      30: 1,
                    }[field.field_type]
                "
                :pk="field.pk"
                :on-confirm="clear_val_by_pk"
              />
              <InputTemplates :field="field" :group="group" v-if="!confirmed && [0].includes(field.field_type)" />
              <FastTemplates
                :update_value="updateValue(field)"
                :value="field.value"
                :values="field.values_to_input"
                :confirmed="confirmed"
                :field_type="field.field_type"
                :field_title="field.title"
              />
              <div class="field-value field-value-with-templates" v-if="field.field_type === 0">
                <TextFieldWithTemplates v-model="field.value" :confirmed="confirmed" :field-pk="field.pk" :lines="field.lines" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 1">
                <input :readonly="confirmed" class="form-control" style="width: 160px" type="date" v-model="field.value" />
              </div>
              <div class="field-value mkb10" v-else-if="field.field_type === 2 && !confirmed">
                <MKBFieldForm :short="false" @input="change_mkb(field)" v-model="field.value" />
              </div>
              <div class="field-value mkb10" v-else-if="field.field_type === 3">
                <FormulaField
                  :fields="research.groups.reduce((a, b) => a.concat(b.fields), [])"
                  :formula="field.default_value"
                  :patient="patient"
                  v-model="field.value"
                />
              </div>
              <div class="field-value" v-else-if="field.field_type === 2 && confirmed">
                <input :readonly="true" class="form-control" v-model="field.value" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 10">
                <TreeSelectField :disabled="confirmed" :variants="field.values_to_input" v-model="field.value" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 11">
                <SearchFractionValueField
                  :readonly="confirmed"
                  :fraction-pk="field.default_value"
                  :client-pk="patient.card_pk"
                  v-model="field.value"
                />
              </div>
              <div class="field-value" v-else-if="field.field_type === 12">
                <RadioField :disabled="confirmed" :variants="field.values_to_input" v-model="field.value" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 13 || field.field_type === 14 || field.field_type === 23">
                <SearchFieldValueField
                  :readonly="confirmed"
                  :field-pk="field.default_value"
                  :client-pk="patient.card_pk"
                  :lines="field.lines"
                  :raw="field.field_type === 14 || field.field_type === 23"
                  :not_autoload_result="field.field_type === 23"
                  :iss_pk="pk"
                  v-model="field.value"
                />
              </div>
              <div class="field-value" v-else-if="field.field_type === 15">
                <RichTextEditor :readonly="confirmed" :disabled="confirmed" v-model="field.value" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 16 && pk">
                <AggregateLaboratory :pk="pk" extract v-model="field.value" :disabled="confirmed" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 17 && pk && hospital_r_type">
                <AggregateDesc :pk="pk" extract :r_type="hospital_r_type" v-model="field.value" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 18">
                <NumberField v-model="field.value" :disabled="confirmed" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 19">
                <NumberRangeField :variants="field.values_to_input" v-model="field.value" :disabled="confirmed" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 20">
                <input :readonly="confirmed" class="form-control" style="width: 110px" type="time" v-model="field.value" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 21">
                <AnesthesiaProcess :fields="field.values_to_input" :iss="pk" :field_pk="field.pk" :disabled="confirmed" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 22">
                <TextareaAutocomplete :disabled="confirmed" v-model="field.value" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 24">
                <LaboratoryPreviousResults v-model="field.value" :disabled="confirmed" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 25">
                <DiagnosticPreviousResults v-model="field.value" :disabled="confirmed" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 26">
                <DocReferralPreviousResults v-model="field.value" :disabled="confirmed" />
              </div>
              <div class="field-value" v-else-if="field.field_type === 27">
                <TableField
                  :variants="field.values_to_input"
                  :fields="research.groups.reduce((a, b) => a.concat(b.fields), [])"
                  :field-pk="field.pk"
                  v-model="field.value"
                  :disabled="confirmed"
                  :card_pk="patient.card_pk"
                  :iss_pk="pk"
                />
              </div>
              <div class="field-value" v-else-if="field.field_type === 28">
                <PermanentDirectoryField
                  :oid="field.values_to_input"
                  v-model="field.value"
                  :field-title="field.title"
                  :disabled="confirmed"
                />
              </div>
              <div class="field-value field-value-address mkb" v-else-if="field.field_type === 29">
                <AddressFiasField
                  v-model="field.value"
                  :disabled="confirmed"
                  :client-pk="patient.card_pk"
                  :edit-title="`${group.title} ${field.title}`.trim()"
                  :strict="false"
                />
              </div>
              <div class="field-value field-value-address mkb" v-else-if="field.field_type === 30">
                <NumberGeneratorField
                  v-model="field.value"
                  :number-key="field.default_value"
                  :disabled="confirmed"
                  :iss-pk="pk"
                  :field-pk="field.pk"
                />
              </div>
              <div class="field-value field-value-address mkb" v-else-if="field.field_type === 37">
                <NumberGeneratorField
                  v-model="field.value"
                  :number-key="field.default_value"
                  :disabled="confirmed"
                  :iss-pk="pk"
                  :field-pk="field.pk"
                />
              </div>
              <div class="field-value field-value-address mkb" v-else-if="field.field_type === 31">
                <TfomsAttachmentField v-model="field.value" :disabled="confirmed" :client-pk="patient.card_pk" />
              </div>
              <div class="field-value field-value-address mkb" v-else-if="field.field_type === 32">
                <MKBFieldTreeselect v-model="field.value" :disabled="confirmed" dictionary="mkb10.6" />
              </div>
              <div class="field-value field-value-address mkb" v-else-if="field.field_type === 33">
                <MKBFieldTreeselect v-model="field.value" :disabled="confirmed" dictionary="mkb10.5" />
              </div>
              <div class="field-value field-value-address mkb" v-else-if="field.field_type === 34">
                <MKBFieldTreeselect v-model="field.value" :disabled="confirmed" dictionary="mkb10.4" />
              </div>
              <div class="field-value field-value-address mkb" v-else-if="field.field_type === 35">
                <DoctorProfileTreeselectField v-model="field.value" :disabled="confirmed" />
              </div>
              <div class="field-value field-value-address mkb" v-else-if="field.field_type === 36">
                <MKBFieldTreeselect v-model="field.value" :disabled="confirmed" dictionary="mkb10.combined" />
              </div>
              <div
                :title="field.helper"
                class="field-helper"
                v-if="field.helper"
                v-tippy="{
                  placement: 'left',
                  arrow: true,
                  interactive: true,
                  theme: 'dark longread',
                }"
              >
                <i class="fa fa-question" />
              </div>
            </div>
          </visibility-field-wrapper>
        </div>
      </div>
    </visibility-group-wrapper>
  </div>
</template>

<script lang="ts">
import LPress from '@/ui-cards/LPress.vue';
import VisibilityGroupWrapper from '../components/VisibilityGroupWrapper.vue';
import VisibilityFieldWrapper from '../components/VisibilityFieldWrapper.vue';
import FastTemplates from './FastTemplates.vue';
import InputTemplates from './InputTemplates.vue';
import { enter_field, leave_field } from './utils';

export default {
  name: 'DescriptiveForm',
  components: {
    FastTemplates,
    InputTemplates,
    VisibilityGroupWrapper,
    VisibilityFieldWrapper,
    LPress,
    TextareaAutocomplete: () => import('../fields/TextareaAutocomplete.vue'),
    NumberRangeField: () => import('../fields/NumberRangeField.vue'),
    NumberField: () => import('../fields/NumberField.vue'),
    TableField: () => import('../fields/TableField.vue'),
    AggregateDesc: () => import('../fields/AggregateDesc.vue'),
    AggregateLaboratory: () => import('../fields/AggregateLaboratory.vue'),
    RichTextEditor: () => import('../fields/RichTextEditor.vue'),
    SearchFractionValueField: () => import('../fields/SearchFractionValueField.vue'),
    SearchFieldValueField: () => import('../fields/SearchFieldValueField.vue'),
    RadioField: () => import('../fields/RadioField.vue'),
    TreeSelectField: () => import('../fields/TreeSelectField.vue'),
    AnesthesiaProcess: () => import('../fields/AnesthesiaProcess.vue'),
    MKBFieldForm: () => import('../fields/MKBFieldForm.vue'),
    FormulaField: () => import('../fields/FormulaField.vue'),
    LaboratoryPreviousResults: () => import('../fields/LaboratoryPreviousResults.vue'),
    DiagnosticPreviousResults: () => import('../fields/DiagnosticPreviousResults.vue'),
    DocReferralPreviousResults: () => import('../fields/DocReferralPreviousResults.vue'),
    PermanentDirectoryField: () => import('../fields/PermanentDirectoryField.vue'),
    AddressFiasField: () => import('../fields/AddressFiasField.vue'),
    MKBFieldTreeselect: () => import('../fields/MKBFieldTreeselect.vue'),
    TextFieldWithTemplates: () => import('../fields/TextFieldWithTemplates.vue'),
    NumberGeneratorField: () => import('../fields/NumberGeneratorField.vue'),
    TfomsAttachmentField: () => import('../fields/TfomsAttachmentField.vue'),
    DoctorProfileTreeselectField: () => import('../fields/DoctorProfileTreeselectField.vue'),
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
      tableFieldsErrors: {},
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

    this.$root.$on('table-field:errors:set', (fieldPk, hasInvalid) => {
      this.tableFieldsErrors = {
        ...this.tableFieldsErrors,
        [fieldPk]: hasInvalid,
      };
    });
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
          if (
            (f.required
              && (f.value === ''
                || f.value === '- Не выбрано'
                || !f.value
                || (f.field_type === 29 && (f.value.includes('"address": ""') || f.value.includes('"address":""')))))
            || this.tableFieldsErrors[f.pk]
          ) {
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
      return newValue => {
        // eslint-disable-next-line no-param-reassign
        field.value = newValue;
      };
    },
    clear_val(field) {
      if (field.field_type === 29) {
        // eslint-disable-next-line no-param-reassign
        field.value = JSON.stringify({ address: '', fias: null });
      } else {
        // eslint-disable-next-line no-param-reassign
        field.value = '';
      }
    },
    clear_val_by_pk(pk) {
      const field = this.research.groups.reduce((a, b) => a.concat(b.fields), []).find(f => f.pk === pk);
      if (field) {
        this.clear_val(field);
      }
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
