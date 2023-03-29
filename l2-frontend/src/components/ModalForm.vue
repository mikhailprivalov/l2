<template>
  <transition name="fade">
    <Modal
      v-if="opened"
      show-footer="true"
      white-bg="true"
      max-width="680px"
      width="100%"
      margin-left-right="auto"
      @close="hide"
    >
      <span slot="header">{{ modalHeader }}</span>
      <div
        v-if="status === ApiStatus.SUCCESS && data.ok && formSchema"
        slot="body"
      >
        <FormulateForm
          v-model="formValues"
          :schema="formSchema"
          @submit="save"
          @input="changed = true"
        />
      </div>
      <div
        v-else-if="status === ApiStatus.SUCCESS && (!data.ok || !formSchema)"
        slot="body"
        style="line-height: 200px;text-align: center"
      >
        {{ data.message || 'Ошибка' }}
      </div>
      <div
        v-else
        slot="body"
        style="line-height: 200px;text-align: center"
      >
        <Spinner />
        <div
          :class="$style.loaderText"
        >
          Загрузка формы
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-8" />
          <div class="col-xs-4">
            <button
              type="button"
              class="btn btn-primary-nb btn-blue-nb"
              @click="hide"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </transition>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, ref, watch,
} from 'vue';

import Modal from '@/ui-cards/Modal.vue';
import Spinner from '@/components/Spinner.vue';
import useApi, { ApiStatus } from '@/api/useApi';
import { useStore } from '@/store';
import { EDIT_HIDE, EDIT_SAVED_OBJECT } from '@/store/action-types';

const store = useStore();

const opened = computed(() => store.getters.editOpened);
const formType = computed(() => store.getters.editFormType);
const filters = computed(() => store.getters.editFilters);
const editId = computed(() => store.getters.editId);
const root = getCurrentInstance().proxy.$root;

interface FormSchema {
  title: string
  schema: any[]
  values: Record<string, any>
  submitText: string
}

type FormResponse = {
  ok: boolean
  message?: string
  form?: FormSchema
};

const apiParams = computed(() => ({
  path: 'edit-forms/markup',
  data: {
    formType: formType.value,
    formData: {
      id: editId.value,
      filters: filters.value,
    },
  },
  disableReactiveRequest: !opened.value,
}));

const { data, status, reset } = useApi<FormResponse>(apiParams, { defaultData: () => ({ ok: false }) });

const modalHeader = computed(
  () => (status.value !== ApiStatus.SUCCESS ? 'Загрузка формы' : (data.value.form?.title || 'Ошибка')),
);

const changed = ref(false);

const hide = async () => {
  if (changed.value) {
    try {
      await root.$dialog.confirm('Изменения не сохранены.\nПодтвердите закрытие формы');
    } catch (_) {
      return;
    }
  }
  changed.value = false;
  store.dispatch(EDIT_HIDE);
  setTimeout(() => {
    reset();
  }, 150);
};

const formValues = ref<Record<string, any>>({});

const formSchema = computed<any[] | null>(() => {
  if (!data.value.form?.schema || !Array.isArray(data.value.form.schema)) {
    return null;
  }

  const r = [
    ...data.value.form.schema,
    {
      type: 'submit',
      label: data.value?.form.submitText || 'Сохранить',
    },
  ];

  return r;
});

watch(data, () => {
  formValues.value = data.value.form?.values || {};
  setTimeout(() => {
    changed.value = false;
  }, 100);
});

const apiSaveParams = computed(() => ({
  path: 'edit-forms/save',
  data: {
    formType: formType.value,
    formData: {
      id: editId.value,
      filters: filters.value,
      values: formValues.value,
    },
  },
  disableReactiveRequest: true,
}));

type FormSavedResult = any

interface FormSaveResponse {
  ok: boolean
  message?: string
  result?: FormSavedResult
}

const { reset: saveReset, call: saveCall } = useApi<FormSaveResponse>(apiSaveParams, { defaultData: () => ({ ok: false }) });

const save = async () => {
  const result = await saveCall();
  if (result.ok) {
    root.$emit('msg', 'ok', result.message || 'Сохранено');
    store.dispatch(EDIT_SAVED_OBJECT, {
      formType: formType.value,
      id: editId.value,
      result: result.result,
    });
    changed.value = false;
    hide();
  } else {
    root.$emit('msg', 'error', result.message || 'Ошибка сохранения');
  }
  saveReset();
};
</script>

<style scoped lang="scss">
.modal-mask {
  align-items: stretch !important;
  justify-content: center !important;
}

::v-deep .panel-flt {
  margin: 41px;
  align-self: stretch !important;
  width: 100%;
  display: flex;
  flex-direction: column;
}

::v-deep .panel-body {
  flex: 1;
  padding: 10px !important;
  height: calc(100% - 144px);
  min-height: 200px;
  background: #fff !important;
}

::v-deep .formulate-input-element {
  max-width: 100% !important;
}
</style>

<style module lang="scss">
.loaderText {
  margin-top: 10px;
  color: gray;
}
</style>
