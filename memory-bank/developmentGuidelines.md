# Development Guidelines: L2 Medical Information System

> **Language Requirement:** All Memory Bank documentation must be written in English.
> New entries, updates, and modifications must be in English.

## Command Execution Priority

### Always Follow This Order:
1. **Check Makefile first** - if command exists, use `make command`
2. **Use Poetry** - for Python/Django commands: `poetry run python ...`
3. **Use Yarn** - for JavaScript/Node.js: `yarn --cwd l2-frontend ...`
4. ❌ **NEVER** use direct python/npm without poetry/yarn

### Key Commands

**Installation:**
```bash
make install              # Full install (poetry + npm)
make poetry_bootstrap     # Python dependencies
make npm_install          # Node.js dependencies
```

**Database:**
```bash
make mm_poetry            # makemigrations + migrate
make migrate_poetry       # Apply migrations only
```

**Frontend:**
```bash
make build                # Development build
make build_prod           # Production build
make vue_dev              # Dev-server with HMR
```

**Development:**
```bash
make django_dev           # Django dev-server (port 8000 with HMR)
poetry run python manage.py <command>    # Django commands
```

---

## Backend (Django + Python)

### View Structure Pattern
```python
import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from laboratory.decorators import group_required

@login_required
@group_required("GroupName", "access_code")
def my_api_view(request):
    data = json.loads(request.body)
    # Business logic
    return JsonResponse({"ok": True, "result": data})
```

### Key Principles

**Security Decorators:**
- `@login_required` - mandatory for authenticated APIs
- `@group_required("Group1", "Group2")` - group membership check
- `@transaction.atomic` - for transactional operations

**Query Optimization:**
- Use `select_related()` for ForeignKey
- Use `prefetch_related()` for ManyToMany
- Complex queries in `sql_func.py` modules

**Settings:**
```python
from appconf.manager import SettingManager
setting = SettingManager.get("KEY", default="value")
```

**Logging:**
```python
import logging
from slog.models import Log

logger = logging.getLogger(__name__)
logger.info("Message")

# System logging
Log.objects.create(key="ACTION_TYPE", user=request.user, body=json.dumps(data))
```

**Async Tasks (Celery):**
```python
from celery import shared_task

@shared_task
def long_task(param):
    # Long operation
    return result

# Usage
task = long_task.delay(param)  # Async
result = long_task(param)      # Sync (for tests)
```

### Code Style
- **Black** (line-length: 190) - auto-formatting
- **Flake8** - linting
- **snake_case** - variables, functions
- **PascalCase** - classes
- **UPPER_CASE** - constants
- ⚠️ **DO NOT add comments/docstrings** unless user explicitly asks

---

## Frontend (Vue.js + TypeScript)

### 🚨 CRITICAL: Only `<script setup>` for New Code!
- ✅ All new components: `<script setup lang="ts">` with Composition API
- ✅ Vue 2.7 with Composition API (Vue 3 compatibility mode)
- ❌ NO Class Components for new code
- ❌ DO NOT rewrite existing Class Components (if they work)

### Component Structure
```vue
<template>
  <div>
    <h1>{{ title }}</h1>
    <button @click="handleClick">Click</button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';

interface Props {
  initialValue?: string;
}

const props = withDefaults(defineProps<Props>(), {
  initialValue: '',
});

const emit = defineEmits<{
  update: [value: string];
  close: [];
}>();

const count = ref<number>(0);
const doubled = computed(() => count.value * 2);

const handleClick = () => {
  count.value++;
  emit('update', String(count.value));
};

onMounted(() => {
  console.log('Mounted');
});

watch(() => props.initialValue, (newVal) => {
  console.log('Changed', newVal);
});
</script>

<style scoped>
/* Component styles */
</style>
```

### Layout Composition

**Built-in Layouts:**
- `PageInnerLayout` - page container (36px top padding)
- `TwoSidedLayout` - two-column (left + right)
- `TopBottomLayout` - vertical split (top + bottom)

**Layout Composition Example:**
```vue
<template>
  <PageInnerLayout>
    <TwoSidedLayout :left-width-px="300">
      <template #left>
        <TopBottomLayout :top-height-px="68" no-border>
          <template #top><!-- Selector --></template>
          <template #bottom><!-- Content --></template>
        </TopBottomLayout>
      </template>
      <template #right><!-- Right panel --></template>
    </TwoSidedLayout>
  </PageInnerLayout>
</template>
```

**⚠️ IMPORTANT - Borders:**
- Default: `TopBottomLayout` adds 1px border-bottom, `TwoSidedLayout` adds 1px border-right
- Sizes `:top-height-px` and `:left-width-px` INCLUDE this 1px border
- Use `:no-border` to remove border

