<script setup lang="ts">
import { onMounted, ref } from 'vue';

import useNotify from '@/hooks/useNotify';
import UrlData from '@/UrlData';

const notify = useNotify();
const q = ref<string>('');

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'search', q: string, onResult: (ok: boolean, message: string) => void): void
}>();

const onSearch = (pk?: string) => {
  emit('search', pk || q.value, (ok, message) => {
    if (!ok) {
      notify.error(message || 'Ошибка');
      UrlData.set(null);
    } else {
      notify.ok(message || 'Найдено');
      if (!pk) {
        UrlData.set({ pk: pk || q.value });
      }
      q.value = '';
    }
  });
};

onMounted(() => {
  const storedData = UrlData.get();
  if (storedData && typeof storedData === 'object') {
    if (storedData.childrenDirection) {
      onSearch(storedData.childrenDirection);
    } else if (storedData.pk) {
      onSearch(storedData.pk);
    }
  }
});
</script>

<template>
  <div :class="$style.form">
    <input
      v-model.trim.number="q"
      type="text"
      class="form-control"
      autofocus
      placeholder="Случай или направление"
      @keyup.enter="onSearch()"
    >
    <button
      class="btn btn-blue-nb"
      :disabled="q === ''"
      @click="onSearch()"
    >
      Поиск
    </button>
  </div>
</template>

<script lang="ts">
export default {
  name: 'SearchForm',
};
</script>

<style module lang="scss">
.form {
  flex: 0 0 34px;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  flex-wrap: nowrap;
  justify-content: stretch;
}
</style>

<style scoped lang="scss">
.form-control,
.btn {
  align-self: stretch;
  border: none;
  border-radius: 0;
}

.form-control {
  border-bottom: 1px solid #b1b1b1;
  width: 226px !important;
  flex: 2 226px;
  min-width: 0;
}

.btn {
  flex: 3 94px;
  width: 94px;
}
</style>
