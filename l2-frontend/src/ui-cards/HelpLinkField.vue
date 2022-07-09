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
  mounted() {
    this.load();
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
.fv {
  cursor: pointer;

  &:hover span {
    text-shadow: 0 0 3px rgba(#049372, 0.4);
    color: #049372;
  }
}

i {
  vertical-align: middle;
  display: inline-block;
  margin-right: 3px;
}

.inFavorite i {
  color: #93046d;
}

.tp {
  text-align: left;
  line-height: 1.1;
  padding: 5px;

  table {
    margin: 0;
  }

  max-height: 600px;
  max-width: 800px;
  overflow-y: auto;
}
</style>
