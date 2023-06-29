<template>
  <div>
    <VisibilityGroupWrapper
      v-for="group in research.groups"
      :key="group.pk"
      :group="group"
      :groups="groups"
      :patient="patient"
    >
      <div class="group">
        <div
          v-if="group.title !== ''"
          class="group-title"
        >
          {{ group.title }}
        </div>
        <div
          class="fields"
          :class="{ 'fields-inline': group.fieldsInline }"
        >
          <VisibilityFieldWrapper
            v-for="field in group.fields"
            :key="field.pk"
            :formula="field.visibility"
            :group="group"
            :groups="research.groups"
            :patient="patient"
          >
            <div
              v-if="field.title !== '' && (research.wide_headers || group.fieldsInline)"
              class="wide-field-title"
            >
              <template v-if="field.title.endsWith('?') || field.title.endsWith(':')">
                {{ field.title }}
              </template>
              <template v-else>
                {{ field.title }}:
              </template>
            </div>
            <div
              :key="`field-${field.pk}`"
              :class="{
                disabled: confirmed,
                empty: notFilled.includes(field.pk),
                'field-vertical-simple': [16, 17].includes(field.field_type) && pk,
                required: field.required,
              }"
              :title="field.required && 'обязательно для заполнения'"
              class="field"
              v-on="{
                mouseenter: enter_field(field.values_to_input.length > 0),
                mouseleave: leave_field(field.values_to_input.length > 0),
              }"
            >
              <div
                v-if="field.title !== '' && !research.wide_headers && !group.fieldsInline"
                class="field-title"
              >
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
                      39: 1,
                    }[field.field_type]
                "
                :pk="field.pk"
                :on-confirm="clear_val_by_pk"
              />
              <InputTemplates
                v-if="!confirmed && [0].includes(field.field_type)"
                :field="field"
                :group="group"
              />
              <FastTemplates
                :update_value="updateValue(field)"
                :value="field.value"
                :values="field.values_to_input"
                :confirmed="confirmed || userGroups.includes(field.deniedGroup)"
                :field_type="field.field_type"
                :field_title="field.title"
              />
              <div
                v-if="field.field_type === 0"
                class="field-value field-value-with-templates"
              >
                <TextFieldWithTemplates
                  v-model="field.value"
                  :confirmed="confirmed || userGroups.includes(field.deniedGroup)"
                  :field-pk="field.pk"
                  :lines="field.lines"
                />
              </div>
              <div
                v-else-if="field.field_type === 1"
                class="field-value"
              >
                <input
                  v-model="field.value"
                  :readonly="confirmed || field.not_edit || userGroups.includes(field.deniedGroup)"
                  class="form-control"
                  style="width: 160px"
                  type="date"
                >
              </div>
              <div
                v-else-if="field.field_type === 2 && !confirmed && !userGroups.includes(field.deniedGroup)"
                class="field-value mkb10"
              >
                <MKBFieldForm
                  v-model="field.value"
                  :short="false"
                  :field-pk="field.default_value"
                  :iss_pk="pk"
                  :client-pk="patient.card_pk"
                  @input="change_mkb(field)"
                />
              </div>
              <div
                v-else-if="field.field_type === 3"
                class="field-value mkb10"
              >
                <FormulaField
                  v-model="field.value"
                  :fields="research.groups.reduce((a, b) => a.concat(b.fields), [])"
                  :formula="field.default_value"
                  :patient="patient"
                  :can-edit="field.can_edit"
                  :disabled="confirmed || field.not_edit || userGroups.includes(field.deniedGroup)"
                />
              </div>
              <div
                v-else-if="(field.field_type === 2 && confirmed) || userGroups.includes(field.deniedGroup)"
                class="field-value"
              >
                <input
                  v-model="field.value"
                  :readonly="true"
                  class="form-control"
                >
              </div>
              <div
                v-else-if="field.field_type === 10"
                class="field-value"
              >
                <TreeSelectField
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  :variants="field.values_to_input"
                />
              </div>
              <div
                v-else-if="field.field_type === 11"
                class="field-value"
              >
                <SearchFractionValueField
                  v-model="field.value"
                  :readonly="confirmed || field.not_edit || userGroups.includes(field.deniedGroup)"
                  :fraction-pk="field.default_value"
                  :client-pk="patient.card_pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 12"
                class="field-value"
              >
                <RadioField
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  :variants="field.values_to_input"
                />
              </div>
              <div
                v-else-if="field.field_type === 13 || field.field_type === 14 || field.field_type === 23"
                class="field-value"
              >
                <SearchFieldValueField
                  v-model="field.value"
                  :readonly="confirmed || field.not_edit || userGroups.includes(field.deniedGroup)"
                  :field-pk="field.default_value"
                  :client-pk="patient.card_pk"
                  :lines="field.lines"
                  :raw="field.field_type === 14 || field.field_type === 23"
                  :not_autoload_result="field.field_type === 23"
                  :iss_pk="pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 15"
                class="field-value"
              >
                <RichTextEditor
                  v-model="field.value"
                  :readonly="confirmed || field.not_edit || userGroups.includes(field.deniedGroup)"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                />
              </div>
              <div
                v-else-if="field.field_type === 16 && pk"
                class="field-value"
              >
                <AggregateLaboratory
                  v-model="field.value"
                  :pk="pk"
                  extract
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                />
              </div>
              <div
                v-else-if="field.field_type === 17 && pk && hospital_r_type"
                class="field-value"
              >
                <AggregateDesc
                  v-model="field.value"
                  :pk="pk"
                  extract
                  :r_type="hospital_r_type"
                />
              </div>
              <div
                v-else-if="field.field_type === 18"
                class="field-value"
              >
                <NumberField
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                />
              </div>
              <div
                v-else-if="field.field_type === 19"
                class="field-value"
              >
                <NumberRangeField
                  v-model="field.value"
                  :variants="field.values_to_input"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                />
              </div>
              <div
                v-else-if="field.field_type === 20"
                class="field-value"
              >
                <input
                  v-model="field.value"
                  :readonly="confirmed || field.not_edit || userGroups.includes(field.deniedGroup)"
                  class="form-control"
                  style="width: 110px"
                  type="time"
                >
              </div>
              <div
                v-else-if="field.field_type === 21"
                class="field-value"
              >
                <AnesthesiaProcess
                  :fields="field.values_to_input"
                  :iss="pk"
                  :field_pk="field.pk"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                />
              </div>
              <div
                v-else-if="field.field_type === 22"
                class="field-value"
              >
                <TextareaAutocomplete
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                />
              </div>
              <div
                v-else-if="field.field_type === 24"
                class="field-value"
              >
                <LaboratoryPreviousResults
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                />
              </div>
              <div
                v-else-if="field.field_type === 25"
                class="field-value"
              >
                <DiagnosticPreviousResults
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                />
              </div>
              <div
                v-else-if="field.field_type === 26"
                class="field-value"
              >
                <DocReferralPreviousResults
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                />
              </div>
              <div
                v-else-if="field.field_type === 27"
                class="field-value"
              >
                <TableField
                  v-model="field.value"
                  :variants="field.values_to_input"
                  :fields="research.groups.reduce((a, b) => a.concat(b.fields), [])"
                  :field-pk="field.pk"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  :card_pk="patient.card_pk"
                  :iss_pk="pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 28"
                class="field-value"
              >
                <PermanentDirectoryField
                  v-model="field.value"
                  :oid="field.values_to_input"
                  :field-title="field.title"
                  :disabled="confirmed || field.not_edit || userGroups.includes(field.deniedGroup)"
                  :field-pk="field.default_value"
                  :iss_pk="pk"
                  :client-pk="patient.card_pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 29"
                class="field-value field-value-address mkb"
              >
                <AddressFiasField
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  :client-pk="patient.card_pk"
                  :edit-title="`${group.title} ${field.title}`.trim()"
                  :strict="false"
                />
              </div>
              <div
                v-else-if="field.field_type === 30"
                class="field-value field-value-address mkb"
              >
                <NumberGeneratorField
                  v-model="field.value"
                  :number-key="field.default_value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  :iss-pk="pk"
                  :field-pk="field.pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 37"
                class="field-value field-value-address mkb"
              >
                <NumberGeneratorField
                  v-model="field.value"
                  :number-key="field.default_value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  :iss-pk="pk"
                  :field-pk="field.pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 31"
                class="field-value field-value-address mkb"
              >
                <TfomsAttachmentField
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  :client-pk="patient.card_pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 32"
                class="field-value field-value-address mkb"
              >
                <MKBFieldTreeselect
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  dictionary="mkb10.6"
                  :field-pk="field.default_value"
                  :iss_pk="pk"
                  :client-pk="patient.card_pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 33"
                class="field-value field-value-address mkb"
              >
                <MKBFieldTreeselect
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  dictionary="mkb10.5"
                  :field-pk="field.default_value"
                  :iss_pk="pk"
                  :client-pk="patient.card_pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 34"
                class="field-value field-value-address mkb"
              >
                <MKBFieldTreeselect
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  dictionary="mkb10.4"
                  :field-pk="field.default_value"
                  :iss_pk="pk"
                  :client-pk="patient.card_pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 35"
                class="field-value field-value-address mkb"
              >
                <DoctorProfileTreeselectField
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  :sign_org="field.sign_organization"
                />
              </div>
              <div
                v-else-if="field.field_type === 36"
                class="field-value field-value-address mkb"
              >
                <MKBFieldTreeselect
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  dictionary="mkb10.combined"
                  :field-pk="field.default_value"
                  :iss_pk="pk"
                  :client-pk="patient.card_pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 38"
                class="field-value"
              >
                <ProcedureListResult
                  v-model="field.value"
                  istresult
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  :pk="pk"
                />
              </div>
              <div
                v-else-if="field.field_type === 39"
                class="field-value field-value-address mkb"
              >
                <DynamicDirectoryField
                  v-model="field.value"
                  :disabled="confirmed || userGroups.includes(field.deniedGroup)"
                  :edit-title="`${group.title} ${field.title}`.trim()"
                  :directory="field.values_to_input[0]"
                />
              </div>
              <div
                v-if="field.helper"
                v-tippy="{
                  placement: 'left',
                  arrow: true,
                  interactive: true,
                  theme: 'dark longread',
                }"
                :title="field.helper"
                class="field-helper"
              >
                <i class="fa fa-question" />
              </div>
            </div>
          </VisibilityFieldWrapper>
        </div>
      </div>
    </VisibilityGroupWrapper>
  </div>
