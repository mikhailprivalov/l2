<template>
  <div v-frag>
    <div class="top-buttons">
      <template v-if="loaded">
        <button
          v-if="!allConfirmed"
          class="btn btn-blue-nb"
          :disabled="!allSaved"
          @click="confirmAll"
        >
          Подтвердить всё
        </button>
        <div
          v-else
          class="eds-wrapper"
        >
          <EDSDirection
            :key="`eds-${direction.pk}`"
            :direction-pk="direction.pk"
            :all_confirmed="true"
          />
        </div>

        <button
          v-tippy
          class="btn btn-blue-nb btn-right"
          title="Перезагрузить данные"
          @click="reload()"
        >
          <i class="fa fa-refresh" />
        </button>
        <button
          v-tippy
          class="btn btn-blue-nb btn-right"
          :disabled="!allConfirmed"
          title="Печать результатов"
          @click="print"
        >
          <i class="fa fa-print" />
        </button>
      </template>
    </div>
    <div class="root">
      <table class="table table-bordered table-condensed table-responsive">
        <colgroup>
          <col width="26%">
          <col width="32%">
          <col width="21%">
          <col width="21%">
        </colgroup>
        <tbody>
          <tr>
            <th>№ направл.</th>
            <td>
              <a
                v-if="direction.pk"
                :href="`/directions/pdf?napr_id=[${direction.pk}]`"
                target="_blank"
                class="a-under"
              >
                {{ direction.pk }}
              </a>
            </td>
            <th>Финанс.</th>
            <td>
              {{ direction.fin_source }}
              <template v-if="fromRmis">
                внеш.орг
              </template>
            </td>
          </tr>
          <tr>
            <th>Пациент</th>
            <td :colspan="patient.diagnosis ? 2 : 3">
              {{ patient.fio }}
            </td>
            <td
              v-if="patient.diagnosis"
              v-tippy
              title="Диагноз"
            >
              {{ patient.diagnosis }}
            </td>
          </tr>
          <tr>
            <th>Пол</th>
            <td>{{ patient.sex }}</td>
            <th>Возраст</th>
            <td>{{ patient.age }}</td>
          </tr>
          <tr v-if="patient.history_num">
            <th>Карта</th>
            <td>{{ patient.card }}</td>
            <th>Истор.</th>
            <td
              v-tippy
              title="Номер истории"
            >
              {{ patient.history_num }}
            </td>
          </tr>
          <tr v-else>
            <th>Карта</th>
            <td colspan="3">
              {{ patient.card }}
            </td>
          </tr>
          <tr
            v-if="!fromRmis"
            v-tippy
            title="Лечащий врач"
          >
            <th>Леч. врач</th>
            <td colspan="3">
              {{ direction.directioner }}
            </td>
          </tr>
          <tr v-if="!fromRmis">
            <th>Отделение</th>
            <td colspan="3">
              {{ direction.otd }}
            </td>
          </tr>
          <tr v-if="fromRmis">
            <th>Организация</th>
            <td colspan="3">
              {{ direction.imported_org }}
            </td>
          </tr>
        </tbody>
      </table>
      <div
        v-if="loaded"
        class="issledovaniya-scroll-wrapper"
      >
        <div
          v-if="issledovaniya.length === 0"
          class="empty-issledovaniya"
        >
          Нет исследований для выбранной лаборатории.<br><br>
          Назначения в направлении:
          <ul>
            <li
              v-for="l in labs"
              :key="l.pk"
            >
              <a
                v-if="l.islab"
                href="#"
                @click.prevent="selectOtherLab(l.pk)"
              >{{ l.title }}</a>
              <span v-else>{{ l.title }}</span>
            </li>
          </ul>
        </div>
        <template v-else>
          <ul class="issledovaniya">
            <li
              v-for="i in issledovaniya"
              :key="i.pk"
              :class="[
                `issledovaniya-isnorm-${i.is_norm}`,
                active !== i.pk && `tb-group-${i.group}`,
                active === i.pk && `tb-group-full-${i.group} tb-group-active-${i.group} active`,
              ]"
              @click="select(i.pk)"
            >
              <div :class="`status status-${getStatusClass(i)}`">
                {{ getStatus(i) }}
              </div>
              {{ i.title }}
              <br>
              <small v-if="i.tubes.length > 0">Ёмкость: {{ i.tubes.map(t => t.pk).join(', ') }}</small>
              <div
                v-if="i.confirmed && i.allow_reset_confirm"
                class="fastlinks hiddenlinks"
              >
                <a
                  href="#"
                  @click.prevent.stop="resetConfirmation(i)"
                >сброс подтверждения</a>
              </div>
            </li>
          </ul>
          <div
            v-if="otherLabs.length > 0 && showOtherLabs"
            class="other-issledovaniya"
          >
            Другие лаборатории в направлении:
            <ul>
              <li
                v-for="l in otherLabs"
                :key="l.pk"
              >
                <a
                  href="#"
                  @click.prevent="selectOtherLab(l.pk)"
                >{{ l.title }}</a>
              </li>
            </ul>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import _ from 'lodash';

