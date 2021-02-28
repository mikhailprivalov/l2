<template>
  <div>
    <div class="filters">
      <form autocomplete="off" @submit.prevent>
        <input autocomplete="false" name="hidden" type="text" style="display: none;"/>
        <div class="input-group">
          <span class="input-group-btn" v-for="m in modes" :key="m.key">
            <a href="#" class="top-inner-select"
               :class="m.key === mode && 'active'" @click.prevent="mode = m.key">
              <span>{{ m.title }}</span>
            </a>
          </span>
          <input type="text" maxlength="13" class="form-control" autofocus
                 ref="q"
                 :placeholder="mode === 'direction' ? 'номер направления' : 'номер ёмкости'"/>
          <span class="input-group-btn">
            <button style="margin-right: -1px;" type="button" class="btn btn-blue-nb">Поиск</button>
          </span>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
const SEARCH_MODES = [
  {
    key: 'direction',
    title: 'Направление',
  },
  {
    key: 'tube',
    title: 'Ёмкость',
  },
];

export default {
  name: "SearchToEnter",
  data() {
    return {
      mode: SEARCH_MODES[0].key,
      modes: SEARCH_MODES,
    };
  },
  watch: {
    mode() {
      $(this.$refs.q).focus();
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
    background: #7f898f !important;
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
