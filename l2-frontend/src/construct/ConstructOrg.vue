<template>
  <div v-frag>
    <div class="card-no-hover card card-1">
      <h4 class="text-center">Настройка данных организации</h4>
      <FormulateForm v-model="org" @submit="save">
        <div class="row f-row">
          <div class="col-xs-6">
            <FormulateInput
              type="text"
              name="title"
              validation-name="Полное название"
              error-behavior="live"
              label="Полное название"
              required
              validation="required"
            />
            <FormulateInput type="text" name="shortTitle" label="Краткое название" />
            <FormulateInput type="text" name="address" label="Адрес" />
            <FormulateInput type="text" name="phones" label="Телефоны" />
            <FormulateInput type="text" name="ogrn" label="ОГРН" maxlength="13" />
          </div>
          <div class="col-xs-6">
            <FormulateInput type="text" name="currentManager" label="Главный врач" />
            <FormulateInput type="text" name="licenseData" label="Лицензия" />
            <FormulateInput type="text" name="www" label="Сайт" />
            <FormulateInput type="text" name="email" label="Email" />
          </div>
        </div>
        <FormulateInput type="submit" label="Сохранить" :disabled="loading" />

        <div class="journal-warning">
          Изменения будут записаны в журнал.<br />
          <strong>Обновлённые данные будут отображены на печатных бланках, в отчётах и в интерфейсе L2</strong>
        </div>
      </FormulateForm>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import * as actions from '@/store/action-types';

@Component({
  data() {
    return {
      org: {},
      loading: false,
    };
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { org } = await this.$api('/current-org');
    this.org = org;
    await this.$store.dispatch(actions.DEC_LOADING);
  },
})
export default class ConstructOrg extends Vue {
  org: any;

  loading: boolean;

  async save() {
    this.loading = true;
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message } = await this.$api('/current-org-update', this.org);
    if (ok) {
      this.$root.$emit('msg', 'ok', 'Изменения сохранены');
      await this.$store.dispatch(actions.GET_USER_DATA);
    } else {
      this.$root.$emit('msg', 'error', message);
    }
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loading = false;
  }
}
</script>

<style lang="scss" scoped>
.card {
  padding: 6px 12px;
  margin-left: 0;
  margin-right: 0;
  margin-bottom: 18px;
}

::v-deep .formulate-input .formulate-input-element {
  max-width: 1000px;
}

.f-row {
  margin-bottom: 15px;
}

.journal-warning {
  margin: 10px 0;
  padding: 10px;
  background-color: rgba(0, 0, 0, 8%);
  border-radius: 4px;
}
</style>
