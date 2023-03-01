<template>
  <div>
    <template v-if="Boolean(mode)">
      <div>{{ modeTitle }}</div>
      <div v-if="mode === 'formula'">
        <ul>
          <li
            v-for="l in formulaLinks"
            :key="`${l.type}-${l.id}`"
          >
            <u>{{ LINK_TITLES[l.type] }} {{ l.id }}</u>:
            <span v-if="fieldsAsObject[l.id]">{{ fieldsAsObject[l.id] }}</span>
            <strong v-else>значение не найдено</strong>
          </li>
        </ul>
      </div>
      <div v-else-if="mode === 'fraction'">
        <u>Фракция {{ value }}</u>:
        <span v-if="loading">загрузка...</span>
        <span v-else-if="fractions[value.trim()]">{{ fractions[value.trim()] }}</span>
        <strong v-else>фракция не найдена</strong>
      </div>
      <div v-else>
        <div
          v-if="fieldsAndGroups.sign === '&'"
          class="bold"
        >
          Объединение полей или групп
        </div>
        <div
          v-if="fieldsAndGroups.sign === '|'"
          class="bold"
        >
          Одно из полей или групп
        </div>
        <div
          v-if="fieldsAndGroups.ids.length === 1"
          class="bold"
        >
          Одно поле или группа
        </div>
        <ul>
          <li
            v-for="fg in fieldsAndGroups.ids"
            :key="fg"
          >
            <u>
              {{ fg.endsWith('@') ? 'Группа' : fg.startsWith('%') ? 'Ссылка на значение в базе' : 'Поле' }}
              {{ fg.replace('@', '') }}:
            </u>
            <span v-if="loading">загрузка</span>
            <span v-else-if="fieldsAndGroupsCache[fg]">{{ fieldsAndGroupsCache[fg] }}</span>
            <strong v-else>не найдено</strong>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script lang="ts">
import _ from 'lodash';
import { debounce } from 'lodash/function';

import { LINK_FIELD, LINK_PATIENT, PrepareFormula } from '@/utils';
import laboratoryPoint from '@/api/laboratory-point';
import researchesPoint from '@/api/researches-point';

const fieldModes = {
  3: 'formula',
  11: 'fraction',
  13: 'field',
  14: 'field',
  23: 'field-and-group',
};

const modeTitles = {
  formula: 'Формульные ссылки на значения из того же направления',
  fraction: 'Ссылка на фракцию (лаборатория)',
};

const DB_LINKS = {
  '%work_place': 'Место работы пациента',
  '%hospital': 'Больница направления',
  '%main_address': 'Адрес регистрации пациента (строкой)',
  '%full_main_address': 'Адрес регистрации пациента (полный)',
  '%docprofile': 'Текущий пользователь (врач)',
  '%patient_fio': 'ФИО пациента',
  '%patient_family': 'Фамилия пациента',
  '%patient_born': 'Дата рождения пациента',
  '%snils': 'СНИЛС пациента',
  '%polis_enp': 'ЕНП пациента',
  '%fact_address': 'Адрес фактического проживания пациента (строкой)',
  '%full_fact_address': 'Адрес фактического проживания пациента (полный)',
  '%phone': 'Телефон пациента',
  '%current_manager': 'Главный врач больницы направления',
  '%work_position': 'Должность пациента',
  '%work_department': 'Подразделение места работы пациента',
  '%harmful_factor': 'Фактор вредности пациента',
  '%proto_operation': 'proto_operation',
  '%proto_description': 'proto_description',
  '%doc_position': 'Должность врача',
  '%mother_family': 'Мать-Фамилия',
  '%mother_name': 'Мать-Имя',
  '%mother_patronymic': 'Мать-Отчество',
  '%mother_born': 'Мать-Дата рождения',
  '%mother_snils': 'Мать-СНИЛС',
  '%mother_polis_enp': 'Мать-ЕНП',
  '%mother_document_type': 'Мать-Тип Документа',
  '%mother_passport_num': 'Мать-паспорт-номер',
  '%mother_passport_serial': 'Мать-паспорт-серия',
  '%mother_passport_who': 'Мать-паспорт-кто выдал',
  '%mother_passport_date_issue': 'Мать-паспорт-дата выдачи',
  '%mother_full_main_address': 'Мать-Адрес регистрации пациента (полный)',
};

export default {
  name: 'FieldHelper',
  props: {
    fieldType: {
      type: Number,
      required: true,
    },
    value: {
      type: String,
      required: true,
    },
    groups: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      LINK_FIELD,
      LINK_PATIENT,
      LINK_TITLES: {
        LINK_FIELD: 'Поле',
        LINK_PATIENT: 'Данные пациента',
      },
      fractions: {},
      fieldsAndGroupsCache: {
        ...DB_LINKS,
      },
      loading: false,
    };
  },
  computed: {
    mode() {
      return fieldModes[this.fieldType];
    },
    modeTitle() {
      return modeTitles[this.mode];
    },
    formulaLinks() {
      if (this.mode !== 'formula') {
        return null;
      }

      return PrepareFormula([], this.value, {}, false, true);
    },
    fieldsAsObject() {
      if (this.mode !== 'formula') {
        return null;
      }

      return _.flatten(this.groups.map((g) => g.fields.map((f) => ({ pk: f.pk, title: f.title, group: g.title }))))
        .filter((f: { pk?: number }) => f.pk && f.pk > -1)
        .reduce(
          (a: any, b: any) => ({ ...a, [b.pk]: `${b.group || 'группа без названия'} – ${b.title || 'поле без названия'}` }),
          { age: 'возраст', sex: 'пол' },
        );
    },
    fieldsAndGroups() {
      if (this.mode === 'formula' || this.mode === 'fraction' || typeof this.value !== 'string') {
        return null;
      }
      const signAND = this.value.includes('&');
      const signOR = this.value.includes('|');
      const sign = !signAND && !signOR ? '-' : (signAND && '&') || '|';
      const ids = _.uniq(this.value.trim().split(sign).filter(Boolean));

      return { ids, sign };
    },
  },
  watch: {
    value: {
      handler() {
        this.updated();
      },
    },
  },
  mounted() {
    this.loadFractionFast();
    this.loadFieldsAndGroupsFast();
  },
  methods: {
    loadFraction: debounce(function () {
      this.loadFractionFast();
    }, 300),
    async loadFractionFast() {
      if (this.mode !== 'fraction') {
        return;
      }
      this.loading = true;
      const { title } = await laboratoryPoint.getFraction({ pk: Number(this.value) || -1 });
      this.fractions = { ...this.fractions, [this.value.trim()]: title };
      this.loading = false;
    },
    loadFieldsAndGroups: debounce(function () {
      this.loadFieldsAndGroupsFast();
    }, 400),
    async loadFieldsAndGroupsFast() {
      if (!this.fieldsAndGroups) {
        return;
      }
      const ids = this.fieldsAndGroups.ids.filter((i) => !this.fieldsAndGroupsCache[i]);
      if (ids.length > 0) {
        this.loading = true;
        const { titles } = await researchesPoint.getFieldsAndGroups({ ids });
        this.fieldsAndGroupsCache = { ...this.fieldsAndGroupsCache, ...titles };
        this.loading = false;
      }
    },
    updated() {
      if (this.mode === 'fraction' && !this.fractions[this.value.trim()]) {
        this.loadFraction();
      } else if (this.fieldsAndGroups) {
        this.loadFieldsAndGroups();
      }
    },
  },
};
</script>
