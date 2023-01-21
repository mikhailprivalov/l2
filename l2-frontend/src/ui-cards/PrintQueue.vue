<template>
  <ul class="nav navbar-nav">
    <li>
      <a
        href="#"
        @click.prevent="load"
      >
        Очередь печати <span class="badge badge-light">{{ printQueueCount }}</span></a>
    </li>
  </ul>
</template>

<script lang="ts">

export default {
  name: 'PrintQueue',
  computed: {
    printQueueCount() {
      return this.$store.getters.printQueueCount;
    },
  },
};
</script>

<style scoped lang="scss">
  .cancel-row {
    td, th {
      opacity: .6;
      text-decoration: line-through;
    }

    &:hover {
      td, th {
        opacity: 1;
        text-decoration: none;
      }
    }
  }

  .size-btn {
    width: 50px;
  }

  .fv {
    cursor: pointer;

    &:hover span {
      text-shadow: 0 0 3px rgba(#049372, .4);
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
    overflow-y: auto;
  }
</style>
