<template>
  <div class="group">
    <div class="group-title">
      Микроорганизмы
      <div
        v-if="!confirmed"
        class="input-select flex-select"
      >
        <v-select
          v-model="selectedGroup"
          :clearable="false"
          label="title"
          :options="bacteriesGroups"
          :searchable="true"
          class="inner-select"
          placeholder="Выберите группу"
          append-to-body
          :calculate-position="withPopper"
        />
        <v-select
          v-model="selectedBactery"
          :clearable="false"
          label="title"
          :options="bacteries"
          :searchable="true"
          class="inner-select"
          placeholder="Выберите микроорганизм"
          append-to-body
          :calculate-position="withPopper"
        />
        <button
          class="btn btn-blue-nb"
          @click="addBactery"
        >
          Добавить
        </button>
      </div>
    </div>
    <div class="fields">
      <div style="height: 100%;width: 100%;position: relative;min-height: 100px;">
        <div
          v-for="bactery in bacteriesResult"
          :key="bactery.bacteryPk"
          class="bactery"
        >
          <div class="bactery-title">
            <span
              v-tippy
              title="Удалить"
              class="bactery-delete"
              @click="deleteBac(bactery.bacteryPk)"
            >
              <i class="fa fa-times" />
            </span>
            <span class="bactery-title-inner"> {{ bactery.bacteryGroupTitle }} {{ bactery.bacteryTitle }} </span>
          </div>
          <div class="bactery-body">
            <div
              v-if="!confirmed"
              class="bactery-selects"
            >
              <div class="row">
                <div class="col-xs-6 two">
                  <v-select
                    v-model="bactery.selectedSet"
                    :clearable="false"
                    label="title"
                    :options="antibiotics.sets"
                    :searchable="true"
                    class="inner-select"
                    placeholder="Выберите набор"
                    append-to-body
                    :calculate-position="withPopper"
                  />
                  <button
                    class="btn btn-blue-nb"
                    @click="loadSet(bactery)"
                  >
                    Загрузить набор
                  </button>
                </div>
                <div class="col-xs-6 three">
                  <v-select
                    v-model="bactery.selectedAntibiotic"
                    :clearable="false"
                    label="title"
                    :options="antibiotics.groupsObj[bactery.selectedGroup.pk]"
                    :searchable="true"
                    class="inner-select"
                    placeholder="Выберите антибиотик"
                    append-to-body
                    :calculate-position="withPopper"
                  />
                  <button
                    class="btn btn-blue-nb"
                    @click="loadAntibiotic(bactery)"
                  >
                    Добавить
                  </button>
                </div>
              </div>
            </div>
            <div class="table-row">
              <div class="left">
                <table
                  class="table table-bordered table-condensed"
                  style="max-width: 665px;margin-top: 15px"
                >
                  <colgroup>
                    <col
                      v-if="!confirmed"
                      style="width: 34px"
                    >
                    <col>
                    <col style="width: 90px">
                    <col style="width: 74px">
                    <col style="width: 148px">
                    <col style="width: 100px">
                  </colgroup>
                  <thead>
                    <tr>
                      <th
                        v-if="!confirmed"
                        colspan="2"
                      >
                        Название
                      </th>
                      <th v-else>
                        Название
                      </th>
                      <th />
                      <th>Чувствительность</th>
                      <th>Диаметр</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="a in bactery.antibiotics"
                      :key="a.pk"
                    >
                      <td
                        v-if="!confirmed"
                        class="cl-td"
                      >
                        <button
                          v-tippy
                          title="Удалить"
                          class="btn last btn-blue-nb nbr"
                          type="button"
                          tabindex="-1"
                          @click="deleteAnti(bactery, a.pk)"
                        >
                          <i class="fa fa-times" />
                        </button>
                      </td>
                      <td>
                        {{ antibiotics.antibiotics[a.pk] }}
                      </td>
                      <td class="cl-td">
                        <input
                          v-model="a.amount"
                          class="form-control"
                          maxlength="30"
                          :readonly="confirmed"
                          placeholder="Дозировка"
                        >
                      </td>
                      <td class="cl-td">
                        <RadioField
                          v-model="a.sri"
                          :variants="sri"
                          redesigned
                          :disabled="confirmed"
                        />
                      </td>
                      <td class="cl-td">
                        <input
                          v-model="a.dia"
                          class="form-control"
                          maxlength="64"
                          :readonly="confirmed"
                        >
                      </td>
                    </tr>
                    <tr v-if="bactery.antibiotics.length === 0">
                      <td
                        v-if="!confirmed"
                        colspan="5"
                        class="text-center"
                      >
                        антибиотики не выбраны
                      </td>
                      <td
                        v-else
                        colspan="4"
                        class="text-center"
                      >
                        антибиотики не выбраны
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div
                  v-if="bactery.phenotype && bactery.phenotype.length > 0"
                  class="phen"
                >
                  <ul>
                    <li><strong>Фенотип:</strong></li>
                    <li
                      v-for="p in bactery.phenotype"
                      :key="p.pk"
                    >
                      {{ p.title }}
                    </li>
                  </ul>
                </div>
              </div>
              <div class="right">
                <div class="right-inner">
                  <div
                    class="input-group"
                    style="max-width: 330px"
                  >
                    <span class="input-group-addon">КОЕ</span>
                    <KOEField
                      v-model="bactery.koe"
                      :disabled="confirmed"
                    />
                  </div>

                  <div
                    class="fields"
                    style="padding: 5px 0"
                  >
                    <div
                      :class="{ disabled: confirmed }"
                      class="field field-vertical"
                      v-on="{
                        mouseenter: enter_field(cultureCommentsTemplates.length > 0),
                        mouseleave: leave_field(cultureCommentsTemplates.length > 0),
                      }"
                    >
                      <div class="field-value">
                        <textarea
                          v-model="bactery.comments"
                          placeholder="Комментарии"
                          rows="6"
                          class="form-control"
                          :readonly="confirmed"
                        />
                      </div>

                      <FastTemplates
                        :update_value="updateValue(bactery, 'comments')"
                        :value="bactery.comments || ''"
                        :values="cultureCommentsTemplates"
                        :confirmed="confirmed"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div
          v-if="bacteriesResult.length === 0"
          class="bactery-msg"
        >
          Микроорганизмы не выбраны
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import vSelect from 'vue-select';
import 'vue-select/dist/vue-select.css';
import { createPopper } from '@popperjs/core';
import bacteriaPoint from '@/api/bacteria-point';
import * as actions from '@/store/action-types';
import RadioField from '@/fields/RadioField.vue';
import KOEField from '@/fields/KOEField.vue';
import { enterField, leaveField } from './utils';
import FastTemplates from './FastTemplates.vue';

