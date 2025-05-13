<template>
  <PageInnerLayout>
    <TwoSidedLayout :left-width-px="300">
      <template #left>
        <TopBottomLayout
          :top-height-px="36"
          no-border
        >
          <template #top>
            <DateFieldNav
              :def="date"
              :val.sync="date"
              w="100%"
            />
          </template>
          <template #bottom>
            <TopBottomLayout split-half>
              <template #top>
                <div class="requests-list">
                  <div class="requests-list__header">
                    Ожидающие
                  </div>
                  <div class="requests-list__items">
                    <RequestCard
                      v-for="request in requestsWait"
                      :key="request.id"
                      :request="request"
                    />
                  </div>
                </div>
              </template>
              <template #bottom>
                <div class="requests-list">
                  <div class="requests-list__header">
                    Исполненные
                  </div>
                  <div class="requests-list__items">
                    <RequestCard
                      v-for="request in requestsDone"
                      :key="request.id"
                      :request="request"
                    />
                  </div>
                </div>
              </template>
            </TopBottomLayout>
          </template>
        </TopBottomLayout>
      </template>
      <template #right>
        <div class="results-editor">
          // заполнение протокола
        </div>
      </template>
    </TwoSidedLayout>
  </PageInnerLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import moment from 'moment';

import PageInnerLayout from '@/layouts/PageInnerLayout.vue';
import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import TopBottomLayout from '@/layouts/TopBottomLayout.vue';
import DateFieldNav from '@/fields/DateFieldNav.vue';

import RequestCard, { type Request } from './RequestCard.vue';

const date = ref(moment().format('DD.MM.YYYY'));
const requestsDone = ref<Request[]>([
  {
    id: 1,
    patient: 'Тестов Тест Иванович',
    datetime: moment().subtract(2, 'days').format('DD.MM.YYYY HH:mm'),
    research: 'КТ лёгких',
    cardId: 101,
    waitFill: false,
  },
  {
    id: 2,
    patient: 'Тестов Тест Петровна',
    datetime: moment().subtract(1, 'days').format('DD.MM.YYYY HH:mm'),
    research: 'КТ брюшной полости',
    cardId: 102,
    waitFill: false,
  },
  {
    id: 3,
    patient: 'Тестов Тест Сергеевич',
    datetime: moment().subtract(3, 'days').format('DD.MM.YYYY HH:mm'),
    research: 'МРТ головного мозга',
    cardId: 103,
    waitFill: false,
  },
  {
    id: 4,
    patient: 'Тестов Тест Викторович',
    datetime: moment().subtract(4, 'days').format('DD.MM.YYYY HH:mm'),
    research: 'МРТ позвоночника',
    cardId: 104,
    waitFill: false,
  },
  {
    id: 5,
    patient: 'Тестов Тест Павловна',
    datetime: moment().subtract(5, 'days').format('DD.MM.YYYY HH:mm'),
    research: 'МРТ коленного сустава',
    cardId: 105,
    waitFill: false,
  },
]);

const requestsWait = ref<Request[]>([
  {
    id: 6,
    patient: 'Тестов Тест Сергеевна',
    datetime: moment().add(1, 'days').format('DD.MM.YYYY HH:mm'),
    research: 'КТ органов грудной клетки',
    cardId: 106,
    waitFill: true,
  },
  {
    id: 7,
    patient: 'Тестов Тест Николаевна',
    datetime: moment().add(2, 'days').format('DD.MM.YYYY HH:mm'),
    research: 'КТ почек',
    cardId: 107,
    waitFill: true,
  },
  {
    id: 8,
    patient: 'Тестов Тест Андреевич',
    datetime: moment().add(3, 'days').format('DD.MM.YYYY HH:mm'),
    research: 'МРТ тазобедренного сустава',
    cardId: 108,
    waitFill: true,
  },
  {
    id: 9,
    patient: 'Тестов Тест Владимировна',
    datetime: moment().add(4, 'days').format('DD.MM.YYYY HH:mm'),
    research: 'МРТ печени',
    cardId: 109,
    waitFill: true,
  },
  {
    id: 10,
    patient: 'Тестов Тест Игоревич',
    datetime: moment().add(5, 'days').format('DD.MM.YYYY HH:mm'),
    research: 'МРТ шейного отдела позвоночника',
    cardId: 110,
    waitFill: true,
  },
]);
</script>

<style lang="scss" scoped>
.requests-list {
  height: 100%;
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  background: #ffffff;
}

.requests-list__header {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f5f5f7;
  font-weight: 500;
  font-size: 14px;
  padding: 4px 6px;
  border-radius: 6px;
}

.requests-list__items {
  padding: 5px;
}

.results-editor {
  height: 100%;
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px;
}
</style>
