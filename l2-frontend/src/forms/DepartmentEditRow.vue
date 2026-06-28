<template>
  <tr :class="updated && 'has-success'">
    <td>{{ department.pk }}</td>
    <td>
      <input
        v-model="/* eslint-disable-line vue/no-mutating-props */ department.title"
        class="form-control"
        :disabled="!can_edit"
      >
    </td>
    <td>
      <input
        v-model="/* eslint-disable-line vue/no-mutating-props */ department.oid"
        class="form-control"
        placeholder="oid - подразделения"
        :disabled="!can_edit"
      >
    </td>
    <td>
      <Treeselect
        v-model="/* eslint-disable-line vue/no-mutating-props */ department.type"
        :multiple="false"
        :disable-branch-nodes="true"
        :options="types_options"
        placeholder="Тип не выбран"
        :clearable="false"
        :append-to-body="true"
        :disabled="!can_edit"
      />
    </td>
    <td>
      <div>
        <a
          href="#"
          class="a-under"
          style="padding-right: 10px"
          @click.prevent="editDepartment"
        >
          <i
            v-if="department.type === '7'"
            v-tippy
            class="fa fa-bed"
            style="margin-top: 10px; margin-left: 7px"
            title="Настройки подразделения"
          />
          <i
            v-if="department.type === '2'"
            v-tippy
            class="fa-solid fa-vials"
            style="margin-top: 10px; margin-left: 7px"
            title="Настройки подразделения"
          />
        </a>
      </div>
    </td>
    <SubGroupsDepartment
      v-if="subgroupsDepartment"
      :department_pk="department.pk"
      :readonly="false"
    />
  </tr>
</template>

<script setup lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import _ from 'lodash';
import {
  computed, getCurrentInstance, onMounted, onUnmounted, ref, watch,
} from 'vue';

import departmentsDirectory from '@/api/departments-directory';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';
import SubGroupsDepartment from '@/modals/SubGroupDepartment.vue';

const props = defineProps<{
  can_edit?: boolean;
  selected_hospital?: number;
  department: Record<string, any>;
  types_options?: any[];
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const updated = ref(false);
const timer = ref<ReturnType<typeof setTimeout> | null>(null);
const subgroupsDepartment = ref(false);

const departmentTitle = computed(() => props.department.title);
const departmentType = computed(() => props.department.type);
const departmentOid = computed(() => props.department.oid);

const save = async () => {
  const ok = await departmentsDirectory.sendDepartments({
    method: 'POST',
    hospital: props.selected_hospital,
    type: 'update',
    data: [
      {
        pk: props.department.pk,
        title: departmentTitle.value,
        type: departmentType.value,
        oid: departmentOid.value,
      },
    ],
  });
  if (ok) {
    root.$emit('msg', 'ok', 'Сохранено');
    updated.value = true;
    timer.value = setTimeout(() => {
      updated.value = false;
    }, 4000);
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }

  await store.dispatch(actions.GET_ALL_DEPARTMENTS);
};

const saveDeb = _.debounce(() => {
  save();
}, 300);

const saveClearDeb = () => {
  updated.value = false;
  saveDeb();
};

const editDepartment = () => {
  subgroupsDepartment.value = true;
};

const hideSubgroupsDepartment = () => {
  subgroupsDepartment.value = false;
};

watch(departmentTitle, saveClearDeb);
watch(departmentType, saveClearDeb);
watch(departmentOid, saveClearDeb);

onMounted(() => {
  root.$on('hide_subgroups_department', hideSubgroupsDepartment);
});

onUnmounted(() => {
  root.$off('hide_subgroups_department', hideSubgroupsDepartment);
  if (timer.value) {
    clearTimeout(timer.value);
  }
  saveDeb.cancel();
});
</script>
