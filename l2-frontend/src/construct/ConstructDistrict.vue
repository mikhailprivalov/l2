<template>
  <div
    ref="root"
    class="district-root"
  >
    <div class="district-sidebar">
      <div
        v-for="row in data"
        :key="row.pk"
        class="sidebar-btn-wrapper"
      >
        <button
          class="btn btn-blue-nb sidebar-btn"
          @click="editDistrict(row)"
        >
          {{ row.title }}
        </button>
      </div>
      <div
        class="
        side-bottom"
      >
        <div
          class="input-group"
          style="width: 280px"
        >
          <input
            type="text"
            class="form-control"
            autofocus
            placeholder="Название участка"
          >
          <span class="input-group-btn">
            <button
              class="btn last btn-blue-nb nbr"
              type="button"
              style="margin-right: -1px"
            >Добавить</button>
          </span>
        </div>
      </div>
    </div>
    <div class="district-content">
      <div>
        <h5 style="text-align: center">
          {{ currentDistrictTitle }}
        </h5>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';

export default {
  name: 'ConstructDistrict',
  data() {
    return {
      data: [],
      district: {},
      currentDistrictTitle: '',
    };
  },
  mounted() {
    this.load_district();
  },
  methods: {
    async load_district() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { result } = await this.$api('districts/districts-load');
      this.data = result;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async editDistrict(row) {
      await this.$store.dispatch(actions.INC_LOADING);
      this.currentDistrictTitle = row.title;
      const { result } = await this.$api('districts/district-edit', { pk: row.pk });
      this.district = result;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.district-root {
  position: absolute;
  top: 36px;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: stretch;
  flex-direction: row;
  flex-wrap: nowrap;
  align-content: stretch;
  overflow-x: hidden;

  & > div {
    align-self: stretch;
  }
}

.district-sidebar {
  width: 280px;
  border-right: 1px solid #b1b1b1;
  display: flex;
  flex-direction: column;
}

.district-content {
  display: flex;
  flex-direction: column;
  width: calc(100% - 280px);
}

.side-bottom {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    border-radius: 0;
    display: flex;
    flex-direction: row;

    .btn {
      height: 34px;
      border-radius: 0;
    }
  }

.sidebar-btn {
  border-radius: 0;

  &:not(.text-center) {
    text-align: left;
  }

  border-top: none !important;
  border-right: none !important;
  border-left: none !important;
  padding: 0 12px;
  height: 28px;

  &:not(:hover):not(.colorBad),
  &.active-btn:hover:not(.colorBad) {
    cursor: default;
    background-color: rgba(#000, 0.02) !important;
    color: #000;
    border-bottom: 1px solid #b1b1b1 !important;
  }
}

.sidebar-btn-wrapper {
  display: flex;
  flex-direction: row;

  .sidebar-btn:first-child {
    flex: 1 1 auto;
  }
}

</style>
