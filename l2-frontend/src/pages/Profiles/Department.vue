<template>
  <ul class="department">
    <li>
      <strong>{{ props.department.title }}</strong>
      <ul>
        <li
          v-for="user in props.department.users"
          :key="user.pk"
          :class="{ selected: user.pk === selectedUserId }"
        >
          <a
            class="user-link"
            href="#"
            @click.prevent="selectUser(user.pk)"
          >{{ user.username }} – {{ user.fio }}</a>
        </li>
        <li :class="{ selected: selectedUserId === -1 && user.department === props.department.pk }">
          <a
            href="#"
            @click.prevent="selectUser(-1, props.department.pk)"
          > <i class="fa fa-plus" /> добавить пользователя</a>
        </li>
      </ul>
    </li>
  </ul>
</template>

<script setup lang="ts">

import { ref } from 'vue';

const emit = defineEmits(['select-user']);
const props = defineProps({
  department: {
    required: true,
    type: Object,
  },
});

const selectedUserId = ref(-1);

const selectUser = (userId: number, departmentId: number = null) => {
  selectedUserId.value = userId;
  emit('select-user', { userId, departmentId });
};
</script>

<style scoped lang="scss">
.user-link {
  color: #000;
  text-decoration: none;

  &:hover {
    text-decoration: underline;
  }
}

.department {
  margin-bottom: 0;
}
ul {
  padding-left: 20px;
}

li > ul > li {
  list-style: none;

  &::before {
    color: #000;
    content: '\2022';
    font-size: 18px;
    line-height: 12px;
    padding-right: 8px;
    position: relative;
    top: 0;
  }

  &.selected::before {
    color: #26816a;
    text-shadow: 0 0 4px rgba(#26816a, 0.9);
  }
}

li.selected {
  a {
    font-weight: bold;

    &.user-link {
      text-shadow: 0 0 4px rgba(#26816a, 0.5);
    }

    &::before {
      content: '[';
      color: #26816a;
    }

    &::after {
      content: ']';
      color: #26816a;
    }
  }
}
</style>
