<!-- eslint-disable vue/no-v-html -->
<template>
  <PageInnerLayout>
    <TopBottomLayout :top-height-px="35">
      <template #top>
        <div :class="$style.searchForm">
          <Treeselect
            v-model="selectedOrg"
            class="treeselect-noborder treeselect-34px"
            :options="orgs"
            :multiple="false"
            :disable-branch-nodes="true"
            :append-to-body="true"
            :clearable="false"
            placeholder="Выберите организацию"
          />
          <Treeselect
            v-model="selectedUser"
            class="treeselect-noborder treeselect-34px"
            :options="users"
            :multiple="false"
            :disable-branch-nodes="true"
            :append-to-body="true"
            :clearable="false"
            placeholder="Выберите пользователя"
          />
          <Treeselect
            v-model="selectedType"
            class="treeselect-noborder treeselect-34px"
            :options="types"
            :multiple="false"
            :disable-branch-nodes="true"
            :append-to-body="true"
            :clearable="false"
            placeholder="Выберите тип действия"
          >
            <template #value-label="{ node }">
              <template v-if="node.ancestors && node.ancestors.length">
                <span
                  v-for="ancestor in [...node.ancestors].reverse()"
                  :key="ancestor.id"
                >
                  {{ ancestor.label }}
                  <i
                    class="fa fa-angle-right"
                    :class="$style.angleRight"
                  />
                </span>
                {{ node.label }}
              </template>
              <template v-else>
                {{ node.label }}
              </template>
            </template>
          </Treeselect>
          <Treeselect
            v-model="selectedApplication"
            class="treeselect-noborder treeselect-34px"
            :options="applications"
            :multiple="false"
            :disable-branch-nodes="true"
            :append-to-body="true"
            :clearable="false"
            placeholder="Выберите приложение"
          />
          <input
            v-model="searchKey"
            type="text"
            class="form-control"
            :class="$style.formInput"
            placeholder="Ключ"
          >
        </div>
      </template>
      <template #bottom>
        <div
          ref="logsContainer"
          :class="$style.logsContainer"
          @scroll="handleScroll"
        >
          <div
            v-if="isLoading && logs.length === 0"
            :class="$style.loading"
          >
            <i class="fa fa-spinner fa-spin" />
          </div>
          <div
            v-if="!isLoading && logs.length === 0"
            :class="$style.loading"
          >
            Нет данных
          </div>
          <div
            v-for="log in logs"
            :key="log.id"
            :class="$style.logCard"
          >
            <div :class="$style.logContent">
              <div :class="$style.logDetails">
                <div :class="$style.logUser">
                  <i class="fa fa-user" />
                  {{ log.user.fio }}
                  <span
                    v-if="log.user.username"
                    :class="$style.username"
                  >({{ log.user.username }})</span>
                </div>
                <div
                  v-if="log.org.title"
                  :class="$style.logOrg"
                >
                  <i class="fa fa-building" />
                  {{ log.org.title }}
                </div>
                <div :class="$style.logType">
                  {{ log.type }}
                </div>
                <div :class="$style.logTime">
                  {{ log.time }}
                </div>
                <div
                  v-if="log.key"
                  :class="$style.logKey"
                >
                  <strong>ключ:</strong> {{ formatKey(log.key) }}
                </div>
                <div
                  v-if="log.application"
                  :class="$style.logApplication"
                >
                  <strong>приложение:</strong> {{ log.application.label || log.application.id }}
                </div>
              </div>
              <div :class="$style.logBody">
                <Collapse>
                  <pre
                    v-if="isValidJson(log.body)"
                    :class="$style.jsonBody"
                    v-html="highlightJson(log.body)"
                  />
                  <pre
                    v-else
                    :class="$style.textBody"
                  >{{ log.body }}</pre>
                </Collapse>
              </div>
            </div>
          </div>
          <div
            v-if="isLoadingMore"
            :class="$style.loadingMore"
          >
            <i class="fa fa-spinner fa-spin" /> Загрузка...
          </div>
          <div
            v-if="!hasMore && logs.length > 0"
            :class="$style.noMore"
          >
            Все записи загружены
          </div>
        </div>
      </template>
    </TopBottomLayout>

    <button
      v-show="showScrollToTop"
      :class="$style.scrollToTopButton"
      title="Наверх"
      @click="scrollToTop"
    >
      <i class="fa fa-arrow-up" />
    </button>
  </PageInnerLayout>
