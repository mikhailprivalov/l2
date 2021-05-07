<template>
  <div v-tippy="{ html: '#' + tid, reactive: true, arrow: true, delay: [500,0], animation: 'fade', duration: 0, theme: 'light'}">
    <span class="rps">{{ research.short_title || research.title }}</span>
    <div :id="tid" v-if="research.full_title || research.code || force_tippy">
      <div class="rtitle">{{research.full_title || research.title}}</div>
      <span class="s-code" v-if="research.code">{{research.code}}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'research-pick',
  props: {
    research: {
      type: Object,
      required: true,
    },
    force_tippy: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    tid() {
      return `research-pick-tip-${this.research.pk}`;
    },
  },
};
</script>

<style scoped>
  .rps {
    display: block;
    text-overflow: ellipsis;
    overflow: hidden;
    word-break: keep-all;
    max-height: 2.2em;
    line-height: 1.1em;
    cursor: pointer;
  }

  .s-code {
    font-size: 12px;
    margin-top: 5px;
  }

  .rtitle {
    font-size: 14px;
    max-width: 280px;
    text-align: justify;
    font-weight: 400;
  }
</style>
