<template>
  <div v-frag>
    <div class="card-no-hover card card-1">
      <h4 class="text-center">
        Настройка данных организации
      </h4>

      <div class="org-top-row">
        <div
          v-if="hasAccessToAllHospitals"
          class="input-group treeselect-noborder-left org-selector"
        >
          <span class="input-group-addon">Организация</span>
          <treeselect
            v-model="hospitalId"
            :multiple="false"
            :disable-branch-nodes="true"
            :options="hospitals"
            placeholder="Организация не выбрана"
            :clearable="false"
            class="treeselect-wide"
          />
        </div>
        <div class="org-top-checks">
          <label class="org-top-check">
            <input
              v-model="strictDataOwnership"
              type="checkbox"
            >
            Доступ к себе
          </label>
          <label class="org-top-check">
            <input
              v-model="hide"
              type="checkbox"
            >
            Скрыть
          </label>
        </div>
      </div>

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
            <FormulateInput
              type="text"
              name="hl7SenderApplication"
              label="HL7 приложение отправитель"
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
            <FormulateInput
              type="text"
              name="hl7ReceiverAapplication"
              label="HL7 приложение получатель"
              maxlength="13"
            />
          </div>
        </div>

        <div class="row f-row">
          <div class="col-xs-6">
            <FormulateInput
              type="text"
              name="oid"
              label="OID"
              maxlength="128"
            />
          </div>
          <div class="col-xs-6">
            <FormulateInput
              type="text"
              name="timeZone"
              label="Часовой пояс"
              maxlength="100"
            />
          </div>
        </div>

        <div class="row f-row">
          <div class="col-xs-6">
            <div class="org-fin-source">
              <label class="org-field-label">Источник финансирования по умолчанию</label>
              <treeselect
                v-model="defaultFinSource"
                :multiple="false"
                :options="finSourceOptions"
                placeholder="Не выбран"
                class="treeselect-wide"
              />
            </div>
          </div>
          <div class="col-xs-6">
            <div class="schema-docx">
              <label class="org-field-label">Шаблон DOCX результата по больнице заявки</label>
              <div class="schema-docx-row">
                <span>{{ schemaDocxName || 'Файл не загружен' }}</span>
                <button
                  type="button"
                  class="btn btn-blue-nb"
                  @click="pickSchemaDocx"
                >
                  {{ schemaDocxName ? 'Заменить' : 'Добавить' }}
                </button>
                <button
                  v-if="schemaDocxName"
                  type="button"
                  class="btn btn-blue-nb"
                  @click="clearSchemaDocx"
                >
                  Убрать
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="row f-row">
          <div class="col-xs-12">
            <div class="org-fin-source">
              <label class="org-field-label">Недоступные источники финансирования</label>
              <treeselect
                v-model="disabledFinSources"
                :multiple="true"
                :options="finSourceOptions"
                placeholder="Нет запретов"
                class="treeselect-wide"
              />
            </div>
          </div>
        </div>

        <template v-if="ftp && hasAccessToAllHospitals">
          <div class="full-width show-layout">
            <FormulateInput
              type="checkbox"
              name="needSendMail"
              label="Отправлять результаты на почту"
            />
          </div>
          <div class="full-width">
            <FormulateInput
              type="text"
              name="ordersPullFtpServerUrl"
              label="URL для FTP директории получения заказов"
            />
          </div>
          <div class="full-width">
            <FormulateInput
              type="checkbox"
              name="strictTubeNumbers"
              label="Требовать наличие интервалов/генератора номеров ёмкостей при получении заказов"
            />
          </div>
          <div class="full-width">
            <FormulateInput
              type="checkbox"
              name="isAutotransfer"
              label="Автоматически пересылать"
            />
          </div>
          <div class="full-width">
            <FormulateInput
              type="text"
              name="ordersPushFtpServerUrl"
              label="URL для FTP директории отправки заказов"
            />
          </div>
          <div class="full-width">
            <FormulateInput
              type="checkbox"
              name="isExternalPerformingOrganization"
              label="Организация является внешним исполнителем"
            />
          </div>
          <div class="full-width">
            <FormulateInput
              type="checkbox"
              name="strictExternalNumbers"
              label="Требовать наличие генератора номеров ёмкостей при отправке заказов"
            />
          </div>
          <div class="full-width">
            <FormulateInput
              type="text"
              name="resultPullFtpServerUrl"
              label="URL для FTP директории получения результатов"
            />
          </div>
        </template>

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
            <td v-if="g.key !== 'tubeNumber' && g.key !== 'externalOrderNumber'">
              {{ g.year }}
            </td>
            <td v-else />
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
          :options="availableGenerators"
          type="select"
          placeholder="Выберите тип генератора"
          label="Тип генератора"
          required
        />
        <FormulateInput
          v-if="generator.key !== 'tubeNumber' && generator.key !== 'externalOrderNumber'"
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
          :required="generator.key !== 'tubeNumber' && generator.key !== 'externalOrderNumber'"
        />
        <FormulateInput
          v-if="generator.key !== 'tubeNumber' && generator.key !== 'externalOrderNumber'"
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
          Существующие генераторы такого же
          типа {{
            (generator.key !== 'tubeNumber' && generator.key !== 'externalOrderNumber') ? 'и с тем же годом ' : ''
          }}будут деактивированы.<br>
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
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import * as actions from '@/store/action-types';
import { selectFile } from '@/utils';

