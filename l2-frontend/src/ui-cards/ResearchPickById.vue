<template>
  <div class="research-wrapper">
    <ResearchPick
      v-if="research"
      :class="{ active }"
      class="research-select"
      :research="research"
      @click.native="toggle"
    />
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import { Research, ResearchPk } from '@/types/research';
import ResearchPick from '@/ui-cards/ResearchPick.vue';

@Component({
  components: {
    ResearchPick,
  },
  props: {
    pk: {
      type: Number,
      required: true,
    },
    selectedResearches: {
      type: Array,
      required: true,
    },
    kk: {
      type: String,
      default: '',
      required: false,
    },
  },
})
export default class ResearchPickById extends Vue {
  pk: ResearchPk;

  selectedResearches: ResearchPk[];

  kk: string;

  get research(): Research | null {
    return this.$store.getters.researches_obj[this.pk] || null;
  }

  get active() {
    return this.selectedResearches.includes(this.pk);
  }

  toggle() {
    if (this.active) {
      this.$root.$emit(`researches-picker:deselect${this.kk}`, this.pk);
    } else {
      this.$root.$emit(`researches-picker:add_research${this.kk}`, this.pk);
    }
  }
}
</script>

<style lang="scss" scoped>
.research-select {
  padding: 3px;
  border: 1px solid #6C7A89 !important;
  cursor: pointer;
  text-align: left;
  outline: transparent;
  display: flex;
  align-items: center;
  color: #000;
  background-color: #fff;
  transition: 0.15s linear all;
  font-size: 12px;

  &.active {
    background: #049372 !important;
    color: #fff;
  }

  &:hover {
    box-shadow: inset 0 0 8px rgba(0, 0, 0, .8) !important;
  }
}
</style>
