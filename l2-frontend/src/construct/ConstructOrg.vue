<template>
  <div v-frag>
    <div class="card-no-hover card card-1">
      <h4 class="text-center">
        Настройка данных организации
      </h4>
      <FormulateForm
        v-model="org"
        @submit="save"
      >
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
            <FormulateInput
              type="text"
              name="shortTitle"
              label="Краткое название"
            />
            <FormulateInput
              type="text"
              name="address"
              label="Адрес"
            />
            <FormulateInput
              type="text"
              name="phones"
              label="Телефоны"
            />
            <FormulateInput
              type="text"
              name="ogrn"
              label="ОГРН"
              maxlength="13"
            />
          </div>
          <div class="col-xs-6">
            <FormulateInput
              type="text"
              name="currentManager"
              label="Главный врач"
            />
            <FormulateInput
              type="text"
              name="licenseData"
              label="Лицензия"
            />
            <FormulateInput
              type="text"
              name="www"
              label="Сайт"
            />
            <FormulateInput
              type="text"
              name="email"
              label="Email"
            />
            <FormulateInput
              type="text"
              name="okpo"
              label="ОКПО"
            />
          </div>
        </div>
        <FormulateInput
          type="submit"
          label="Сохранить"
          :disabled="loading"
        />

        <div class="journal-warning">
          Изменения будут записаны в журнал.<br>
          <strong>Обновлённые данные будут отображены на печатных бланках, в отчётах и в интерфейсе {{ system }}</strong>
        </div>
      </FormulateForm>
    </div>

    <div
      v-if="numberGeneratorEnabled"
      class="card-no-hover card card-1"
    >
      <h4 class="text-center">
        Генераторы номеров
      </h4>

      <table class="table table-bordered">
        <thead>
          <tr>
            <th>Тип</th>
            <th>Год</th>
            <th>Активен</th>
            <th>Начало</th>
            <th>Конец</th>
            <th>Последнее значение</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="g in generators"
            :key="g.pk"
          >
            <td>{{ g.keyDisplay }}</td>
            <td>{{ g.year }}</td>
            <td>
              <span
                v-if="g.isActive"
                class="badge badge-success"
              >да</span>
              <span
                v-else
                class="badge badge-warning"
              >нет</span>
            </td>
            <td>{{ g.start }}</td>
            <td>{{ g.end }}</td>
            <td>{{ g.last }}</td>
          </tr>
        </tbody>
      </table>

      <h5>Добавить новый или заменить генератор</h5>

      <FormulateForm
        v-model="generator"
        @submit="saveGenerator"
      >
        <FormulateInput
          key="key"
          name="key"
          :options="{ deathFormNumber: 'Номер свидетельства о смерти', tubeNumber: 'Номер ёмкости биоматериала' }"
          type="select"
          placeholder="Выберите тип генератора"
          label="Тип генератора"
          required
        />
        <FormulateInput
          v-if="generator.key !== 'tubeNumber'"
          key="year"
          type="number"
          name="year"
          label="Год"
          :min="2021"
          :max="3000"
          required
        />
        <FormulateInput
          key="start"
          type="number"
          name="start"
          label="Начало (первое значение)"
          :max="generator.end"
          required
        />
        <FormulateInput
          key="end"
          type="number"
          name="end"
          label="Конец (последнее значение)"
          :min="generator.start || 0"
          :required="generator.key !== 'tubeNumber'"
        />
        <FormulateInput
          v-if="generator.key !== 'tubeNumber'"
          key="prependLength"
          type="number"
          name="prependLength"
          label="Количестов символов для добавления нулей в начало"
          :min="0"
          :max="20"
          required
        />
        <FormulateInput
          type="submit"
          label="Сохранить"
          :disabled="loading"
        />

        <div class="journal-warning">
          Существующие генераторы такого же типа и с тем же годом будут деактивированы.<br>
          Изменения будут записаны в журнал.
        </div>
      </FormulateForm>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment from 'moment';

import * as actions from '@/store/action-types';

const newGenerator = () => ({
  key: 'deathFormNumber',
  year: moment().year(),
  start: '',
  end: '',
  prependLength: 8,
});

@Component({
  data() {
    return {
      org: {},
      loading: false,
      generators: [],
      generator: newGenerator(),
    };
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { org } = await this.$api('/current-org');
    this.org = org;
    await this.loadGenerators();
    await this.$store.dispatch(actions.DEC_LOADING);
  },
})
export default class ConstructOrg extends Vue {
  org: any;

  generators: any[];

  generator: any;

  loading: boolean;

  get system() {
    return this.$systemTitle();
  }

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

  get numberGeneratorEnabled() {
    return this.$store.getters.modules.number_generator_field;
  }

  async loadGenerators() {
    await this.$store.dispatch(actions.INC_LOADING);
    if (this.numberGeneratorEnabled) {
      const { rows } = await this.$api('/org-generators');
      this.generators = rows;
    }
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async saveGenerator() {
    this.loading = true;
    await this.$store.dispatch(actions.INC_LOADING);
    await this.$api('/org-generators-add', this.generator);
    this.generator = newGenerator();
    await this.loadGenerators();
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
