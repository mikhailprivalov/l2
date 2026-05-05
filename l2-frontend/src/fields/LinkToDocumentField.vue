<template>
  <div>
    <div
      v-if="!disabled"
      class="row"
    >
      <div class="col-xs-5">
        <div
          ref="searchContainer"
          class="attached-group search-select-container"
        >
          <div class="input-with-clear">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Введите номер направления"
              class="form-control"
              @focus="onFocus"
              @input="onInput"
            >
            <i
              v-if="searchQuery"
              class="fa fa-times clear-icon"
              @click="clearSearch"
            />
          </div>

          <transition name="fade">
            <ul
              v-if="isSearchOpened && !selectedDirection &&
                (directionData.length || searchLoading || (searchQuery.length >= 4 && !directionData.length))"
              class="dropdown-menu custom-dropdown"
            >
              <li
                v-if="searchLoading && directionData.length === 0"
                class="dropdown-item disabled"
              >
                <span class="search-text-info">Поиск документа...</span>
              </li>

              <li
                v-else-if="searchQuery.length >= 4 && directionData.length === 0"
                class="dropdown-item disabled"
              >
                <span class="search-text-info">Документов не найдено</span>
              </li>

              <li
                v-for="direction in directionData"
                :key="direction.id"
                class="dropdown-item"
                @mousedown.prevent="selectDirection(direction)"
              >
                <div class="default-slot-content">
                  <span class="document-text">{{ direction.id }} - {{ direction.label }}</span>
                </div>
              </li>
            </ul>
          </transition>

          <button
            class="btn btn-blue-nb attached-button"
            type="button"
            :disabled="!selectedDirection"
            @click="addLinkToDirection"
          >
            <i class="fa fa-plus" />
          </button>
        </div>
      </div>
    </div>

    <div
      class="row"
      style="margin-top: 5px"
    >
      <div class="col-xs-12">
        <table
          class="table table-responsive table-bordered table-condensed"
          style="background-color: #fff"
        >
          <thead>
            <tr>
              <th class="text-center">
                Ссылка на документ
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="selectedDirections.length === 0">
              <td class="text-center">
                нет ссылок на документы
              </td>
            </tr>
            <tr
              v-for="(direction, index) in selectedDirections"
              :key="index"
            >
              <td>
                <button
                  v-if="!disabled"
                  class="btn btn-blue-nb btn-xs"
                  @click="removeLink(index)"
                >
                  <i class="fa fa-times" />
                </button>
                <a
                  v-if="disabled"
                  :href="generateLink(direction)"
                  target="_blank"
                  class="a-under"
                >
                  {{ direction.id }} - {{ direction.label }}
                </a>
                <span v-else-if="!disabled">{{ direction.id }} - {{ direction.label }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, onBeforeUnmount, onMounted, onUnmounted, ref, watch,
} from 'vue';

const emit = defineEmits(['edit-link-field-value']);
const { proxy } = getCurrentInstance();
const api = proxy.$api;

