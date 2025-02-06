<template>
  <ul class="department">
    <li
      v-for="d in departmentFiltered"
      :key="d.pk"
    >
      <strong>{{ d.title }}</strong>
      <ul>
        <li
          v-for="x in d.users"
          :key="x.pk"
          :class="{ selected: x.pk === openPk }"
        >
          <a
            class="user-link"
            href="#"
            @click.prevent="open(x.pk)"
          >{{ x.username }} – {{ x.fio }}</a>
        </li>
        <li :class="{ selected: openPk === -1 && user.department === d.pk }">
          <a
            href="#"
            @click.prevent="open(-1, d.pk)"
          > <i class="fa fa-plus" /> добавить пользователя</a>
        </li>
      </ul>
    </li>
  </ul>
</template>

<script setup lang="ts">

</script>

<style scoped lang="scss">

</style>