### API Requests

**⚠️ USE ONLY Built-in API Module!**

**Method 1: Base API (simple requests):**
```typescript
import api from '@/api';

const response = await api('endpoint', {
  param: 'value',
  anotherParam: 123,
});

if (response.ok) {
  data.value = response.result;
}
```

**Method 2: Point Modules (typed endpoints):**
```typescript
import directionsPoint from '@/api/directions-point';

const response = await directionsPoint.getHistory({ cardId: 123 });
```

**Existing Point Modules:**
- `@/api/directions-point`, `@/api/patients-point`, `@/api/researches-point`
- `@/api/stationar-point`, `@/api/user-point`, `@/api/laboratory-point`
- `@/api/plans-point`, `@/api/cards-point`, `@/api/construct-point`

**Method 3: useApi Composable (reactive requests):**
```typescript
import useApi, { ApiStatus } from '@/api/useApi';
import { ref, computed } from 'vue';

const cardId = ref(123);

const apiParams = computed(() => ({
  path: 'endpoint',
  data: { cardId: cardId.value },
  disableReactiveRequest: false, // auto-reload on param change
}));

const { data, status, call, reset } = useApi<ResponseType>(
  apiParams,
  { defaultData: () => ({ ok: false, result: [] }) }
);

const isLoading = computed(() => status.value === ApiStatus.LOADING);
```

**When to Use:**
- `api()` - Simple requests, button clicks
- Point modules - Typed endpoints, frequently used
- `useApi` - Auto-load on mount, reactive params, status control

**❌ DO NOT use axios directly!**

### Vue-Treeselect (Dropdowns)

**Used for ALL selectors instead of native `<select>`:**

```vue
<template>
  <Treeselect
    v-model="selectedId"
    :options="items"
    :clearable="false"
    :multiple="false"
    :disable-branch-nodes="true"
    :append-to-body="true"
    placeholder="Select item"
    class="treeselect-noborder treeselect-34px"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const items = ref([
  { id: 1, label: 'First' },
  { id: 2, label: 'Second' },
]);
const selectedId = ref<number>(1);
</script>
```

**Key Points:**
- Data format: `{ id: number, label: string }`
- `v-model` binds to ID (not object!)
- Always import CSS
- Ready classes: `treeselect-noborder`, `treeselect-34px`, `treeselect-25px`

### Code Style
- **ESLint + Prettier**
- 2 spaces indentation
- Single quotes for strings
- **camelCase** - variables, functions
- **PascalCase** - components, classes, interfaces
- **UPPER_CASE** - constants
- Component files: `MyComponent.vue`

---

## Backend ↔ Frontend Integration

### API Response Format

**Success:**
```json
{
  "ok": true,
  "result": { /* data */ },
  "message": "Success"
}
```

**Error:**
```json
{
  "ok": false,
  "message": "Error description"
}
```

### Data Transmission

**Backend:**
```python
data = json.loads(request.body)
param = data.get('param')
```

**Frontend:**
```typescript
import api from '@/api';
const response = await api('endpoint', { param: 'value' });
```

### Date Handling

**Backend:**
```python
from django.utils import timezone
date = timezone.now()
# ISO format or DD.MM.YYYY
return date.strftime('%d.%m.%Y')
```

**Frontend:**
```typescript
import moment from 'moment';
const formatted = moment().format('DD.MM.YYYY');
const response = await api('endpoint', { date: formatted });
```

---

## Testing

**Backend:**
```python
# __spec__/test_something.py
from django.test import TestCase

class SomethingTestCase(TestCase):
    def test_something(self):
        result = some_function()
        self.assertEqual(result, expected)
```

**Frontend:**
```typescript
// tests/unit/Component.spec.ts
import { mount } from '@vue/test-utils';
import Component from '@/components/Component.vue';

describe('Component', () => {
  it('renders properly', () => {
    const wrapper = mount(Component);
    expect(wrapper.text()).toContain('Expected');
  });
});
```

---

## General Recommendations

1. **Write clear code** - code is read more often than written
2. **DO NOT write comments** unless user explicitly requests
3. **DO NOT delete existing comments** if related logic remains
4. **Use git** - commit often with clear messages
5. **Test critical logic** - cover with tests
6. **Optimize consciously** - working code first, then optimize
7. **Follow existing patterns** - study how similar code is written

### Package Managers
- Backend: **Poetry** (NOT pip!)
- Frontend: **Yarn** (NOT npm!)

```bash
# ✅ CORRECT
make migrate_poetry
poetry run python manage.py migrate
poetry add django-package
yarn --cwd l2-frontend add vue-package

# ❌ WRONG
pip install django-package
npm install vue-package
python manage.py migrate
```
