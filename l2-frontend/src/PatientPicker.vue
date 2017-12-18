<template>
  <div>
    <div class="input-group">
      <input type="text" class="form-control" id="search-field" name="search-field" placeholder="Введите запрос">
      <span class="input-group-btn">
        <select class="btn" v-model.number="base">
          <option v-for="row in bases" :value="row.pk" v-if="!row.hide">{{row.title}}</option>
        </select>
      </span>
      <span class="input-group-btn"><button class="btn btn-blue-nb" type="button">Поиск</button></span>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'patient-picker',
    data() {
      return {
        base: JSON.parse(JSON.stringify(this.$store.getters.bases()[0].pk))
      }
    },
    computed: {
      bases() {
        return this.$store.getters.bases()
      }
    }
  }
</script>

<style scoped>
  .input-group-btn select {
    height: 34px;
    padding: 6px 12px;
    font-size: 14px;
    line-height: 1.42857143;
    background: #fff none;
    color: #434a54;
    border: 1px solid #aab2bd;
    margin-top: 0;
    margin-bottom: 0;
    border-radius: 0;
    border-left-width: 0;
  }
</style>
