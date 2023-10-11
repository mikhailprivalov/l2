<script setup lang="ts">
import { ref } from 'vue';

import patientsPoint from '@/api/patients-point';
import useLoader from '@/hooks/useLoader';
import useNotify from '@/hooks/useNotify';
import Modal from '@/ui-cards/Modal.vue';

const props = defineProps<{
  cardPk: number;
}>();
const loader = useLoader();
const notify = useNotify();
const isLoading = ref<boolean>(false);
const isEditing = ref<boolean>(false);
const anamnesisData = ref<any>({ text: '' });

const loadAnamnesis = async () => {
  isLoading.value = true;
  anamnesisData.value = await patientsPoint.loadAnamnesis({ card_pk: props.cardPk, skipHistory: true, withPatient: true });
  isLoading.value = false;
};

const editAnamnesis = async () => {
  loader.inc();
  anamnesisData.value = await patientsPoint.loadAnamnesis({ card_pk: props.cardPk, skipHistory: true, withPatient: true });
  loader.dec();
  isEditing.value = true;
};

const hideModalAnamnesisEdit = () => {
  isEditing.value = false;
};

const saveAnamnesis = async () => {
  loader.inc();
  await patientsPoint.saveAnamnesis({ card_pk: props.cardPk, text: anamnesisData.value.text });
  loader.dec();
  hideModalAnamnesisEdit();
  notify.ok('Сохранено');
};
</script>

<template>
  <div v-frag>
    <a
      v-tippy="{
        placement: 'right',
        arrow: true,
        reactive: true,
        popperOptions: {
          modifiers: {
            preventOverflow: {
              boundariesElement: 'window',
            },
            hide: {
              enabled: false,
            },
          },
        },
        interactive: true,
        html: '#template-anamnesis',
      }"
      href="#"
      class="a-under"
      @show="loadAnamnesis"
      @click.prevent="editAnamnesis"
    >Анамнез жизни</a>

    <div id="template-anamnesis">
      <strong>Анамнез жизни</strong><br>
      <span v-if="isLoading">загрузка...</span>
      <pre
        v-else
        :class="$style.anamnesisText"
      >{{ anamnesisData.text || 'нет данных' }}</pre>
    </div>

    <Modal
      v-if="isEditing"
      ref="modalAnamnesisEdit"
      show-footer="true"
      white-bg="true"
      max-width="710px"
      width="100%"
      margin-left-right="auto"
      margin-top
      @close="hideModalAnamnesisEdit"
    >
      <span slot="header">Редактор анамнеза жизни – {{ anamnesisData.patient }}</span>
      <div
        slot="body"
        style="min-height: 140px"
        class="registry-body"
      >
        <textarea
          v-model="anamnesisData.text"
          rows="14"
          class="form-control"
          placeholder="Анамнез жизни"
        />
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="hideModalAnamnesisEdit"
            >
              Отмена
            </button>
          </div>
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="saveAnamnesis"
            >
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<style module lang="scss">
.anamnesisText {
  padding: 5px;
  text-align: left;
  white-space: pre-wrap;
  word-break: keep-all;
  max-width: 600px;
}
</style>
