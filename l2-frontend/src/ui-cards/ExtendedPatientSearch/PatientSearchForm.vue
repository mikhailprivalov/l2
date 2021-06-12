<template>
  <div>
    <div class="input-group">
      <input class="form-control" placeholder="Фамилия" v-model="form.family" maxlength="120">
      <span class="input-group-btn" style="width:0"></span>
      <input class="form-control" placeholder="Имя" v-model="form.name" maxlength="120">
      <span class="input-group-btn" style="width:0"></span>
      <input class="form-control" placeholder="Отчество" v-model="form.patronymic" maxlength="120">
      <span class="input-group-btn" style="width:0"></span>
      <input class="form-control" v-model="form.birthday" placeholder="Дата рождения" v-mask="'99.99.9999'">
    </div>
    <div class="input-group mt15">
      <span class="input-group-addon addon-fixed">Полис ОМС</span>
      <input class='form-control' v-model="form.enp_s" placeholder="серия" maxlength="30"/>
      <span class="input-group-btn" style="width:0"></span>
      <input class='form-control' v-model="form.enp_n" placeholder="номер" maxlength="30"/>
    </div>
    <div class="input-group mt5">
      <span class="input-group-addon addon-fixed">Паспорт</span>
      <input class='form-control' v-model="form.pass_s" placeholder="серия" maxlength="30"/>
      <span class="input-group-btn" style="width:0"></span>
      <input class='form-control' v-model="form.pass_n" placeholder="номер" maxlength="30"/>
    </div>
    <div class="input-group mt5">
      <span class="input-group-addon addon-fixed">СНИЛС</span>
      <input class='form-control' v-model="form.snils" placeholder="номер" maxlength="30"/>
    </div>
    <div class="input-group mt5" v-if="l2_profcenter">
      <span class="input-group-addon addon-fixed">Мед.книжка</span>
      <input class='form-control' v-model="form.medbookNumber" placeholder="номер" maxlength="16"/>
    </div>
    <div class="input-group mt5">
      <span class="input-group-addon addon-fixed">Телефон</span>
      <input class='form-control' v-model="form.phone" placeholder="телефон" v-mask="'8 999 9999999'"/>
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

  clearForm() {
    this.form = makeForm();
  }

  debouncedEmit = debounce(function () {
    this.emit();
  }, 100);

  emit() {
    this.$emit('modified', Object.keys(this.form).reduce((a, k) => ({ ...a, [k]: this.form[k].trim() }), {}));
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

</style>