@Component({
  components: { Treeselect },
  data() {
    return {
      hospitalId: null,
      hospitals: [],
      org: {},
      strictDataOwnership: true,
      hide: false,
      defaultFinSource: null,
      disabledFinSources: [],
      finSourceOptions: [],
      schemaDocxName: '',
      schemaDocxResult: null,
      clearSchemaDocxResult: false,
      loading: false,
      generators: [],
      generator: {},
    };
  },
  watch: {
    hospitalId() {
      if (this.hospitalId !== null) {
        this.loadOrgData();
      }
    },
    userHospital: {
      immediate: true,
      handler() {
        if (this.hospitalId === null) {
          this.hospitalId = this.userHospital;
        }
      },
    },
  },
})
export default class ConstructOrg extends Vue {
  hospitalId: number | null;

  hospitals: any[];

  org: any;

  strictDataOwnership: boolean;

  hide: boolean;

  defaultFinSource: number | null;

  disabledFinSources: number[];

  finSourceOptions: Array<{ id: number; label: string }>;

  schemaDocxName: string;

  schemaDocxResult: { name: string; content: string } | null;

  clearSchemaDocxResult: boolean;

  generators: any[];

  generator: any;

  loading: boolean;

  get availableGenerators() {
    const generators: Record<string, string> = {};

    if (!this.disableDeathCert) {
      generators.deathFormNumber = 'Номер свидетельства о смерти';
    }

    generators.tubeNumber = 'Номер ёмкости биоматериала';

    if (this.ftp) {
      generators.externalOrderNumber = 'Номер внешнего заказ для отправки';
    }

    return generators;
  }

  get system() {
    return this.$systemTitle();
  }

  get userData() {
    return this.$store.getters.user_data;
  }

  get userHospital() {
    return this.userData.hospital;
  }

  get hasAccessToAllHospitals() {
    return (this.userData.groups || []).includes('Конструктор: Настройка всех организаций');
  }

  get disableDeathCert() {
    return this.$store.getters.modules.l2_disable_death_cert;
  }

  get ftp() {
    return this.$store.getters.modules.l2_ftp;
  }

