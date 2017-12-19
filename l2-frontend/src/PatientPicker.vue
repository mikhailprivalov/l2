<template>
  <div>
    <div class="input-group">
      <input type="text" class="form-control" v-model="query" placeholder="Введите запрос" autofocus>
      <div class="dropdown">
        <button class="btn btn-blue-nb dropdown-toggle" type="button" data-toggle="dropdown">{{selected_base.title}} <span class="caret"></span></button>
        <ul class="dropdown-menu">
          <li v-for="row in bases" :value="row.pk" v-if="!row.hide && row.pk !== selected_base.pk"><a href="#" @click.prevent="select_base(row.pk)">{{row.title}}</a></li>
        </ul>
      </div>
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
      },
      selected_base() {
        for (let b of this.bases) {
          if (b.pk === this.base) {
            return b
          }
        }
        return {title: '', pk: -1, hide: false}
      }
    },
    methods: {
      select_base(pk) {
        this.base = pk
      }
    }
  }
</script>

<style scoped lang="scss">
</style>