</template>

<script setup lang="ts">
import {
  onMounted,
  onUnmounted,
  ref,
  watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import hljs from 'highlight.js/lib/core';
import json from 'highlight.js/lib/languages/json';
import 'highlight.js/styles/github.css';
import debounce from 'lodash/debounce';

import PageInnerLayout from '@/layouts/PageInnerLayout.vue';
import api from '@/api';
import useLoader from '@/hooks/useLoader';
import TopBottomLayout from '@/layouts/TopBottomLayout.vue';
import Collapse from '@/components/Collapse.vue';

hljs.registerLanguage('json', json);

const loader = useLoader();

type SelectType = {
  id: number;
  label: string;
};

type SelectTypeWithChildren = SelectType & {
  children?: SelectType[];
};

type Log = {
  id: number;
  user: {
    id: number;
    fio: string;
    username?: string | null;
  };
  org: {
    id: number;
    title?: string | null;
  };
  application: {
    id: number;
    label?: string | null;
  } | null;
  key: string;
  body: string;
  type: string;
  time: string;
};

const orgs = ref<SelectType[]>([]);
const selectedOrg = ref<number>(-1);

const users = ref<SelectType[]>([]);
const selectedUser = ref<number>(-1);

const types = ref<SelectTypeWithChildren[]>([]);
const selectedType = ref<number>(-1);

const applications = ref<SelectType[]>([]);
const selectedApplication = ref<number>(-1);

const searchKey = ref<string>('');

const logs = ref<Log[]>([]);
const isLoading = ref(false);
const isLoadingMore = ref(false);
const hasMore = ref(true);
const lastId = ref<number | null>(null);
const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null);
const logsContainer = ref<HTMLElement | null>(null);
const showScrollToTop = ref(false);

const loadUsers = async () => {
  const usersData = await api('logs/users', { orgId: selectedOrg.value }).then(result => result.users);
  users.value = usersData;

  if (!users.value.find(user => user.id === selectedUser.value)) {
    selectedUser.value = usersData[0].id;
  }
};

const loadSearchParams = async () => {
  const [logTypes, orgsData, applicationsData] = await Promise.all([
    api('logs/types').then(result => result.types),
    api('logs/orgs').then(result => result.orgs),
    api('logs/applications').then(result => result.applications),
    loadUsers(),
  ]);
  orgs.value = orgsData;
  selectedOrg.value = orgsData[0].id;
  types.value = logTypes;
  selectedType.value = logTypes[0].id;
  applications.value = applicationsData;
  selectedApplication.value = applicationsData[0].id;
};

const stopPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value);
    pollingInterval.value = null;
  }
};

const loadLogs = async (options: {
  append?: boolean;
  loadNewer?: boolean;
} = {}) => {
  const { append = false, loadNewer = false } = options;

  if (append) {
    isLoadingMore.value = true;
  } else if (!loadNewer) {
    isLoading.value = true;
  }

  try {
    const params: any = {
      orgId: selectedOrg.value,
      userId: selectedUser.value,
      typeId: selectedType.value,
      key: searchKey.value || undefined,
      applicationId: selectedApplication.value,
    };

    if (append && lastId.value) {
      params.lastId = lastId.value;
    } else if (loadNewer && logs.value.length > 0) {
      params.afterId = logs.value[0].id;
    }

    const result = await api('logs/logs', params);
    const newLogs = result.logs || [];

    if (append) {
      logs.value = [...logs.value, ...newLogs];
      if (newLogs.length > 0) {
        lastId.value = newLogs[newLogs.length - 1].id;
      }
    } else if (loadNewer) {
      if (newLogs.length > 0) {
        logs.value = [...newLogs, ...logs.value];
      }
    } else {
      logs.value = newLogs;
      if (newLogs.length > 0) {
        lastId.value = newLogs[newLogs.length - 1].id;
      }
    }

    hasMore.value = newLogs.length > 0;
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Ошибка загрузки логов:', error);
  } finally {
    isLoading.value = false;
    isLoadingMore.value = false;
  }
};

