<template>
  <ul class="nav navbar-nav">
    <li class="dropdown">
      <a
        v-tippy="{
          html: '#help-link-field-view',
          reactive: true,
          interactive: true,
          arrow: true,
          animation: 'fade',
          duration: 0,
          theme: 'light',
          placement: 'bottom',
          trigger: 'click mouseenter',
          popperOptions: {
            modifiers: {
              preventOverflow: {
                boundariesElement: 'window',
              },
              hide: {
                enabled: false,
              },
            },
          },
        }"
        href="#"
        class="dropdown-toggle"
        @click.prevent
        @mouseenter="load"
      >
        Помощь
      </a>

      <div
        id="help-link-field-view"
        class="tp"
      >
        <div
          v-for="(element) in data"
          :key="element.param"
          :class="[{ 'strong-element' : element.label === 'Справка' }]"
        >
          {{ element.label }} {{ element.param }} — {{ element.value }}
          <br>
          <br>
        </div>
      </div>
    </li>
  </ul>
</template>

<script lang="ts">

export default {
  name: 'HelpLinkField',
  data() {
    return {
      data: {},
    };
  },
  methods: {
    async load() {
      const { data } = await this.$api('researches/help-link-field');
      this.data = data;
    },
  },
};
</script>

<style scoped lang="scss">
.tp {
  text-align: left;
  line-height: 1.1;
  padding: 5px;

  max-height: 600px;
  max-width: 800px;
  overflow-y: auto;
}
.strong-element {
  font-weight: bolder;
}
</style>
