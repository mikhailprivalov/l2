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
    clinic: 'ОГАЗ Клиника1',
    datetime: '12:10',
    research: 'КТ лёгких',
    cardId: 101,
    waitFill: false,
  },
  {
    id: 2,
    clinic: 'Частная Клинка 2',
    datetime: '12:03',
    research: 'КТ брюшной полости',
    cardId: 102,
    waitFill: false,
  },
  {
    id: 3,
    clinic: 'Государственная Клинка 3',
    datetime: '12:01',
    research: 'МРТ головного мозга',
    cardId: 103,
    waitFill: false,
  },
  {
    id: 4,
    clinic: 'Частная Клинка 4',
    datetime: '12:00',
    research: 'МРТ позвоночника',
    cardId: 104,
    waitFill: false,
  },
  {
    id: 5,
    clinic: 'Частная Клинка 4',
    datetime: '12:01',
    research: 'МРТ коленного сустава',
    cardId: 105,
    waitFill: false,
  },
]);

const requestsWait = ref<Request[]>([
  {
    id: 6,
    clinic: 'Государственная Клинка 3',
    datetime: '12:00',
    research: 'КТ органов грудной клетки',
    cardId: 106,
    waitFill: true,
  },
  {
    id: 7,
    clinic: 'Частная Клинка 1',
    datetime: '11:31',
    research: 'КТ почек',
    cardId: 107,
    waitFill: true,
  },
  {
    id: 8,
    clinic: 'Частная Клинка 4',
    datetime: '10:02',
    research: 'МРТ тазобедренного сустава',
    cardId: 108,
    waitFill: true,
  },
  {
    id: 9,
    clinic: 'Частная Клинка 9',
    datetime: '10:01',
    research: 'МРТ печени',
    cardId: 109,
    waitFill: true,
  },
  {
    id: 10,
    clinic: 'Частная Клинка 10',
    datetime: '10:00',
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
