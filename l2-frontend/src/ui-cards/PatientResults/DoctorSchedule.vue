<template>
  <li>
    <a href="#" @click.prevent="open_schedule">
      В регистратуру
    </a>
  </li>
</template>

<script>


export default {
  name: 'DoctorSchedule',
  data() {
    return {
      linkSchedule: '',
    };
  },
  mounted() {
    this.get()
  },
  methods: {
    open_schedule() {

    },
    async get_auth(){
        const params = await api('eln-link');
        this.link_auth = params.eln_auth;
        this.linkSchedule = params.link_schedule
      },
  },
}
</script>

<style lang="scss" scoped>
.an-body {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  display: block;
}

.an-body > div {
  align-self: stretch;
}

.d-root {
  height: 100%;
  display: flex;
  flex-wrap: wrap;
  flex-direction: row;

  > div {
    flex-basis: calc(50% - 8px);
    margin: 4px;

    > div {
      height: 100%;
      border: 1px solid rgba(0, 0, 0, .3);
      overflow-x: hidden;
      overflow-y: auto;

      &.overflow-visible {
        overflow: visible;
      }
    }
  }
}
</style>
