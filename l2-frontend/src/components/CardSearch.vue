<template>
  <div
    class="input-group"
    style="margin-right: -1px;"
  >
    <div class="input-group-btn">
      <button
        class="btn btn-blue-nb btn-ell dropdown-toggle nbr"
        type="button"
        data-toggle="dropdown"
        style="width: 115px;text-align: left!important;font-size: 12px;height: 34px;padding-right: 1px;"
        :title="selectedBase.title"
      >
        {{ selectedBase.title }}
      </button>
      <ul class="dropdown-menu">
        <li
          v-for="row in basesFiltered"
          :key="row.pk"
          :value="row.pk"
        >
          <a
            href="#"
            @click.prevent="selectBase(row.pk)"
          >{{ row.title }}</a>
        </li>
      </ul>
    </div>
    <input
      ref="q"
      v-model="query"
      type="text"
      class="form-control bob"
      placeholder="Поиск пациента"
      maxlength="255"
      @keyup.enter="search"
    >
    <span class="input-group-btn">
      <button
        class="btn last btn-blue-nb nbr"
        type="button"
        :disabled="!queryValid || inLoading"
        @click="search"
      >
        <i class="fa fa-search" />
      </button>
    </span>
    <Modal
      v-show="showModal"
      ref="modal"
      show-footer="true"
      @close="hideModal"
    >
      <span slot="header">Найдено несколько карт</span>
      <div slot="body">
        <table
          class="table table-responsive table-bordered table-hover"
          style="background-color: #fff;max-width: 680px"
        >
          <colgroup>
            <col width="95">
            <col width="155">
            <col>
            <col width="140">
          </colgroup>
          <thead>
            <tr>
              <th>Категория</th>
              <th>Карта</th>
              <th>ФИО, пол</th>
              <th>Дата рождения</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, i) in foundedCards"
              :key="row.num"
              class="cursor-pointer"
              @click="selectCard(i)"
            >
              <td class="text-center">
                {{ row.type_title }}
              </td>
              <td>{{ row.num }}</td>
              <td>{{ row.family }} {{ row.name }} {{ row.twoname }}, {{ row.sex }}</td>
              <td class="text-center">
                {{ row.birthday }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div
        slot="footer"
        class="text-center"
      >
        <small>Показано не более 10 карт</small>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  onMounted,
  ref,
  watch,
} from 'vue';

import { useStore } from '@/store';
import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';
import patientsPoint from '@/api/patients-point';

defineProps<{ value?: any }>();
const store = useStore();

// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
const instance = getCurrentInstance()!.proxy;

const base = ref(-1);
const query = ref('');
const foundedCards = ref<any[]>([]);
const selectedCard = ref<any>({});
const showModal = ref(false);
const loaded = ref(false);

const bases = computed(() => store.getters.bases);
const selectedBase = computed(() => {
  for (const b of bases.value) {
    if (b.pk === base.value) {
      return b;
    }
  }
  return {
    title: 'Не выбрана база', pk: -1, hide: false, history_number: false, fin_sources: [],
  };
});
const basesFiltered = computed(() => bases.value.filter((row: any) => !row.hide && row.pk !== selectedBase.value.pk));
const normalizedQuery = computed(() => query.value.trim());
const queryValid = computed(() => normalizedQuery.value.length > 0);
const inLoading = computed(() => store.getters.inLoading);

function emitInput() {
  let pk = -1;
  if ('pk' in selectedCard.value) {
    pk = selectedCard.value.pk;
  }
  if (pk === -1) {
    instance.$emit('input', {
      pk: -1,
      num: '',
      base: '',
      base_pk: -1,
      is_rmis: false,
      fio: '',
      sex: '',
      bd: '',
      age: '',
    });
    return;
  }
  instance.$emit('input', {
    pk,
    num: selectedCard.value.num,
    base: selectedBase.value.title,
    base_pk: selectedBase.value.pk,
    is_rmis: selectedCard.value.is_rmis,
    fio: [selectedCard.value.family, selectedCard.value.name, selectedCard.value.twoname].join(' ').trim(),
    sex: selectedCard.value.sex,
    bd: selectedCard.value.birthday,
    age: selectedCard.value.age,
  });
}

function hideModal() {
  showModal.value = false;
  const modalRef = instance.$refs.modal;
  if (modalRef && 'modal' in Modal) {
    (modalRef as any).$el.style.display = 'none';
  } else if (modalRef && 'style' in modalRef) {
    (modalRef as HTMLElement).style.display = 'none';
  }
}

