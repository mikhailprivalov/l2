<template>
  <Modal
    ref="modal"
    margin-top
    margin-left-right="auto"
    max-width="800px"
    show-footer="true"
    white-bg="true"
    width="100%"
    @close="hideModal"
  >
    <span slot="header">Данные абитуриента - {{ fio }} </span>
    <div
      slot="body"
      class="registry-body"
      style="min-height: 100px"
    >
      <h4 class="text-center">
        Заявления
      </h4>
      <div class="three-col-div">
        <div
          v-for="application in applications"
          :key="application.pk"
          class="application-div"
        >
          <label>Заявление №{{ application.pk }}</label> <br>
          <label>Cпециальность:</label>
          {{ application.speciality }} <br>
          <label>Дата:</label>
          {{ application.date }}<br>
          <div
            v-for="subject in application.subjects"
            :key="subject.pk"
          >
            <label>{{ subject.title }}:
            </label>
            {{ subject.grade }}
          </div>
        </div>
      </div>
      <h4 class="text-center">
        Достижения
      </h4>
      <div class="three-col-div">
        <div
          v-for="achievement in achievements"
          :key="achievement.pk"
        >
          <label>Достижение №{{ achievement.pk }}</label> <br>
          <label>Название:</label>
          {{ achievement.title }} <br>
          <label>Дата:</label>
          {{ achievement.date }}<br>
          <label>Балл:</label>
          {{ achievement.grade }} <br>
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
    fio: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      applications: [],
      achievements: [],
    };
  },
  mounted() {
    this.getApplications();
    this.getAchievements();
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
      this.applications = data.result;
    },
    async getAchievements() {
      const data = await this.$api('/education/get-achievements-by-card', { card_pk: this.card_pk });
      this.achievements = data.result;
    },
  },
};
</script>

<style lang="scss" scoped>
.three-col-div {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 5px;
}
.application-div {
  margin: 5px;
  padding: 0 5px;
}
</style>
