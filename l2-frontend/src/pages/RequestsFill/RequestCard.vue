<template>
  <div
    class="direction"
  >
    <div>{{ props.request.patient }}</div>
    <div class="research-row">
      <div class="row">
        <div class="col-xs-7">
          {{ props.request.datetime }}
        </div>
        <div class="col-xs-5 text-right">
          <span
            class="fill-status"
            :class="props.request.waitFill ? 'fill-status--wait' : 'fill-status--done'"
          >
            {{ props.request.waitFill ? 'Ожидает' : 'Заполнено' }}
          </span>
        </div>
      </div>
      <div class="research-row">
        {{ props.request.research }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
export type Request = {
  id: number;
  patient: string;
  datetime: string;
  research: string;
  cardId: number;
  waitFill: boolean;
};

const props = defineProps<{ request: Request }>();
</script>

<style scoped lang="scss">
.direction {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
}
.research-row {
  margin-top: 3px;
  margin-bottom: 3px;
  padding: 3px;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
}
.fill-status {
  font-size: 12px;
  font-weight: 500;
}
.fill-status--wait {
  color: #1448f4;
}
.fill-status--done {
  color: #2ecc40;
}
</style>
