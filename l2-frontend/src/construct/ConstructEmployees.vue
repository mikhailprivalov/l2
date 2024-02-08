<template>
  <TwoSidedLayout>
    <template #left>
      <SimpleSelectableList
        v-model="activeSection"
        :rows="sections"
      />
    </template>
    <template #right>
      <TwoSidedLayout
        v-if="activeSection === 'positions'"
        key="positions"
      >
        <template #left>
          <EditFormList
            form-type="employeePosition"
            loading-text="загрузка должностей..."
            add-text="Добавить должность"
            with-creating
            with-name-filter
          />
        </template>
      </TwoSidedLayout>
      <TwoSidedLayout
        v-else-if="activeSection === 'people'"
        key="people"
      >
        <template #left>
          <EditFormList
            form-type="employeeEmployee"
            loading-text="загрузка сотрудников..."
            add-text="Добавить сотрудника"
            with-creating
            with-name-filter
          />
        </template>
      </TwoSidedLayout>
      <TwoSidedLayout
        v-else-if="activeSection === 'departments'"
        key="departments"
      >
        <template #left>
          <EditFormList
            v-model="selectedDepartmentId"
            form-type="employeeDepartment"
            loading-text="загрузка подразделений..."
            add-text="Добавить подразделение"
            with-creating
            with-name-filter
            selectable
          />
        </template>
        <template #right>
          <ContentCenterLayout v-if="selectedDepartmentId === null">
            <span :class="$style.notSelected">подразделение не выбрано</span>
          </ContentCenterLayout>
          <TopBottomLayout
            v-else
            :top-height-px="80"
          >
            <template #top>
              <FetchComponent
                :id="selectedDepartmentId"
                v-slot="slotProps"
                form-type="employeeDepartment"
                with-loader
              >
                <div
                  v-if="slotProps.data"
                  :class="$style.departmentHeader"
                >
                  <div class="row">
                    <div class="col-xs-6">
                      <div>Подразделение: {{ slotProps.data.name }}</div>
                      <div>Сотрудников: {{ slotProps.data.childrenElementsCount }}</div>
                      <div>
                        Скрыто: {{ slotProps.data.isActive ? 'нет' : 'да' }}
                      </div>
                    </div>
                    <div class="col-xs-6">
                      <div>
                        Создано: {{ slotProps.data.createdAt }}<span v-if="slotProps.data.whoCreate">,
                          {{ slotProps.data.whoCreate }}</span>
                      </div>
                      <div
                        v-if="
                          slotProps.data.whoUpdate
                            || (slotProps.data.updatedAt && slotProps.data.updatedAt !== slotProps.data.createdAt)
                        "
                      >
                        Обновлено: {{ slotProps.data.updatedAt }}<span v-if="slotProps.data.whoUpdate">,
                          {{ slotProps.data.whoUpdate }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </FetchComponent>
            </template>
            <template #bottom>
              <EditFormTable
                form-type="employeeEmployeePosition"
                :filters="employeeEmployeePositionFilters"
              />
            </template>
          </TopBottomLayout>
        </template>
      </TwoSidedLayout>
    </template>
  </TwoSidedLayout>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import ContentCenterLayout from '@/layouts/ContentCenterLayout.vue';
import TopBottomLayout from '@/layouts/TopBottomLayout.vue';
import SimpleSelectableList, { ListElementSimple } from '@/components/SimpleSelectableList.vue';
import EditFormList from '@/components/EditFormList.vue';
import FetchComponent from '@/components/FetchComponent.vue';
import EditFormTable from '@/components/EditFormTable.vue';
import type { IdOptional } from '@/components/EditableList.vue';

const selectedDepartmentId = ref<IdOptional>(null);

const activeSection = ref<IdOptional>(null);

const sections = ref<ListElementSimple[]>([
  {
    id: 'positions',
    name: 'Должности',
  },
  {
    id: 'people',
    name: 'Люди',
  },
  {
    id: 'departments',
    name: 'Подразделения и сотрудники',
  },
]);

const employeeEmployeePositionFilters = computed(() => ({
  department_id: selectedDepartmentId.value,
}));
</script>

<style lang="scss" module>
.notSelected {
  color: gray;
}

.departmentHeader {
  padding: 5px;
  overflow-x: hidden;
}
</style>