const props = defineProps({
  value: {
    type: String,
    required: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const directionData = ref([]);
const selectedDirection = ref(null);
const selectedDirections = ref([]);
const searchQuery = ref('');
const isSearchOpened = ref(false);
const searchLoading = ref(false);
const debounceTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const abortController = ref<AbortController | null>(null);
const searchContainer = ref<HTMLElement | null>(null);

const onFocus = () => {
  if (!selectedDirection.value) {
    isSearchOpened.value = true;
  }
};

const onInput = () => {
  isSearchOpened.value = true;
  selectedDirection.value = null;
  directionData.value = [];
};

const handleGlobalClick = (event: MouseEvent) => {
  const el = searchContainer.value;
  if (el && !el.contains(event.target as Node)) {
    isSearchOpened.value = false;
  }
};

const getLinks = async () => {
  const { result } = await api(
    'directions/get-direction-data-for-link',
    { directions_id: props.value, mode: 'multiple' },
  );
  selectedDirections.value = result;
};

const searchDirection = async (directionId: string) => {
  if (abortController.value) {
    abortController.value.abort();
  }
  abortController.value = new AbortController();
  searchLoading.value = true;
  const { result } = await api(
    'directions/get-direction-data-for-link',
    { direction_id: directionId, mode: 'single' },
    null,
    { signal: abortController.value.signal },
  );
  directionData.value = result || [];
  if (!abortController.value?.signal.aborted) {
    searchLoading.value = false;
  }
};

watch(searchQuery, (newValue) => {
  if (debounceTimer.value) clearTimeout(debounceTimer.value);
  if (newValue.length >= 4 && !selectedDirection.value) {
    searchLoading.value = true;
    debounceTimer.value = setTimeout(() => {
      searchDirection(newValue);
    }, 1000);
  } else {
    directionData.value = [];
    searchLoading.value = false;
    if (abortController.value) abortController.value.abort();
  }
});

const selectDirection = (direction) => {
  selectedDirection.value = direction;
  searchQuery.value = `${direction.id} - ${direction.label}`;
  isSearchOpened.value = false;
};

const editFieldValue = () => {
  const selectedDirectionsIDs = ref([]);
  selectedDirections.value.forEach(obj => {
    selectedDirectionsIDs.value.push(obj.id);
  });
  emit('edit-link-field-value', selectedDirectionsIDs.value.join(','));
};

const addLinkToDirection = () => {
  if (selectedDirection.value) {
    if (!selectedDirections.value.some(row => row.id === selectedDirection.value.id)) {
      selectedDirections.value.push(selectedDirection.value);
      editFieldValue();
      selectedDirection.value = null;
      searchQuery.value = '';
      directionData.value = [];
    }
  }
};

const generateLink = (direction) => {
  const path = ref('');
  const directionId = ref(direction.id);
  if (direction.is_descriptive) {
    path.value = `/ui/results/descriptive#{%22pk%22:${directionId.value}}`;
  } else if (direction.is_hosp) {
    path.value = `/ui/stationar#{%22pk%22:${directionId.value},
    %22opened_list_key%22:null,%22opened_form_pk%22:null,%22every%22:false}`;
  } else if (direction.is_slave_hospital) {
    path.value = `/ui/stationar#{%22pk%22:${direction.hosp_direction_id},%22opened_list_key%22:"all",
    %22opened_form_pk%22:${directionId.value},%22every%22:false}`;
  } else if (direction.is_case) {
    path.value = `/ui/case-control#{%22pk%22:${directionId.value}}`;
  } else if (direction.is_lab) {
    path.value = `/ui/biomaterial/get#{%22pk%22:${directionId.value}}`;
  }
  return path.value;
};

const clearSearch = () => {
  searchQuery.value = '';
  selectedDirection.value = null;
  directionData.value = [];
  isSearchOpened.value = false;
  if (abortController.value) abortController.value.abort();
};

const removeLink = (index) => {
  selectedDirections.value.splice(index, 1);
  editFieldValue();
};

onMounted(() => {
  getLinks();
  document.addEventListener('mousedown', handleGlobalClick);
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleGlobalClick);
});

onBeforeUnmount(() => {
  if (debounceTimer.value) clearTimeout(debounceTimer.value);
  if (abortController.value) abortController.value.abort();
});
</script>

<style scoped lang="scss">
.input-with-clear {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;

  .form-control {
    padding-right: 30px;
    width: 100%;
  }

  .clear-icon {
    position: absolute;
    right: 10px;
    color: #ccc;
    cursor: pointer;
    z-index: 5;
    transition: color 0.2s;

    &:hover {
      color: #999;
    }
  }
}

.search-select-container {
  position: relative;
}

.custom-dropdown {
  display: block;
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  z-index: 1050;
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 6px 12px rgba(0,0,0,.175);
  max-height: 200px;
  overflow-y: auto;
  padding: 0;
  margin: 2px 0 0;
}

.dropdown-item {
  padding: 8px 12px;
  cursor: pointer;
  list-style: none;
  color: #333;

  &:hover {
    background-color: #f5f5f5;
  }

  &.disabled {
    cursor: default;
    color: #999;
    &:hover {
      background-color: transparent;
    }
  }
}

.document-text {
  font-size: 14px;
  display: inline-block;
}

.search-text-info {
  font-size: 13px;
  font-style: italic;
  color: #888;
}

.default-slot-content {
  display: flex;
  align-items: center;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.attached-group {
  display: flex;
  .form-control {
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    flex: 1;
  }
  .input-with-clear {
    .form-control {
      border-top-right-radius: 0;
      border-bottom-right-radius: 0;
    }
  }
  .attached-button {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    margin-left: -1px;
  }
}
</style>
