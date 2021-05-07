<template>
  <div class="root">
    <div>
      <div class="sticky-d">
        {{research.title}}
      </div>
      <div class="l-actions" v-if="params.length > 1">
        <a href="#" @click.prevent="select_all">выбрать всё</a> <a href="#" @click.prevent="deselect_all">снять всё</a>
      </div>
    </div>
    <div>
      <div v-for="p in params"
           :key="p.pk"
           :class="{
             active: selected_param(p.pk),
             n1: params_cnt === 1,
             n2: params_cnt === 2,
             n3: params_cnt === 3,
             n4: params_cnt > 3
           }"
           @click="toggle_select(p.pk)"
           class="param" :title="p.title"><span>{{p.title}}</span></div>
    </div>
    <div>
      <longpress class="btn btn-blue-nb btn-sticky" :on-confirm="deselect" :confirm-time="0" :duration="400"
                 pressing-text="×"
                 action-text="×">
        <span class="inner-sticky">×</span>
      </longpress>
    </div>
  </div>
</template>

<script>
import Longpress from 'vue-longpress';

export default {
  name: 'research-params-select',
  components: {
    Longpress,
  },
  props: {
    research: {
      required: true,
    },
    value: {
      type: Array,
    },
  },
  data() {
    return {
      selected_params: [],
      inited: false,
    };
  },
  computed: {
    params_cnt() {
      return this.research.params.length;
    },
    params() {
      return this.research.params;
    },
  },
  mounted() {
    if (this.value.length === 0) {
      if (this.params_cnt === 1) {
        this.selected_params.push({ pk: this.research.params[0].pk, is_paraclinic: this.research.is_paraclinic });
      }
    } else {
      this.selected_params = JSON.parse(JSON.stringify(this.value));
    }
    this.inited = true;
  },
  methods: {
    deselect() {
      this.$root.$emit('researches-picker:deselect', this.research.pk);
    },
    deselect_all() {
      this.selected_params = [];
    },
    select_all() {
      for (const p of this.params) {
        if (!this.selected_param(p.pk)) {
          this.toggle_select(p.pk);
        }
      }
    },
    selected_param(pk) {
      return this.selected_params.filter((item) => item.pk === pk).length > 0;
    },
    toggle_select(pk) {
      if (this.selected_param(pk)) {
        this.selected_params = this.selected_params.filter((item) => item.pk !== pk);
      } else {
        this.selected_params.push({ pk, is_paraclinic: this.research.is_paraclinic });
      }
    },
  },
  watch: {
    selected_params() {
      if (this.inited) this.$emit('input', JSON.parse(JSON.stringify(this.selected_params)));
    },
    research() {
      if (this.selected_params.length === 0 && this.research.selected_params.length > 0) {
        this.selected_params = JSON.parse(JSON.stringify(this.research.selected_params));
      }
    },
  },
};
</script>

<style scoped lang="scss">
  .root {
    margin: 5px;
    display: flex;
    flex-direction: row;
    justify-content: stretch;
    border: 1px solid #ddd;
    width: 100%;
    align-self: flex-start;

    & > div {
      padding: 3px;
    }

    & > :nth-child(1) {
      width: 220px;
      border-right: 1px solid #ddd;
      display: flex;
      justify-content: space-between;
      flex-direction: column;
      position: relative;

      div {
        align-self: stretch;
        width: 220px;
        position: relative;
      }

      .sticky-d {
        position: sticky;
        top: 0;
        background: #fff;
        width: 100%;
        z-index: 1;
      }
    }

    & > :nth-child(2) {
      width: 100%;
      display: flex;
      align-content: flex-start;
      flex-wrap: wrap;
      justify-content: stretch;
      align-items: stretch;

      .param {
        flex: 0 1 auto;
        height: 34px;
        border: 1px solid #6C7A89 !important;
        align-self: stretch;
        display: flex;
        align-items: center;
        padding: 1px 2px 1px;
        color: #000;
        background-color: #fff;
        text-decoration: none;
        transition: .15s linear all;
        cursor: pointer;
        margin: 0;
        font-size: 12px;
        min-width: 0;

        span {
          display: block;
          text-overflow: ellipsis;
          overflow: hidden;
          word-break: keep-all;
          max-height: 2.2em;
          line-height: 1.1em;
        }

        &.active {
          background: #049372 !important;
          color: #fff;
        }

        &:hover {
          box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.8) !important;
        }
        &.n4 {
          width: 25%;
        }
        &.n3 {
          width: 33.33333%;
        }
        &.n2 {
          width: 50%;
        }
        &.n1 {
          width: 100%;
        }
      }
    }

    & > :nth-child(3) {
      width: 50px;
      display: flex;
      justify-content: stretch;
      padding: 0;
      button {
        align-self: stretch;
        border-radius: 0;
      }
    }
  }

  .btn-sticky {
    position: relative;
    border-radius: 0;
  }

  .inner-sticky {
    position: sticky;
    top: 5px;
  }
  .l-actions {
    padding-right: 12px;
    padding-left: 5px;
    display: flex;
    justify-content: space-between;
    flex-direction: row;
    flex-wrap: nowrap;

    a {
      color: #000;
      text-decoration: dotted underline;
    }

    a:hover {
      text-decoration: none;
    }
  }
</style>
