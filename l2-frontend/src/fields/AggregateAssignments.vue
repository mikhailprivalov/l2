<template>
  <div>
    <div>
      <table class="table">
        <colgroup>
          <col>
        </colgroup>
        <thead>
          <tr>
            <th class="text-center">
              <strong>Медицинское вмешательство</strong>
            </th>
            <th class="text-center">
              <strong>Дата назначения</strong>
            </th>
            <th class="text-center">
              <strong>Медицинское вмешательство</strong>
            </th>
            <th class="text-center">
              <strong>Медицинское вмешательство</strong>
            </th>
            <th class="text-center">
              <strong>Медицинское вмешательство</strong>
            </th>
          </tr>
        </thead>
        <tr>
          <td><div>fff</div></td>
        </tr>
      </table>
    </div>
    <div>
      <AggregatePharmacotherapy
        :direction="direction"
      />
    </div>
  </div>
</template>

<script>
// eslint-disable-next-line import/extensions
import AggregatePharmacotherapy from '@/fields/AggregatePharmacotherapy';

export default {
  name: 'AggregateAssignments',
  components: { AggregatePharmacotherapy },
  props: {
    direction: {},
  },
};
</script>

<style scoped>
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
</style>
