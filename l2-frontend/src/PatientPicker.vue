<template>
  <div>
    <div class="input-group">
      <input type="text" class="form-control" v-model="query" placeholder="Введите запрос" autofocus>
      <span class="input-group-btn">
        <select class="btn btn" v-model.number="base">
          <option v-for="row in bases" :value="row.pk" v-if="!row.hide">{{row.title}}</option>
        </select>
      </span>
      <span class="input-group-btn"><button class="btn last btn-blue-nb" type="button">Поиск</button></span>
    </div>

  </div>
</template>

<script>
  export default {
    name: 'patient-picker',
    data() {
      return {
        base: null,
        query: ''
      }
    },
    watch: {
      bases(newVal) {
        if (newVal.length > 0) {
          this.base = JSON.parse(JSON.stringify(newVal[0].pk))
        }
      }
    },
    computed: {
      bases() {
        return this.$store.getters.bases
      }
    }
  }
</script>

<style scoped lang="scss">
  .input-group-btn {

    select.btn {
      text-align: left;
    }

    .btn {
      height: 34px;
      padding: 6px 12px;
      font-size: 14px;
      line-height: 1.42857143;
      margin-top: 0;
      margin-bottom: 0;
      border-radius: 0;
      background-color: #AAB2BD !important;
      border-color: #AAB2BD !important;
      border-left-width: 0;
    }

    .btn-blue-nb.last {
      border-radius: 0 4px 4px 0;
      margin-right: -2px;
    }
  }

</style>
