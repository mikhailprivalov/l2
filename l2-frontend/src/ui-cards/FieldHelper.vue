<template>
  <div>
    <template v-if="Boolean(mode)">
      <div>{{modeTitle}}</div>
      <div v-if="mode === 'formula'">
        <ul>
          <li v-for="l in formulaLinks" :key="`${l.type}-${l.id}`">
            <u>{{LINK_TITLES[l.type]}} {{l.id}}</u>:
            <span v-if="fieldsAsObject[l.id]">{{fieldsAsObject[l.id]}}</span>
            <strong v-else>значение не найдено</strong>
          </li>
        </ul>
      </div>
      <div v-else-if="mode === 'fraction'">
        <u>Фракция {{this.value}}</u>:
        <span v-if="loading">загрузка...</span>
        <span v-else-if="fractions[this.value.trim()]">{{fractions[this.value.trim()]}}</span>
        <strong v-else>фракция не найдена</strong>
      </div>
      <div v-else>
        <div class="bold" v-if="fieldsAndGroups.sign === '&'">Объединение полей или групп</div>
        <div class="bold" v-if="fieldsAndGroups.sign === '|'">Одно из полей или групп</div>
        <div class="bold" v-if="fieldsAndGroups.ids.length === 1">Одно поле или группа</div>
        <ul>
          <li v-for="fg in fieldsAndGroups.ids" :key="fg">
            <u>{{fg.endsWith('@') ? 'Группа' : 'Поле'}} {{fg.replace('@', '')}}</u>:
            <span v-if="loading">загрузка</span>
            <span v-else-if="fieldsAndGroupsCache[fg]">{{fieldsAndGroupsCache[fg]}}</span>
            <strong v-else>не найдено</strong>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script>
import _ from 'lodash';
import { debounce } from 'lodash/function';
import { LINK_FIELD, LINK_PATIENT, PrepareFormula } from '@/utils';
import laboratoryPoint from '@/api/laboratory-point';
import researchesPoint from '@/api/researches-point';

const fieldModes = {
  3: 'formula', 11: 'fraction', 13: 'field', 14: 'field', 23: 'field-and-group',
};

const modeTitles = {
  formula: 'Формульные ссылки на значения из того же направления',
  fraction: 'Ссылка на фракцию (лаборатория)',
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
      fieldsAndGroupsCache: {},
      loading: false,
    };
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
  watch: {
    value: {
      handler() {
        this.updated();
      },
    },
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

      return PrepareFormula({}, this.value, {}, false, true);
    },
    fieldsAsObject() {
      if (this.mode !== 'formula') {
        return null;
      }

      return _.flatten(
        this.groups
          .map((g) => g.fields.map((f) => ({ pk: f.pk, title: f.title, group: g.title }))),
      )
        .filter((f) => f.pk && f.pk > -1)
        .reduce(
          (a, b) => ({ ...a, [b.pk]: `${b.group || 'группа без названия'} – ${b.title || 'поле без названия'}` }),
          { age: 'возраст', sex: 'пол' },
        );
    },
    fieldsAndGroups() {
      if (this.mode === 'formula' || this.mode === 'fraction') {
        return null;
      }
      const signAND = this.value.includes('&');
      const signOR = this.value.includes('|');
      const sign = (!signAND && !signOR) ? '-' : ((signAND && '&') || '|');
      const ids = _.uniq(this.value.trim().split(sign).filter(Boolean));

      return { ids, sign };
    },
  },
};
</script>
