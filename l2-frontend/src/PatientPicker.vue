<template>
  <div>
    <div class="input-group">
      <div class="input-group-btn">
        <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown" style="width: 200px;text-align: left!important;"><span class="caret"></span> {{selected_base.title}}</button>
        <ul class="dropdown-menu">
          <li v-for="row in bases" :value="row.pk" v-if="!row.hide && row.pk !== selected_base.pk"><a href="#" @click.prevent="select_base(row.pk)">{{row.title}}</a></li>
        </ul>
      </div>
      <input type="text" class="form-control" v-model="query" placeholder="Введите запрос" autofocus>
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
    created() {
      let vm = this

      if (vm.bases.length === 0) {
        vm.$store.watch(state => state.bases, (oldValue, newValue) => {
          if (vm.base === null && newValue.length > 0) {
            vm.base = JSON.parse(JSON.stringify(newValue[0].pk))
          }
        })
      } else {
        if (vm.base === null) {
          vm.base = JSON.parse(JSON.stringify(vm.bases[0].pk))
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