</template>

<script lang="ts">
import LPress from '@/ui-cards/LPress.vue';

import VisibilityGroupWrapper from '../components/VisibilityGroupWrapper.vue';
import VisibilityFieldWrapper from '../components/VisibilityFieldWrapper.vue';
import FastTemplates from './FastTemplates.vue';
import InputTemplates from './InputTemplates.vue';
import { enterField, leaveField } from './utils';

export default {
  name: 'DescriptiveForm',
  components: {
    FastTemplates,
    InputTemplates,
    VisibilityGroupWrapper,
    VisibilityFieldWrapper,
    LPress,
    TextareaAutocomplete: () => import('@/fields/TextareaAutocomplete.vue'),
    NumberRangeField: () => import('@/fields/NumberRangeField.vue'),
    NumberField: () => import('@/fields/NumberField.vue'),
    TableField: () => import('@/fields/TableField.vue'),
    AggregateDesc: () => import('@/fields/AggregateDesc.vue'),
    AggregateLaboratory: () => import('@/fields/AggregateLaboratory.vue'),
    RichTextEditor: () => import('@/fields/RichTextEditor.vue'),
    SearchFractionValueField: () => import('@/fields/SearchFractionValueField.vue'),
    SearchFieldValueField: () => import('@/fields/SearchFieldValueField.vue'),
    RadioField: () => import('@/fields/RadioField.vue'),
    TreeSelectField: () => import('@/fields/TreeSelectField.vue'),
    AnesthesiaProcess: () => import('@/fields/AnesthesiaProcess.vue'),
    MKBFieldForm: () => import('@/fields/MKBFieldForm.vue'),
    FormulaField: () => import('@/fields/FormulaField.vue'),
    LaboratoryPreviousResults: () => import('@/fields/LaboratoryPreviousResults.vue'),
    DiagnosticPreviousResults: () => import('@/fields/DiagnosticPreviousResults.vue'),
    DocReferralPreviousResults: () => import('@/fields/DocReferralPreviousResults.vue'),
    PermanentDirectoryField: () => import('@/fields/PermanentDirectoryField.vue'),
    AddressFiasField: () => import('@/fields/AddressFiasField.vue'),
    MKBFieldTreeselect: () => import('@/fields/MKBFieldTreeselect.vue'),
    TextFieldWithTemplates: () => import('@/fields/TextFieldWithTemplates.vue'),
    NumberGeneratorField: () => import('@/fields/NumberGeneratorField.vue'),
    TfomsAttachmentField: () => import('@/fields/TfomsAttachmentField.vue'),
    DoctorProfileTreeselectField: () => import('@/fields/DoctorProfileTreeselectField.vue'),
    ProcedureListResult: () => import('@/fields/ProcedureListResult.vue'),
    DynamicDirectoryField: () => import('@/fields/DynamicDirectoryField.vue'),
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
    userGroups() {
      return this.$store.getters.user_data.groups || [];
    },
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
  methods: {
    inc_version() {
      // eslint-disable-next-line vue/no-mutating-props
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
      return enterField.apply(this, args);
    },
    leave_field(...args) {
      return leaveField.apply(this, args);
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

.fields-inline {
  display: flex;
  flex-direction: row;
  justify-content: stretch;

  > div {
    align-self: stretch;
    flex: 1 1 0;
  }

  &:not(:first-child) {
    > div {
      padding-left: 5px;
    }
  }

  .wide-field-title {
    padding-left: 0;
  }
}
</style>
