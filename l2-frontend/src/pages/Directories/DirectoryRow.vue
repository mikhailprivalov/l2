<template>
  <tr>
    <td>{{ row.title }}</td>
    <td>{{ row.code }}</td>
    <td
      v-for="(f, fpk) in fields"
      :key="fpk"
    >
      {{ row.fields[fpk] }}
    </td>
    <td
      v-if="canEdit"
      class="x-cell"
      style="width: 34px;"
    >
      <button
        v-tippy
        class="btn btn-sm btn-cell"
        title="Редактировать"
        @click="$root.$emit('directory-row-editor:open', row.pk)"
      >
        <i class="fa fa-pencil" />
      </button>
    </td>
  </tr>
</template>

<script lang="ts">
export default {
  name: 'DirectoryRow',
  props: {
    row: {
      type: Object,
      required: true,
    },
    fields: {
      type: Object,
      required: true,
    },
    canEdit: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {};
  },
};
</script>

<style lang="scss" scoped>
  .td-empty {
    text-align: center;
    color: #999;
    font-style: italic;
  }
</style>