function clear() {
  loaded.value = false;
  selectedCard.value = {};
  foundedCards.value = [];
  if (query.value.includes('card_pk:')) {
    query.value = '';
  }
  emitInput();
}

function selectCard(index: number) {
  hideModal();
  selectedCard.value = foundedCards.value[index];
  emitInput();
  loaded.value = true;
  instance.$root.$emit('patient-picker:select_card');
}

function checkBase() {
  if (base.value === -1 && bases.value.length > 0) {
    const params = new URLSearchParams(window.location.search);
    const rmisUid = params.get('rmis_uid');
    const basePk = params.get('base_pk');
    const cardPk = params.get('card_pk');
    const ofname = params.get('ofname');
    const ofnameDep = params.get('ofname_dep');
    const q = params.get('q');

    if (rmisUid) {
      window.history.pushState('', '', window.location.href.split('?')[0]);
      for (const row of bases.value) {
        if (row.code === 'Р') {
          base.value = row.pk;
          query.value = rmisUid;
          break;
        }
      }
      if (base.value === -1) {
        base.value = bases.value[0].pk;
      }
    } else if (basePk) {
      window.history.pushState('', '', window.location.href.split('?')[0]);
      for (const row of bases.value) {
        if (row.pk === parseInt(basePk, 10)) {
          base.value = row.pk;
          break;
        }
      }
      if (base.value === -1) {
        base.value = bases.value[0].pk;
      }
      if (cardPk) {
        query.value = `card_pk:${cardPk}`;
      }
    } else if (q) {
      window.history.pushState('', '', window.location.href.split('?')[0]);
      for (const b of bases.value) {
        if (b.internal_type) {
          base.value = b.pk;
          break;
        }
      }
      if (base.value === -1) {
        base.value = bases.value[0].pk;
      }
      query.value = q;
    } else {
      base.value = bases.value[0].pk;
    }
    window.$(instance.$refs.q).focus();
    emitInput();
  }
}

function search() {
  if (!queryValid.value || inLoading.value) return;
  checkBase();
  window.$('input').each(function () {
    window.$(this).trigger('blur');
  });
  clear();
  store.dispatch(actions.ENABLE_LOADING, { loadingLabel: 'Поиск карты' });
  patientsPoint.searchCard(base.value, query.value, true).then((result: any) => {
    if (result.results) {
      foundedCards.value = result.results;
      if (foundedCards.value.length > 1) {
        const modalRef = instance.$refs.modal;
        if (modalRef && 'modal' in Modal) {
          (modalRef as any).$el.style.display = 'flex';
        } else if (modalRef && 'style' in modalRef) {
          (modalRef as HTMLElement).style.display = 'flex';
        }
        showModal.value = true;
      } else if (foundedCards.value.length === 1) {
        selectCard(0);
      } else {
        instance.$root.$emit('msg', 'error', 'Не найдено\nКарт по такому запросу не найдено');
      }
    } else {
      instance.$root.$emit('msg', 'error', 'Ошибка на сервере');
    }
  }).catch((error: any) => {
    instance.$root.$emit('msg', 'error', `Ошибка на сервере\n${error.message}`);
  }).finally(() => {
    store.dispatch(actions.DISABLE_LOADING);
  });
}

function selectBase(pk: number) {
  base.value = pk;
  emitInput();
  search();
}

watch(bases, () => {
  checkBase();
});

onMounted(() => {
  checkBase();
  store.watch((state: any) => state.bases, () => {
    checkBase();
  });
  instance.$root.$on('search', () => {
    search();
  });
});
</script>

<style lang="scss">
  .select-td {
    padding: 0 !important;

    .bootstrap-select {
      height: 38px;
      display: flex !important;
      button {
        border: none !important;
        border-radius: 0 !important;
        .filter-option {
          text-overflow: ellipsis;
        }
      }
    }
  }

  .hovershow {
    position: relative;

    a {
      font-size: 12px;
    }

    .hovershow1 {
      top: 1px;
      position: absolute;

      a {
        color: grey;
        display: inline-block;
      }
      color: grey;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
    .hovershow2 {
      opacity: 0;
    }

    &:hover {
      .hovershow1 {
        display: none;
      }
      .hovershow2 {
        opacity: 1;
        transition: .5s ease-in opacity;
      }
    }
  }

  .bob {
    border-left: none !important;
    border-top: none !important;
    border-right: none !important;
  }
</style>
