<template>
  <Modal
    ref="modal"
    margin-top
    margin-left-right="auto"
    max-width="680px"
    show-footer="true"
    white-bg="true"
    width="100%"
    @close="hideModal"
  >
    <span slot="header">Данные абитуриента</span>
    <div
      slot="body"
      class="registry-body"
      style="min-height: 100px"
    >
      <h4 class="text-center">
        Заявления
      </h4>
      <div class="two-col-div">
        <div
          v-for="application in applications"
          :key="application.pk"
          class="application-div"
        >
          <label>Заявление № {{ application.pk }}</label> <br>
          <label>Cпециальность:</label>
          {{ application.speciality }} <br>
          <label>Дата:</label>
          {{ application.date }}<br>
          <div
            v-for="subject in application.subjects"
            :key="subject.pk"
          >
            <label>{{ subject.title }}
            </label>
            {{ subject.score }}
          </div>
        </div>
      </div>
    </div>
    <div slot="footer">
      <div>
        <button
          class="btn btn-blue-nb"
          type="button"
          @click="hideModal"
        >
          Закрыть
        </button>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">

import Modal from '@/ui-cards/Modal.vue';

export default {
  name: 'EnrolleesApplication',
  components: { Modal },
  props: {
    card_pk: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      applications: [],
    };
  },
  mounted() {
    this.getApplications();
  },
  methods: {
    hideModal() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('hide_enrollees');
    },
    async getApplications() {
      const data = await this.$api('/education/get-applications-by-card', { card_pk: this.card_pk });
      console.log(data);
      this.applications = data.result;
    },
  },
};
</script>

<style lang="scss" scoped>
.two-col-div {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-bottom: 5px;
}
.application-div {
  margin: 5px;
  padding: 0 5px;
}
</style>
