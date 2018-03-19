<template>
  <div class="root">
    <div>
      <div>
        <span class="sticky-span">{{research.title}}</span>
      </div>
    </div>
    <div>
      <div v-for="p in research.params"
           :class="{active: selected_param(p.pk), n1: params_cnt === 1, n2: params_cnt === 2, n3: params_cnt === 3, n4: params_cnt > 3}"
           @click="toggle_select(p.pk)"
           class="param"><span>{{p.title}}</span></div>
    </div>
    <div>
      <button class="btn btn-blue-nb">&times;</button>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'research-params-select',
    props: {
      research: {
        reqired: true
      },
      value: {
        type: Array
      }
    },
    data() {
      return {
        selected_params: []
      }
    },
    computed: {
      params_cnt() {
        return this.research.params.length
      },
    },
    mounted() {
      if (this.params_cnt === 1) {
        this.selected_params.push(this.research.params[0].pk)
      }
    },
    methods: {
      selected_param(pk) {
        console.log(pk, this.selected_params, this.selected_params.indexOf(pk), this.selected_params.indexOf(pk) !== -1)
        return this.selected_params.indexOf(pk) !== -1
      },
      toggle_select(pk) {
        if (this.selected_param(pk))
          this.selected_params = this.selected_params.filter(item => item !== pk)
        else
          this.selected_params.push(pk)
      },
    },
    watch: {
      selected_params() {
        this.$emit('input', this.selected_params)
      }
    }
  }
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
      justify-content: stretch;

      div {
        align-self: stretch;
        width: 220px;
        position: relative;
      }

      .sticky-span {
        position: sticky;
        top: 0;
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
</style>
