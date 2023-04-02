<template>
  <div>
    <h2>
      Тестируемся 3
    </h2>
    <div>
      <h3>
        Название отделения
      </h3>
      <Treeselect
        v-model="selectedPodrazdeleniya"
        :options="formattedPodrazdeleniya"
        placeholder="Выберите отделение"
      />
    </div>
    <div>
      <button @click="showFormWards=true">
        Добавить палату
      </button>
      <div v-if="showFormWards">
        <form>
          <lable>
            Название палаты:
            <input
              v-model="newWardTitle"
              type="text"
            >
          </lable>
          <button @click.prevent="addWard">
            Сохранить
          </button>
        </form>
      </div>
      <div>
        <div
          v-for="ward in wards"
          :key="ward.id"
        >
          {{ ward.title }}
          <ul>
            <li v-for="bed in beds[String(ward.id)]"
                :key="bed.id">
              {{ bed.bed_number }}
            </li>
          </ul>
          <div>
            <button type="reset" @click="showFormBeds=true; selectedWard=ward">
              Добавить койку
            </button>
            <div v-if="showFormBeds">
              <form>
                <lable>
                  Номер койки:
                  <input
                    v-model="newBedNumber"
                    type="text"
                  >
                </lable>
                <button @click.prevent="addBed">
                  Сохранить
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  name: 'ConstructWards',
  components: { Treeselect },
  data() {
    return {
      podrazdeleniya: [],
      wards: [],
      beds: [],
      showFormWards: false,
      showFormBeds: false,
      selectedPodrazdeleniya: [],
      selectedWard: null,
    };
  },
  computed: {
    formattedPodrazdeleniya() {
      return this.podrazdeleniya.map(item => ({
        id: item.id,
        label: item.title,
      }));
    },
  },
  watch: {
    selectedPodrazdeleniya() {
      this.getWards();
      this.getBeds();
    },
  },
  mounted() {
    this.getPodrazdeleniya();
  },
  methods: {
    async getPodrazdeleniya() {
      const response = await fetch('/api/get-podrazdeleniya');
      const data = await response.json();
      this.podrazdeleniya = data.podrazdeleniya;
    },
    async getWards() {
      const response = await fetch(`/api/get-wards?department=${this.selectedPodrazdeleniya}`);
      const data = await response.json();
      this.wards = data.wards;
      await this.getBeds();
    },
    async getBeds() {
      const wardsId = this.wards.map(ward => ward.id).join(',');
      const response = await fetch(`/api/get-beds?wardsId=${wardsId}`);
      const data = await response.json();
      this.beds = data.beds;
    },
    async addWard() {
      const newWard = {
        title: this.newWardTitle,
        department: this.selectedPodrazdeleniya,
        hide: false,
      };
      const response = await fetch('/api/add-ward', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newWard),
      });

      const data = await response.json();

      this.wards.push(data);
      this.showFormWards = false;
      this.newWardTitle = '';
      await this.getWards();
    },
    async addBed() {
      const newBed = {
        bed_number: this.newBedNumber,
        ward: this.selectedWard.id,
        hide: false,
      };
      const response = await fetch('/api/add-bed', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newBed),
      });

      // const data = await response.json();

      // this.beds.push(data);
      this.showFormBeds = false;
      this.newBedNumber = '';
      await this.getBeds();
    },
  },
};
</script>

<style scoped>

</style>
