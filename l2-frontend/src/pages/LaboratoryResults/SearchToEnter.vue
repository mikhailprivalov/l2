<template>
  <div>
    <div class="filters">
      <form autocomplete="off" @submit.prevent>
        <input autocomplete="false" name="hidden" type="text" style="display: none;"/>
        <div class="input-group">
          <span class="input-group-btn" v-for="(title, key) in modes" :key="key">
            <a href="#" class="top-inner-select"
               :class="key === mode && 'active'" @click.prevent="mode = key">
              <span>{{ title }}</span>
            </a>
          </span>
          <input type="text" maxlength="13" class="form-control" autofocus
                 ref="q" v-model="q"
                 :placeholder="mode === 'direction' ? 'номер направления' : 'номер ёмкости'"/>
          <span class="input-group-btn">
            <button style="margin-right: -1px;" type="button"
                    @click="search"
                    class="btn btn-blue-nb">Поиск</button>
          </span>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import {SEARCH_MODES, SEARCH_MODES_TITLES} from "@/pages/LaboratoryResults/constants";
import * as action_types from "@/store/action-types";
import api from "@/api";

export default {
  name: "SearchToEnter",
  props: {
    laboratory: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      mode: SEARCH_MODES.DIRECTION,
      modes: SEARCH_MODES_TITLES,
      q: '',
    };
  },
  mounted() {
    this.$root.$on('laboratory:results:search', (mode, pk) => {
      this.mode = mode;
      this.q = String(pk);
      this.search();
    })
  },
  watch: {
    mode() {
      $(this.$refs.q).focus();
    },
    q() {
      this.q = this.q.replace(/\D/g, '');
    },
  },
  methods: {
    async search() {
      await this.$store.dispatch(action_types.INC_LOADING);
      const {ok, data, msg} = await api('laboratory/search', this, ['q', 'mode', 'laboratory']);
      if (ok) {
        this.q = '';
        this.$root.$emit('laboratory:results:show-direction', data);
      } else {
        errmessage(msg || 'Не найдено');
      }
      await this.$store.dispatch(action_types.DEC_LOADING);
    },
  },
}
</script>

<style scoped lang="scss">
.filters {
  background-color: #edeeef;

  form {
    .btn, .form-control, .top-inner-select {
      border-radius: 0 !important;
      padding: 6px 4px !important;
      font-size: 12px;
      height: 34px;
    }
  }
}

.top-inner-select {
  align-self: stretch;
  display: flex;
  align-items: center;
  text-decoration: none;
  cursor: pointer;
  flex: 1;
  margin: 0;
  font-size: 12px;
  min-width: 0;
  background-color: #AAB2BD;
  color: #fff;

  &:hover {
    background-color: #434a54;
  }

  &.active {
    background: #8d98a7 !important;
    color: #fff;
  }

  &.disabled {
    color: #fff;
    cursor: not-allowed;
    opacity: .8;
    background-color: rgba(255, 255, 255, .7) !important;
  }

  span {
    display: block;
    text-overflow: ellipsis;
    overflow: hidden;
    word-break: keep-all;
    max-height: 2.2em;
    line-height: 1.1em;
    margin: 0 auto;
  }
}
</style>
