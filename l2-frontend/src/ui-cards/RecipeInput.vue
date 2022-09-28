<template>
  <div style="height: 100%;width: 100%;position: relative;min-height: 100px;">
    <table
      class="table table-responsive table-bordered table-condensed"
      style="table-layout: fixed;margin-bottom: 0;background-color: #fff"
    >
      <colgroup>
        <col width="280">
        <col>
        <col width="290">
        <col
          v-if="!confirmed"
          width="38"
        >
      </colgroup>
      <thead>
        <tr>
          <th>Наименование ЛП</th>
          <th>Форма выпуска, дозировка, количество</th>
          <th>Способ применения</th>
          <th v-if="!confirmed" />
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="v in fv"
          :key="v.pk"
        >
          <td>{{ v.prescription }}</td>
          <td class="cl-td prec">
            <TypeAhead
              v-if="!confirmed"
              v-model="v.taking"
              :delay-time="300"
              :get-response="resp => [...resp.data.data]"
              :highlighting="(item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`)"
              :limit="10"
              :min-chars="1"
              :render="items => items.map(i => `${i.method_of_taking}`)"
              :select-first="true"
              :src="`/api/methods-of-taking?keyword=:keyword&prescription=${v.prescription}`"
              maxlength="128"
            />
            <input
              v-else
              v-model="v.taking"
              class="form-control"
              readonly
            >
          </td>
          <td class="cl-td">
            <input
              v-model="v.comment"
              :readonly="confirmed"
              class="form-control"
              maxlength="128"
            >
          </td>
          <td
            v-if="!confirmed"
            class="cl-td"
          >
            <button
              v-tippy="{ placement: 'bottom', arrow: true }"
              :title="`Убрать назначение`"
              class="btn last btn-blue-nb nbr"
              type="button"
              @click.prevent="remove(v.pk)"
            >
              <i class="fa fa-times-circle" />
            </button>
          </td>
        </tr>
        <tr v-if="fv.length === 0">
          <td
            class="text-center"
            :colspan="confirmed ? 3 : 4"
          >
            нет назначений
          </td>
        </tr>
      </tbody>
    </table>
    <hr v-if="!confirmed">
    <div
      v-if="!confirmed"
      class="row"
    >
      <div class="col-xs-3">
        <div
          class="input-group"
          style="z-index: 0"
        >
          <input
            v-model="search"
            class="form-control"
            placeholder="Поиск назначения"
          >
          <span class="input-group-btn">
            <button
              class="btn btn-blue-nb"
              type="button"
              @click="search = ''"
            ><i class="fa fa-times" /></button>
          </span>
        </div>
        <div v-if="variants.length > 0">
          <small>выберите назначение из списка справа</small>
        </div>
      </div>
      <div
        class="col-xs-9"
        style="padding-left: 0"
      >
        <div
          v-for="v in variants"
          :key="v.pk"
          class="variant"
          @click="add(v.value)"
        >
          <strong>{{ v.highlighted }}</strong>{{ v.noHighlighted }}
        </div>
        <div
          v-if="search === ''"
          class="variant-msg"
        >
          выполните поиск для добавления назначений
        </div>
        <div
          v-else-if="variants.length === 0"
          class="variant-msg"
        >
          не найдено
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import TypeAhead from 'vue2-typeahead';

import * as actions from '@/store/action-types';

export default {
  name: 'RecipeInput',
  components: { TypeAhead },
  props: {
    value: {
      type: Array,
    },
    confirmed: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      search: '',
      variants: [],
      toRemove: [],
    };
  },
  computed: {
    fv() {
      return this.value.filter(v => !this.toRemove.includes(v.pk) && !v.remove);
    },
  },
  watch: {
    async search() {
      if (this.search.trim() === '') {
        this.variants = [];
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { data } = await fetch(`/api/key-value?key=mnn&value=${this.search}`).then(r => r.json());
      this.variants = [];
      const lowerSearch = this.search.trim().toLowerCase();
      const l = lowerSearch.length;
      for (const v of data) {
        const i = v.value.toLowerCase().indexOf(lowerSearch);
        const to = i + l;

        const highlighted = v.value.substring(i, to);
        const noHighlighted = v.value.substring(to);
        this.variants.push({
          value: v.value,
          highlighted,
          noHighlighted,
        });
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
  methods: {
    add(value) {
      // eslint-disable-next-line vue/no-mutating-props
      this.value.push({
        pk: Math.random() + Math.random(),
        prescription: value,
        taking: '',
        comment: '',
        isNew: true,
      });
    },
    async remove(pk) {
      for (let i = 0; i < this.value.length; i++) {
        if (this.value[i].pk === pk) {
          try {
            await this.$dialog.confirm(`Подтвердите удаление назначения «${this.value[i].prescription}»`);
          } catch (_) {
            return;
          }
          // eslint-disable-next-line vue/no-mutating-props
          this.value[i].remove = true;
          this.toRemove.push(pk);
          break;
        }
      }
    },
  },
};
</script>

<style scoped lang="scss">
.variant {
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

  &:hover {
    color: #fff;
    background-color: #049372;
    box-shadow: 0 14px 28px rgba(#049372, 0.35), 0 10px 10px rgba(#049372, 0.32);
    position: relative;
    z-index: 1;
    transform: scale(1.008) translateX(-2px);
  }
}

.variant,
.variant-msg {
  color: #000;
  background: rgba(0, 0, 0, 0.05);
  padding: 7px 5px;
  margin: 4px 0 2px 4px;
  border-radius: 5px;

  &:first-child {
    margin-top: 0;
  }
}

.prec {
  margin-right: -1px;
  z-index: 0;
}

.prec ::v-deep .input-group {
  border-radius: 0;
  width: 100%;
  z-index: 0;
}

.prec ::v-deep input {
  border-radius: 0 !important;
}

.prec ::v-deep ul {
  position: relative;
  font-size: 13px;
  z-index: 1000;
}

.prec ::v-deep ul li {
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 2px 0.25rem;
  margin: 0 0.2rem;
  a {
    padding: 2px 10px;
  }
}
</style>
