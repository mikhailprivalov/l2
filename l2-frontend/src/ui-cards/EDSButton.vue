<template>
  <fragment v-if="direction.all_confirmed && eds">
    <button class="btn btn-blue-nb nbr" @click="modal_opened = true">
      Подписать ЭЦП
    </button>
    <modal v-if="modal_opened" ref="modal" @close="hide_modal" show-footer="true"
           white-bg="true" width="100%" marginLeftRight="34px" margin-top="30px">
      <span slot="header">Подписать ЭЦП результат направления {{ direction.pk }}</span>
      <div slot="body" class="eds-body">
        <iframe :src="eds_base"></iframe>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="hide_modal" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </modal>
  </fragment>
</template>

<script>
import Modal from "@/ui-cards/Modal";

export default {
  name: 'EDSButton',
  components: {
    Modal,
  },
  props: {
    direction: {}
  },
  data() {
    return {
      modal_opened: false,
    }
  },
  methods: {
    hide_modal() {
      this.modal_opened = false;
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none'
      }
    },
  },
  computed: {
    eds() {
      return this.$store.getters.modules.l2_eds;
    },
    eds_base() {
      return this.$store.getters.modules.eds_base_url;
    },
  },
}
</script>

<style scoped lang="scss">
.eds-body {
  height: calc(100vh - 179px);
  position: relative;

  iframe {
    display: block;
    width: 100%;
    height: 100%;
    border: none;
  }
}

.btn.nbr {
  margin: 0 5px;
}
</style>