import * as actions from '@/store/action-types';

export default {
  name: 'DirectionForm',
  components: {
    EDSDirection: () => import('@/ui-cards/EDSDirection.vue'),
  },
  props: {
    laboratory: {},
  },
  data() {
    return {
      direction: {},
      patient: {},
      issledovaniya: [],
      labs: [],
      loaded: false,
      showOtherLabs: false,
      allConfirmed: false,
      allSaved: false,
      active: -1,
      q: {},
    };
  },
  computed: {
    fromRmis() {
      return this.loaded && this.direction && this.direction.imported_from_rmis;
    },
    otherLabs() {
      return this.labs.filter(l => l.islab && l.pk !== this.laboratory);
    },
  },
  mounted() {
    this.$root.$on('laboratory:results:show-direction', (data, pk) => {
      this.direction = data.direction;
      this.patient = data.patient;
      this.issledovaniya = data.issledovaniya;
      this.allConfirmed = data.allConfirmed;
      this.allSaved = data.allSaved;
      this.labs = data.labs;
      this.q = data.q;
      this.showOtherLabs = false;
      this.loaded = true;
      if (!pk) {
        this.select(-1);
      } else {
        this.select(pk);
      }
      const tubesInGroups = {};

      for (const i of data.issledovaniya) {
        if (this.active === -1) {
          this.select(i.pk);
        }
        for (const t of i.tubes) {
          tubesInGroups[t.pk] = i.group;
        }
      }

      this.$root.$emit(
        'laboratory:results:activate-pks',
        [data.direction.pk],
        _.uniq(_.flatten(data.issledovaniya.map(i => i.tubes.map(t => t.pk)))),
        tubesInGroups,
      );

      setTimeout(() => {
        if (this.otherLabs.length > 0) {
          this.showOtherLabs = true;
        }
      }, 300);
    });

    this.$root.$on('laboratory:reload-direction:with-open-first', () => this.reload());
    this.$root.$on('laboratory:reload-direction:with-open-pk', pk => this.reload(pk));
  },
  methods: {
    getStatusClass(i) {
      if (i.saved && !i.confirmed) {
        return 's';
      }

      if (i.confirmed) {
        return 'c';
      }

      if (!i.deff) {
        return 'n';
      }

      return 'o';
    },
    getStatus(i) {
      const status = this.getStatusClass(i);

      return {
        n: 'Не обработан',
        s: 'Обработан',
        c: 'Подтверждён',
        o: 'Отложен',
      }[status];
    },
    select(pk) {
      this.active = pk;
      this.$root.$emit(
        'laboratory:results:open-form',
        pk,
        this.issledovaniya.map(i => ({
          pk: i.pk,
          research_pk: i.research_pk,
          title: i.title,
        })),
        this.direction.dirData,
      );
    },
    reload(pk) {
      this.$root.$emit('laboratory:results:search', this.q.mode, String(this.q.text), pk);
    },
    print() {
      this.$root.$emit('print:results', [this.direction.pk]);
    },
    async confirmAll() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('laboratory/confirm-list', this.direction, 'pk');
      if (!ok) {
        this.$root.$emit('msg', 'error', message);
      } else {
        this.$root.$emit('msg', 'ok', 'Подтверждено');
      }
      this.$root.$emit('laboratory:reload-direction:with-open-first');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    selectOtherLab(pk) {
      this.$root.$emit('external-change-laboratory', pk, () => {
        this.reload();
      });
    },
    async resetConfirmation(iss) {
      try {
        await this.$dialog.confirm(`Подтвердите сброс: ${iss.title}`);
      } catch (e) {
        // pass
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('laboratory/reset-confirm', iss, 'pk');
      if (!ok) {
        this.$root.$emit('msg', 'error', message);
      } else {
        this.$root.$emit('msg', 'ok', 'Подтверждение сброшено');
      }
      this.$root.$emit('laboratory:reload-form');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.root {
  position: absolute;
  top: 34px !important;
  right: 0;
  left: 0;
  bottom: 0;

  display: flex;
  flex-direction: column;
  justify-content: stretch;
  align-items: stretch;
}

table {
  margin-bottom: 0;
  min-height: 145px;

  td,
  th {
    padding: 3px !important;
    font-size: 12px;
  }
}

.issledovaniya {
  margin: 0 3px;
  padding: 0;

  &-scroll-wrapper {
    overflow-x: visible;
    overflow-y: auto;
    flex: 1 1;
  }

  li {
    list-style: none;
    cursor: pointer;
    margin: 3px 0;
    width: calc(100% - 3px);
    background-color: #f8fcfd;
    border-left-width: 3px;
    border-radius: 3px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    transition: left 0.15s linear;
    position: relative;
    left: 3px;
    padding: 6px 6px 6px 9px;

    & small {
      color: rgba(0, 0, 0, 0.5);
      font-size: 8pt;
    }

    .hiddenlinks {
      opacity: 0;
      transition: 0.1s linear;
    }

    .fastlinks {
      position: absolute;
      right: 0;
      bottom: 0;
      margin: 0;

      a {
        font-size: 12px;
      }
    }

    &:hover {
      background-color: #eef1f5;

      .hiddenlinks {
        opacity: 1;
      }

      small {
        color: #000;
      }
    }

    &.active {
      background-color: #fff !important;
      color: #000 !important;
    }

    &:not(.active) {
      border: 1px solid #ecf0f1;
    }

    &:not(.issledovaniya-isnorm-maybe):not(.issledovaniya-isnorm-not_normal) {
      padding-right: 8px;
    }

    &.issledovaniya-isnorm-maybe,
    &.issledovaniya-isnorm-not_normal {
      border-right-width: 3px !important;
    }

    &.issledovaniya-isnorm-not_normal {
      border-right-color: #e68364 !important;
    }

    &.issledovaniya-isnorm-maybe {
      border-right-color: #f5d76e !important;
    }

    .status {
      float: right;
      display: inline-block;
      vertical-align: top;
      font-size: 11px;
      text-align: right;
      padding-bottom: 3px;
      position: absolute;
      right: 0;
      top: -3px;
    }

    .status-n {
      color: #cf3a24;
      font-weight: bold;
    }

    .status-s {
      color: #4b77be;
    }

    .status-c {
      color: #049372;
    }

    .status-o {
      color: #f7ca18;
    }
  }
}

.empty-issledovaniya {
  padding: 20px;
  color: #7a7a7a;
  text-align: left;
}

.other-issledovaniya {
  padding: 20px;
  color: #7a7a7a;
  text-align: left;
}

.eds-wrapper {
  display: flex;
  flex-direction: row;
  max-width: 175px;
  position: absolute;
  top: 0;
  left: 0;
}
</style>