const startPolling = () => {
  stopPolling();
  pollingInterval.value = setInterval(async () => {
    if (logsContainer.value && logsContainer.value.scrollTop === 0) {
      await loadLogs({ loadNewer: true });
    }
  }, 3000);
};

const handleScroll = async () => {
  if (!logsContainer.value) {
    return;
  }

  const { scrollTop, scrollHeight, clientHeight } = logsContainer.value;

  showScrollToTop.value = scrollTop > 0;

  if (scrollTop === 0) {
    startPolling();
  } else {
    stopPolling();
  }

  if (!logsContainer.value || isLoadingMore.value || !hasMore.value) return;

  if (scrollHeight - scrollTop - clientHeight < 100) {
    await loadLogs({ append: true });
  }
};

const scrollToTop = () => {
  if (logsContainer.value) {
    logsContainer.value.scrollTo({ top: 0 });
  }
};

const isValidJson = (str: string) => {
  try {
    JSON.parse(str);
    return true;
  } catch {
    return false;
  }
};

const highlightJson = (str: string) => {
  try {
    const formatted = JSON.stringify(JSON.parse(str), null, 2);
    return hljs.highlight(formatted, { language: 'json' }).value;
  } catch {
    return str;
  }
};

const formatKey = (key: string): string => {
  if (key.startsWith('[') && key.endsWith(']')) {
    return key.slice(1, -1);
  }
  return key;
};

const applyFilters = async () => {
  if (orgs.value.length < 1) {
    return;
  }
  stopPolling();
  lastId.value = null;
  hasMore.value = true;
  logsContainer.value?.scrollTo({ top: 0 });
  await loadLogs();
  startPolling();
};

const debouncedApplyFilters = debounce(applyFilters, 300);

watch([selectedOrg, selectedUser, selectedType, selectedApplication], applyFilters);

watch(searchKey, debouncedApplyFilters);

watch(selectedOrg, async () => {
  if (orgs.value.length >= 1) {
    loader.inc();
    await loadUsers();
    loader.dec();
  }
});

onMounted(async () => {
  loader.global.inc();
  await loadSearchParams();
  await loadLogs();
  startPolling();
  loader.global.dec();
});

onUnmounted(() => {
  stopPolling();
  debouncedApplyFilters.cancel();
});
</script>

<style lang="scss" module>
.searchForm {
  display: flex;
  align-items: center;
  justify-content: stretch;
  gap: 1px;
  background-color: #656d78;
}

.formInput {
  border: none;
  border-radius: 0;
  min-width: 25%;
}

.angleRight {
  margin-left: 1px;
  margin-right: 3px;
  width: 9px;
}

.logsContainer {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  overflow-y: auto;
  padding: 16px;
  background: #f8f9fa;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #6c757d;
  font-size: 16px;
  gap: 8px;
}

.logCard {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.logContent {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.logDetails {
  flex: 0 0 300px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.logUser {
  font-weight: 600;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 6px;

  i {
    color: #6c757d;
  }
}

.username {
  font-weight: 400;
  color: #6c757d;
  font-size: 14px;
}

.logOrg {
  color: #6c757d;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;

  i {
    color: #adb5bd;
  }
}

.logType {
  background: #6c757d;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
  align-self: flex-start;
}

.logTime {
  color: #6c757d;
  font-size: 12px;
}

.logKey, .logApplication {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  padding: 8px 12px;
  margin: 0;
  font-size: 12px;
  border-radius: 0 4px 4px 0;
}

.logApplication {
  background: #cde4ff;
  border-left: 4px solid #007bff;
}

.logBody {
  flex: 1;
  padding: 16px 20px;
  border-left: 1px solid #e9ecef;
}

.jsonBody {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  color: #495057;
  overflow-x: auto;
  margin: 0;
  white-space: pre-wrap;
}

.textBody {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  color: #495057;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.loadingMore {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #6c757d;
  gap: 8px;
}

.noMore {
  text-align: center;
  padding: 20px;
  color: #adb5bd;
  font-style: italic;
}

.scrollToTopButton {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background-color: white;
  color: #6c757d;
  border: 1px solid #e9ecef;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  font-size: 20px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.2s ease;

  &:hover {
    background-color: #f8f9fa;
    color: #495057;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  }
}
</style>
