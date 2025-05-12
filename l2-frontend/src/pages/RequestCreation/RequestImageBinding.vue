<template>
  <div class="image-binding-root">
    <div class="image-binding-header">
      <div class="equipment-select-wrap">
        <Treeselect
          v-model="selectedEquipment"
          :options="equipmentList"
          :multiple="false"
          :disable-branch-nodes="true"
          class="equipment-select"
          :append-to-body="true"
          :clearable="false"
          :z-index="5001"
        />
      </div>
      <div class="date-select-wrap">
        <DateFieldNav
          :def="selectedDate"
          :val.sync="selectedDate"
          w="100px"
          light
          class="date-select"
        />
      </div>
    </div>
    <div class="image-list">
      <div
        v-if="isLoading"
        class="image-list-overlay"
      >
        <div class="spinner" />
      </div>
      <div
        v-for="image in images"
        :key="image.id"
        class="image-item"
      >
        <div class="image-info">
          <div class="image-date">
            {{ image.datetime }}
          </div>
          <div class="image-patient">
            {{ image.patient }}
          </div>
          <div class="image-equip-id">
            ID: {{ image.equipmentId }}
          </div>
          <div
            class="image-status"
            :class="image.linked ? 'linked' : 'unlinked'"
          >
            {{ image.linked ? 'Привязано' : 'Не привязано' }}
            <span
              v-if="image.linked && image.requestId"
              class="image-request-number"
            >
              ({{ image.requestId }})
            </span>
          </div>
        </div>
        <div class="image-actions">
          <button
            class="btn btn-blue-nb btn-xs"
            @click="toggleLink(image)"
          >
            {{ image.linked ? 'Отвязать' : 'Привязать' }}
          </button>
        </div>
      </div>
      <div
        v-if="images.length === 0"
        class="no-images"
      >
        Нет снимков
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import DateFieldNav from '@/fields/DateFieldNav.vue';
import api from '@/api';
import useLoader from '@/hooks/useLoader';
import useNotify from '@/hooks/useNotify';

type Equipment = {
  id: number;
  name: string;
};
type Image = {
  id: number;
  datetime: string;
  equipmentId: string;
  linked: boolean;
  requestId?: string;
  patient: string;
};

const root = getCurrentInstance().proxy.$root;
const loader = useLoader();
const notify = useNotify();

const equipmentList = ref<Equipment[]>([]);
const selectedEquipment = ref(equipmentList.value?.[0]?.id || null);
const selectedDate = ref(moment().format('DD.MM.YYYY'));
const images = ref<Image[]>([]);
const isLoading = ref(true);

const getEquipmentList = async () => {
  loader.inc();
  try {
    const { rows } = await api('requests/equipment');
    equipmentList.value = rows;
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error(error);
    notify.error('Ошибка при получении оборудования');
  } finally {
    loader.dec();
  }
};

const getImages = async () => {
  if (!selectedEquipment.value) {
    return;
  }
  isLoading.value = true;
  try {
    const { rows } = await api('requests/images', {
      equipmentId: selectedEquipment.value,
      date: selectedDate.value,
    });
    images.value = rows;
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error(error);
    root.$emit('msg', 'error', 'Ошибка при получении снимков');
  } finally {
    isLoading.value = false;
  }
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const toggleLink = async (image: Image) => {
  // TODO
};

onMounted(async () => {
  await getEquipmentList();
  await getImages();
});

watch([selectedEquipment, selectedDate], async () => {
  await getImages();
}, { immediate: true });

watch(equipmentList, async (newVal) => {
  selectedEquipment.value = newVal?.[0]?.id || null;
});
</script>

<style scoped lang="scss">
.image-binding-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  max-width: 800px;
}
.image-binding-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
  width: 100%;
}
.equipment-select-wrap {
  flex: 1 1 0;
  min-width: 0;
}
.date-select-wrap {
  width: 180px;
  display: flex;
  align-items: center;
}
.equipment-select {
  width: 100%;
}
.date-select {
  width: 100%;
}
.image-list {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 8px;
}
.image-list-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255,255,255,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f5fffb;
  border-top: 4px solid #049372;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.image-item {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  padding: 10px 14px 8px 14px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  background: #fff;
  box-shadow: 0 1px 4px 0 rgba(60,60,60,0.04);
  gap: 24px;
  min-width: 180px;
}
.image-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  width: 100%;
  flex: 1 1 auto;
}
.image-date {
  font-size: 15px;
  color: #333;
  font-weight: 500;
  margin-bottom: 0;
}
.image-patient {
  font-size: 14px;
  color: #222;
  font-weight: 500;
}
.image-equip-id {
  font-size: 13px;
  color: #888;
}
.image-status {
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 0;
}
.linked {
  color: #2ecc40;
}
.unlinked {
  color: #888;
}
.image-request-number {
  font-size: 13px;
  color: #2a6edc;
  margin-left: 0;
}
.image-actions {
  width: 110px;
  min-width: 90px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: flex-start;
  margin-top: 0;
}
.btn.btn-blue-nb.btn-xs {
  padding: 2px 12px;
  font-size: 13px;
  height: 26px;
  min-width: 70px;
}
.no-images {
  color: #aaa;
  font-style: italic;
  padding: 10px 0;
  text-align: center;
}
</style>
