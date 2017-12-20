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
      <span class="input-group-btn"><button style="margin-right: -2px" class="btn last btn-blue-nb" type="button">Поиск</button></span>
    </div>
    <div class="text-center">
      <link-selector v-model="search_type" :options="search_types"></link-selector>
    </div>
  </div>
</template>

<script>
  import LinkSelector from './LinkSelector'

  export default {
    name: 'patient-picker',
    components: {LinkSelector},
    data() {
      return {
        base: -1,
        query: '',
        search_type: 'auto',
        search_types: [
          {key: 'auto', title: 'авто', about: 'Автоматическое определение типа запроса'},
          {key: 'full_fio', title: 'полное фио и дата рождения', about: 'Введите ФИО и дату раждения. Возможен ввод частями, например: Иванов Иван Иванович 01.01.1990 или Петров Пётр'},
          {key: 'short_fio', title: 'краткое фио и дата рождения', about: 'Введите инициалы и дату рождения, например: иии01011990'},
          {key: 'polis', title: 'номер полиса ОМС', about: 'Введите серию (при необходимости через пробел) и номер полиса, например: 1234АБВ 123456789 или 3876543213213413'},
        ]
      }
    },
    created() {
      if (this.bases.length === 0) {
        this.$store.watch(state => state.bases, (oldValue, newValue) => {
          this.check_base()
        })
      }

      this.check_base()
    },
    watch: {
      bases() {
        this.check_base()
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
        return {title: 'Не выбрана база', pk: -1, hide: false}
      }
    },
    methods: {
      select_base(pk) {
        this.base = pk
      },
      check_base() {
        if (this.base === -1 && this.bases.length > 0) {
          this.base = JSON.parse(JSON.stringify(this.bases[0].pk))
        }
      }
    }
  }
</script>

<style scoped lang="scss">
</style>
