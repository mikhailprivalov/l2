<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" min-width="40%"
         max-width="40%" width="100%" marginLeftRight="auto" margin-top="20%">
    <span slot="header">Настройка группы</span>
    <div slot="body" style="min-height: 200px" class="directions-manage" v-if="loaded"></div>


  </modal>

</template>

<script>
  import Modal from '../ui-cards/Modal'
  import bacteria_point from '../api/bacteria-point'

    export default {
      name: "BacteriaEditTitleGroup",
      components: {Modal, },
      props: {
      group_pk: {
        type: Number,
        required: true
      },
      group_title: {
        type: String,
        required: true,
      },
      typesGroups: {
        type: String,
        required: true,
      },
    },
    }
</script>

<style scoped lang="scss">
  .directions-manage {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;
    & > div {
      align-self: stretch;
    }
  }

</style>
