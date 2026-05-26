<template>
  <transition name="fade">
    <Modal
      v-if="opened"
      show-footer="true"
      white-bg="true"
      max-width="960px"
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
          ref="formRef"
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
      <div
        slot="footer"
        :class="$style.modalFooter"
      >
        <button
          v-if="showFormActions && allowDelete"
          type="button"
          class="btn btn-danger"
          @click="removeRecord"
        >
          Удалить
        </button>
        <div :class="$style.modalFooterRight">
          <button
            v-if="showFormActions"
            type="button"
            class="btn modal-form-save-btn"
            @click="triggerSave"
          >
            {{ submitText }}
          </button>
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            @click="hide"
          >
            Закрыть
          </button>
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
import api from '@/api';
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
  allowDelete?: boolean
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

const allowDelete = computed(() => Boolean(editId.value) && data.value.form?.allowDelete);

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
const formRef = ref(null);

const submitText = computed(() => data.value.form?.submitText || 'Сохранить');

const formSchema = computed<any[] | null>(() => {
  if (!data.value.form?.schema || !Array.isArray(data.value.form.schema)) {
    return null;
  }

  return [
    ...data.value.form.schema,
    {
      type: 'submit',
      label: submitText.value,
      'outer-class': 'modal-form-submit-hidden',
    },
  ];
});

const showFormActions = computed(
  () => status.value === ApiStatus.SUCCESS && data.value.ok && Boolean(formSchema.value),
);

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

const triggerSave = () => {
  const form = formRef.value as { $el?: HTMLElement } | null;
  const submitBtn = form?.$el?.querySelector?.('button[type="submit"]') as HTMLButtonElement | null;
  if (submitBtn) {
    submitBtn.click();
  }
};

const removeRecord = async () => {
  try {
    await root.$dialog.confirm('Вы уверены, что хотите удалить должность сотрудника?');
  } catch (_) {
    return;
  }

  const response = await api('edit-forms/delete', {
    formType: formType.value,
    formData: {
      id: editId.value,
      filters: filters.value,
    },
  });

  if (response.ok) {
    root.$emit('msg', 'ok', response.message || 'Удалено');
    store.dispatch(EDIT_SAVED_OBJECT, {
      formType: formType.value,
      id: editId.value,
      result: response.result || { deleted: true },
    });
    changed.value = false;
    hide();
  } else {
    root.$emit('msg', 'error', response.message || 'Ошибка удаления');
  }
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

  input {
    &[type='date'],
    &[type='number'],
    &[type='text'],
    &[type='time'],
    &[type='datetime-local'] {
      min-height: 0;
      height: 34px;
      padding: 6px 10px;
      line-height: 20px;
      box-sizing: border-box;
    }
  }

  select {
    height: 34px;
    padding: 6px 10px;
    line-height: 20px;
    box-sizing: border-box;
  }
}

::v-deep .formulate-form-row {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap;
  gap: 12px;
  margin: 0 0 10px !important;

  &::before,
  &::after {
    display: none;
  }

  > [class*='col-'] {
    flex: 1 1 0;
    min-width: 0;
    width: auto !important;
    float: none !important;
    padding: 0 !important;
  }

  .formulate-input {
    margin-bottom: 0;
  }
}

::v-deep .modal-form-submit-hidden {
  display: none !important;
}

::v-deep .modal-form-save-btn,
.modal-form-save-btn {
  width: auto !important;
  border-color: #049372 !important;
  background-color: #049372 !important;
  color: #fff !important;

  &:hover,
  &:focus,
  &:active {
    border-color: #037a60 !important;
    background-color: #037a60 !important;
    color: #fff !important;
  }
}
</style>

<style module lang="scss">
.modalFooter {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
}

.modalFooterRight {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-left: auto;
}

.loaderText {
  margin-top: 10px;
  color: gray;
}
</style>
