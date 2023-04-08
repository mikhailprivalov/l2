<template>
  <div>
    <div class="radio-button-object">
      <RadioField
        v-model="searchTypesObject"
        :variants="typesObject"
        full-width
        @modified="filteredGroupObject"
      />
    </div>
    <div
      class="row"
      style="padding-top:15px;"
    >
      <div class="col-xs-5">
        <div class="input-group treeselect-noborder-left">
          <span class="input-group-addon">Откуда</span>
          <Treeselect
            v-model="source"
            :multiple="false"
            :disable-branch-nodes="true"
            :flatten-search-results="true"
            :options="sources"
            :clearable="true"
            class="treeselect-wide"
            placeholder="Кабинет не указаны"
          />
        </div>
      </div>
      <div class="col-xs-5">
        <div class="input-group treeselect-noborder-left">
          <span class="input-group-addon">Куда</span>
          <Treeselect
            v-model="destination"
            :multiple="false"
            :disable-branch-nodes="true"
            :flatten-search-results="true"
            :options="destinations"
            placeholder="Кабинет не указаны"
            :clearable="false"
            class="treeselect-wide"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, onBeforeMount, onMounted, ref, watch,
} from 'vue';
import Component from 'vue-class-component';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import RadioField from '@/fields/RadioField.vue';

const typesObject = ref(['Принять', 'Отправить']);
const searchTypesObject = ref('');
const destination = ref(-1);
const source = ref(-1);

const destinations = ref([
  { id: -1, label: 'не выбрано' },
  { id: 1, label: 'каб1' }, { id: 2, label: 'каб2' }, { id: 3, label: 'каб3' }]);
const sources = ref([
  { id: -1, label: 'не выбрано' },
  { id: 1, label: 'каб11' }, { id: 2, label: 'каб22' }, { id: 3, label: 'каб33' }]);

function filteredGroupObject() {
  console.log(searchTypesObject);
}
</script>

<style lang="scss" module>
.radio-button-object {
  width: 70%;
  margin-left: auto;
  margin-right: auto;
  margin-top: 2%;
}

.radio-button-groups {
  width: 40%;
  margin-bottom: 3%;
}

.checkbox-color {
  background-color: #9dcaeb
}
</style>