  async save() {
    this.loading = true;
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message } = await this.$api('organization-data-update', {
      ...this.org,
      strictDataOwnership: this.strictDataOwnership,
      hide: this.hide,
      defaultFinSource: this.defaultFinSource,
      disabledFinSources: this.disabledFinSources || [],
      schemaDocxResult: this.schemaDocxResult,
      clearSchemaDocxResult: this.clearSchemaDocxResult,
    });
    if (ok) {
      this.$ok('Изменения сохранены');
      await this.$store.dispatch(actions.GET_USER_DATA);
      await this.loadHospitals();
      await this.loadOrgData();
    } else {
      this.$error(message);
    }
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loading = false;
  }

  async loadHospitals() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { hospitals } = await this.$api('hospitals', { strictMode: true });

    this.hospitals = hospitals;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async loadOrgData() {
    await this.$store.dispatch(actions.INC_LOADING);

    if (this.hospitals.length === 0) {
      await this.loadHospitals();
      this.generator = this.newGenerator(this.disableDeathCert ? 'tubeNumber' : 'deathFormNumber');
    }

    const { org } = await this.$api('organization-data', this, 'hospitalId');
    this.org = org;
    const finSourceOptions = org.finSources || [];
    const defaultFinSource = org.defaultFinSource ?? null;
    this.strictDataOwnership = !!org.strictDataOwnership;
    this.hide = !!org.hide;
    this.finSourceOptions = finSourceOptions;
    this.defaultFinSource = finSourceOptions.some((row) => row.id === defaultFinSource) ? defaultFinSource : null;
    const disabledFinSources = Array.isArray(org.disabledFinSources) ? org.disabledFinSources : [];
    this.disabledFinSources = disabledFinSources.filter((id) => finSourceOptions.some((row) => row.id === id));
    this.schemaDocxName = org.schemaDocxResultName || '';
    this.schemaDocxResult = null;
    this.clearSchemaDocxResult = false;
    await this.loadGenerators();
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  get numberGeneratorEnabled() {
    return this.$store.getters.modules.number_generator_field;
  }

  async loadGenerators() {
    await this.$store.dispatch(actions.INC_LOADING);
    if (this.numberGeneratorEnabled) {
      const { rows } = await this.$api('org-generators', this, 'hospitalId');
      this.generators = rows;
    }
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async saveGenerator() {
    this.loading = true;
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message } = await this.$api('org-generators-add', {
      hospitalId: this.hospitalId,
      ...this.generator,
    });
    if (!ok) {
      this.$error(message || 'Ошибка');
    } else {
      this.generator = this.newGenerator(this.generator.key);
    }
    await this.loadGenerators();
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loading = false;
  }

  async pickSchemaDocx() {
    const file = await selectFile('.docx');
    if (!file) {
      return;
    }
    if (!file.name.toLowerCase().endsWith('.docx')) {
      this.$error('Нужен файл .docx');
      return;
    }
    let content = '';
    try {
      content = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ''));
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
      });
    } catch {
      this.$error('Не удалось прочитать файл');
      return;
    }
    this.schemaDocxName = file.name;
    this.schemaDocxResult = { name: file.name, content };
    this.clearSchemaDocxResult = false;
  }

  clearSchemaDocx() {
    this.schemaDocxName = '';
    this.schemaDocxResult = null;
    this.clearSchemaDocxResult = true;
  }

  // eslint-disable-next-line class-methods-use-this
  newGenerator(key) {
    return {
      key,
      year: moment().year(),
      start: '',
      end: '',
      prependLength: 8,
    };
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

.full-width ::v-deep .formulate-input .formulate-input-element {
  max-width: 100%;
}

.show-layout {
  display: flex;
}

.layout-padding-send-mail {
  padding-left: 40px;
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

.org-top-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 15px;
}

.org-selector {
  flex: 1 1 auto;
  margin-bottom: 0;
  min-width: 0;
}

.org-top-checks {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: auto;
}

.org-top-check {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-weight: normal;
}

.org-fin-source,
.schema-docx {
  margin-bottom: 0;
}

.org-field-label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
}

.schema-docx-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
