<template>
  <div>
    <div class="input-group">
      <input
        v-model="form.family"
        class="form-control"
        placeholder="Фамилия"
        maxlength="120"
      >
      <span
        class="input-group-btn"
        style="width:0"
      />
      <input
        v-model="form.name"
        class="form-control"
        placeholder="Имя"
        maxlength="120"
      >
      <span
        class="input-group-btn"
        style="width:0"
      />
      <input
        v-model="form.patronymic"
        class="form-control"
        placeholder="Отчество"
        maxlength="120"
      >
      <span
        class="input-group-btn"
        style="width:0"
      />
      <input
        v-model="form.birthday"
        v-mask="'99.99.9999'"
        class="form-control"
        placeholder="Дата рождения"
      >
    </div>
    <div class="input-group mt15">
      <span class="input-group-addon addon-fixed">Полис ОМС</span>
      <input
        v-model="form.enp_s"
        class="form-control"
        placeholder="серия"
        maxlength="30"
      >
      <span
        class="input-group-btn"
        style="width:0"
      />
      <input
        v-model="form.enp_n"
        class="form-control"
        placeholder="номер"
        maxlength="30"
      >
    </div>
    <div class="input-group mt5">
      <span class="input-group-addon addon-fixed">Паспорт</span>
      <input
        v-model="form.pass_s"
        class="form-control"
        placeholder="серия"
        maxlength="30"
      >
      <span
        class="input-group-btn"
        style="width:0"
      />
      <input
        v-model="form.pass_n"
        class="form-control"
        placeholder="номер"
        maxlength="30"
      >
    </div>
    <div class="input-group mt5">
      <span class="input-group-addon addon-fixed">СНИЛС</span>
      <input
        v-model="form.snils"
        class="form-control"
        placeholder="номер"
        maxlength="30"
      >
    </div>
    <div
      v-if="l2_profcenter"
      class="input-group mt5"
    >
      <span class="input-group-addon addon-fixed">Мед.книжка</span>
      <input
        v-model="form.medbookNumber"
        class="form-control"
        placeholder="номер (без префикса)"
        maxlength="16"
      >
    </div>
    <div class="row mt5">
      <div class="col-xs-8">
        <div class="input-group">
          <span class="input-group-addon addon-fixed">Телефон</span>
          <input
            v-model="form.phone"
            v-mask="'8 999 9999999'"
            class="form-control"
            placeholder="телефон"
          >
        </div>
      </div>
      <div class="col-xs-4 text-right">
        <label class="form-label"><input
          v-model="form.archive"
          type="checkbox"
        > включая архив</label>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Vue, { PropType } from 'vue';
import Component from 'vue-class-component';
import _ from 'lodash';
import { debounce } from 'lodash/function';

import { PatientForm } from '@/ui-cards/ExtendedPatientSearch/types';

const makeForm = (): PatientForm => ({
  family: '',
  name: '',
  patronymic: '',
  birthday: '',
  enp_s: '',
  enp_n: '',
  pass_s: '',
  pass_n: '',
  snils: '',
  phone: '',
  medbookNumber: '',
  archive: false,
});

@Component({
  props: {
    value: {
      type: Object as PropType<PatientForm | null>,
      default: '',
    },
  },
  mounted() {
    this.$root.$on('extended-patient-search:reset-patient-form', () => this.clearForm());
  },
  data() {
    return {
      form: makeForm(),
    };
  },
  watch: {
    form: {
      immediate: true,
      deep: true,
      handler() {
        this.debouncedEmit();
      },
    },
    value() {
      if (this.value && !_.isEqual(this.form, this.value)) {
        this.form = this.value;
      }
    },
  },
  model: {
    event: 'modified',
  },
  computed: {
    l2_profcenter() {
      return this.$store.getters.modules.l2_profcenter;
    },
  },
})
export default class PatientSearchForm extends Vue {
  form: PatientForm;

  l2_profcenter: boolean;

  clearForm() {
    this.form = makeForm();
  }

  debouncedEmit = debounce(function () {
    this.emit();
  }, 100);

  emit() {
    this.$emit(
      'modified',
      Object.keys(this.form).reduce(
        (a, k) => ({ ...a, [k]: typeof this.form[k] === 'string' ? this.form[k].trim() : this.form[k] }),
        {},
      ),
    );
  }
}
</script>

<style lang="scss" scoped>
.addon-fixed {
  width: 140px;
  text-align: left;
}

.mt15 {
  margin-top: 15px;
}

.input-group {
  width: 100%;
}

.form-label {
  line-height: 34px;

  input[type='checkbox'] {
    vertical-align: text-top;
  }
}
</style>
