<template>
  <div
    class="research"
  >
    {{ 'Анализы' }}
    <table class="table">
      <colgroup>
        <col>
        <col width="30">
        <col width="30">
      </colgroup>
      <tr
        v-for="research in props.tube.researches"
        :key="research.pk"
      >
        <td class="border research-title">
          {{ research.title }}
        </td>
        <td class="border">
          <div class="button">
            <button
              class="transparent-button"
              @click="hideResearch(research)"
            >
              {{ research.hide ? 'пок' : 'скр' }}
            </button>
          </div>
        </td>
        <td class="border">
          <div class="button">
            <button class="transparent-button">
              <i class="fa fa-pencil" />
            </button>
          </div>
        </td>
      </tr>
    </table>
    <div> {{ 'Ёмкости' }}</div>
    <div
      v-for="currentTube in props.tube.tubes"
      :key="currentTube.pk"
      class="tube-item"
    >
      <div
        class="sq"
      >
        <div
          class="color-sq"
          :style="'background-color: ' + currentTube.color"
        />
      </div>
      <div> {{ currentTube.title }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance } from 'vue';

const props = defineProps({
  tube: {
    type: Object,
    required: true,
  },
});
const root = getCurrentInstance().proxy.$root;

const hideResearch = async (research) => {
  if (research.hide) {
    // eslint-disable-next-line no-param-reassign
    research.hide = !research.hide;
    root.$emit('msg', 'ok', 'Показано');
  } else {
    // eslint-disable-next-line no-param-reassign
    research.hide = !research.hide;
    root.$emit('msg', 'ok', 'Скрыто');
  }
};

</script>

<style scoped lang="scss">
.sq {
    padding: 3px;
    display: inline-block;
    background-color: #efefef;
    border: 1px solid #bbb;
    border-radius: 5px;
    margin-right: 5px;
    vertical-align: middle;
}
.color-sq {
    height: 12px;
    width: 12px;
}
.tube-item {
  display: flex;

}
.table {
  table-layout: fixed;
}
.border {
  border: 1px solid #bbb;;
}
.research {
  background-color: #fff;
  padding: 5px;
  margin: 10px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;

  &.rhide {
    background-image: linear-gradient(#6c7a89, #56616c);
    color: #fff;
  }

  &:hover {
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 1;
    transform: scale(1.008);
  }
}
.research:not(:first-child) {
  margin-top: 0;
}

.research:last-child {
  margin-bottom: 0;
}

.research-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 3px;
  padding-top: 1px;
  padding-bottom: 1px;
}

.research-edit {
  text-align: center;

  .transparent-button {
    padding: 0 5px;
  }
}

.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}

.transparent-button {
  background-color: transparent;
  align-self: stretch;
  flex: 1;
  color: #434A54;
  border: none;
  padding: 1px 0;
}
.transparent-button:hover {
  background-color: #434a54;
  color: #FFFFFF;
  border: none;
}
.transparent-button:active {
  background-color: #37BC9B;
  color: #FFFFFF;
}
</style>
