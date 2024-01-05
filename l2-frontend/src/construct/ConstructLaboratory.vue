<template>
  <div
    class="construct-root"
  >
    <input>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import SelectPickerB from '@/fields/SelectPickerM.vue';

const one = ref('');
</script>

<style scoped lang="scss">
.construct-root {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;

  display: flex;
  align-items: stretch;
  flex-direction: row;
  flex-wrap: nowrap;
  align-content: stretch;

  & > div {
    align-self: stretch;
  }
}

.construct-sidebar {
  width: 350px;
  border-right: 1px solid #b1b1b1;
  display: flex;
  flex-direction: column;

  .form-control {
    border-radius: 0;
    border-top: none;
    border-left: none;
    border-right: none;
  }
}

.construct-content {
  width: 100%;
  position: relative;
}

.sidebar-select ::v-deep .btn {
  border-radius: 0;
  border-top: none;
  border-left: none;
  border-right: none;
  border-top: 1px solid #fff;
}

.sidebar-select,
.sidebar-filter,
.sidebar-footer {
  flex: 0 0 34px;
}

.sidebar-content {
  height: 100%;
  overflow-y: auto;
  background-color: hsla(30, 3%, 97%, 1);
}

.sidebar-content:not(.fcenter) {
  padding-bottom: 10px;
}

.sidebar-footer {
  border-radius: 0;
  margin: 0;
}

.fcenter {
  display: flex;
  align-items: center;
  justify-content: center;
}

.research {
  background-color: #fff;
  padding: 5px;
  margin: 10px;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;

  &.rhide {
    background-image: linear-gradient(#6c7a89, #56616c);
    color: #fff;
  }

  &:hover {
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 1;
    transform: scale(1.008);
  }
}

.research:not(:first-child) {
  margin-top: 0;
}

.research:last-child {
  margin-bottom: 0;
}
</style>