const getDefaultElement = () => ({
  pk: -1,
  title: '',
});

export default {
  name: 'BacMicroForm',
  components: {
    KOEField,
    FastTemplates,
    RadioField,
    vSelect,
  },
  props: {
    cultureCommentsTemplates: {
      type: Array,
      default: () => [],
      required: false,
    },
    value: {
      type: Array,
      default: () => [],
      required: false,
    },
    confirmed: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      sri: ['S', 'R', 'I'],
      val: [...this.value],
      bacteriesGroups: [],
      bacteries: [],
      selectedGroup: getDefaultElement(),
      selectedBactery: getDefaultElement(),
      bacteriesResult: this.value,
      antibiotics: {
        groups: [],
        groupsObj: {},
        antibiotics: {},
        sets: [],
      },
      prev_scroll: 0,
      prev_scrollHeightTop: 0,
    };
  },
  watch: {
    bacteriesResult: {
      deep: true,
      handler() {
        this.$emit('input', this.bacteriesResult);
      },
    },
    selectedGroup: {
      deep: true,
      handler() {
        this.load_bac_by_group();
      },
    },
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    this.bacteriesGroups = (await bacteriaPoint.getBacGroups()).groups;
    this.antibiotics = await bacteriaPoint.getAntibioticGroups();
    this.selectedGroup = this.bacteriesGroups[0] || getDefaultElement();
    await this.$store.dispatch(actions.DEC_LOADING);

    for (const b of this.bacteriesResult) {
      // eslint-disable-next-line prefer-destructuring
      b.selectedGroup = this.antibiotics.groups[0];
      // eslint-disable-next-line prefer-destructuring
      b.selectedAntibiotic = this.antibiotics.groupsObj[this.antibiotics.groups[0].pk][0];
      // eslint-disable-next-line prefer-destructuring
      b.selectedSet = this.antibiotics.sets[0];
    }
  },
  methods: {
    withPopper(dropdownList, component, { width }) {
      // eslint-disable-next-line no-param-reassign
      dropdownList.style.width = width;
      const popper = createPopper(component.$refs.toggle, dropdownList, {
        placement: 'bottom',
      });

      return () => popper.destroy();
    },
    async load_bac_by_group() {
      await this.$store.dispatch(actions.INC_LOADING);
      this.bacteries = (await bacteriaPoint.getBacByGroup({ groupId: this.selectedGroup.pk })).list;
      this.selectedBactery = this.bacteries[0] || getDefaultElement();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    addBactery() {
      for (const bactery of this.bacteriesResult) {
        if (bactery.bacteryPk === this.selectedBactery.pk) {
          return;
        }
      }
      this.bacteriesResult.push({
        resultPk: -1,
        bacteryPk: this.selectedBactery.pk,
        bacteryTitle: this.selectedBactery.title,
        bacteryGroupTitle: this.selectedGroup.title,
        selectedGroup: this.antibiotics.groups[0],
        selectedAntibiotic: this.antibiotics.groupsObj[this.antibiotics.groups[0].pk][0],
        selectedSet: this.antibiotics.sets[0],
        antibiotics: [],
        koe: '',
        comments: '',
      });
    },
    async deleteBac(pk) {
      try {
        await this.$dialog.confirm('Подтвердите удаление');
      } catch (_) {
        return;
      }

      this.bacteriesResult = this.bacteriesResult.filter(br => br.bacteryPk !== pk);
    },
    deleteAnti(bactery, pk) {
      // eslint-disable-next-line no-param-reassign
      bactery.antibiotics = bactery.antibiotics.filter(a => a.pk !== pk);
    },
    loadSet(bactery) {
      for (const id of bactery.selectedSet.ids) {
        this.addAntibiotic(bactery, id);
      }
    },
    loadAntibiotic(bactery) {
      this.addAntibiotic(bactery, bactery.selectedAntibiotic.pk);
    },
    addAntibiotic(bactery, pk) {
      for (const a of bactery.antibiotics) {
        if (a.pk === pk) {
          return;
        }
      }

      bactery.antibiotics.push({
        pk,
        resultPk: -1,
        sri: 'S',
        dia: '',
        amount: '',
      });
    },
    updateSelectedAntibiotic(bactery) {
      // eslint-disable-next-line no-param-reassign,prefer-destructuring
      bactery.selectedAntibiotic = this.antibiotics.groupsObj[bactery.selectedGroup.pk][0];
    },
    updateValue(field, prop) {
      return newValue => {
        // eslint-disable-next-line no-param-reassign
        field[prop] = newValue;
      };
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
.flex-select {
  font-weight: normal;
  padding-left: 5px;
  margin-top: -5px;
  margin-bottom: -5px;
  width: 539px;
  display: inline-flex;
  flex-wrap: nowrap;
  justify-content: stretch;
  align-content: stretch;
  align-items: stretch;

  .btn {
    border-radius: 0 !important;
    height: 31px !important;
  }

  .inner-select {
    align-self: stretch;
    &:first-child {
      flex: 0 0 210px;
      max-width: 210px;
    }
    &:last-child {
      flex: 1;
    }
    margin-right: 5px;
    height: 30px !important;

    ::v-deep .vs__dropdown-toggle {
      border-radius: 0 !important;
    }
  }
}

.table-row {
  display: flex;
  flex-wrap: nowrap;
  justify-content: stretch;
  align-content: stretch;
  align-items: stretch;

  .left,
  .right {
    align-self: stretch;
  }

  .left {
    flex: 1 60%;
    max-width: 665px;
  }

  .right {
    flex: 0 40%;
    padding-left: 10px;
    padding-top: 15px;
    padding-bottom: 20px;

    &-inner {
      width: 100%;

      textarea {
        margin-top: 5px;
      }
    }
  }
}

.inner-select,
.input-select .btn {
  display: inline-block;
  vertical-align: middle;
}

.inner-select,
.input-select .btn {
  height: 32px;
}

.bactery-selects {
  position: sticky;
  top: 80px;
  background: #fff;
  padding-bottom: 5px;
  padding-top: 5px;
  border-bottom: solid 1px lightgray;
  z-index: 1;

  .row {
    max-width: 700px;
  }

  .two,
  .three {
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    align-content: stretch;
    align-items: stretch;
  }

  .two {
    padding-right: 5px;
    border-right: 1px solid lightgray;
  }

  .three {
    padding-left: 5px;
  }

  .inner-select,
  .btn {
    align-self: stretch;
    height: 32px;
    margin: 0 5px;
    max-width: 100%;
  }

  .inner-select {
    flex: 1;
  }

  .btn {
    flex: 0;
  }
}

.inner-select {
  background: #fff !important;
}

.bactery {
  margin: 10px 0;
  border: 1px solid #048493;
  border-radius: 5px;
  overflow: visible;

  &-title {
    z-index: 2;
    position: sticky;
    top: 60px;
    color: #fff;
    background: #048493;
    line-height: 20px;
    border-radius: 4px 4px 0 0;
    overflow: hidden;

    span {
      display: inline-block;
    }
  }

  &-delete {
    padding: 0 4px;
    cursor: pointer;

    &:hover {
      background: #0c7e8b;
    }
  }
}

.bactery-body {
  padding: 5px;

  hr {
    margin: 5px 0;
  }
}

.bactery-msg {
  padding: 20px;
  text-align: center;
}
</style>
