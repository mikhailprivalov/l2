<template>
  <div v-frag>
    <div class="panel panel-default panel-flt">
      <ul class="list-group">
        <li class="list-group-item">
          <div class="row">
            <div class="col-xs-12 col-md-3 col-lg-3">Вход выполнен как: {{ user_data.username }}</div>
            <div class="col-xs-12 col-md-6 col-lg-6 text-center text-left-xs">
              {{ fio_dep }}
            </div>
            <div class="col-xs-12 col-md-3 col-lg-3 text-right text-left-xs">
              <a href="/logout" class="btn btn-blue-nb">Выход</a>
            </div>
          </div>
        </li>
        <li class="list-group-item">
          Группы:
          <div class="row dash-buttons groups-btns">
            <div class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb5" v-for="g in user_data.groups" :key="g">
              <div class="label label-default bw100 btn-ell" :title="g">{{ g }}</div>
            </div>
          </div>
        </li>
        <li class="list-group-item" v-if="user_data.specialities && user_data.specialities.length > 0">
          Специальности:
          <div class="row dash-buttons groups-btns" v-for="s in specialities" :key="s">
            <div class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb5">
              <div class="label label-default bw100 btn-ell" :title="s">{{ s }}</div>
            </div>
          </div>
        </li>
      </ul>
    </div>
    <div class="row menu dash-buttons text-center">
      <div class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb10 dash-btn" v-for="b in buttons" :key="b.title">
        <router-link :to="b.url" class="panel-body" :target="b.nt && '_blank'">
          <span>{{ b.title }}</span>
        </router-link>
      </div>
    </div>
    <hr/>
    <div class="row dash-buttons text-center">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 mb10 dash-btn dash-info">
        <div class="panel-body">
                <span>
                    <span>L2</span><br/>
                    <span>{{ menu.version }}</span>
                </span>
        </div>
      </div>
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 mb10 dash-btn dash-info" v-if="menu.region === '38'">
        <a href="http://l2-irk.ru" target="_blank" class="panel-body">
          <span>l2-irk.ru</span>
        </a>
      </div>
      <div class="col-xs-12 col-sm-6 col-md-4 col-lg-4 mb10 dash-btn dash-info" v-else-if="menu.region === 'DEMO'">
        <div class="panel-body">
            <span>
                <span>DEMO</span>
            </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { mapGetters } from 'vuex';
import { Menu, Button } from '@/types/menu';

@Component({
  computed: {
    ...mapGetters(['menu', 'user_data']),
    buttons() {
      if (!this.menu || !this.menu.buttons) {
        return [];
      }

      return this.menu.buttons.filter(b => !b.not_show_home && !b.hr);
    },
    fio_dep() {
      return [this.user_data.fio, this.user_data.department && this.user_data.department.title]
        .filter(Boolean)
        .join(', ');
    },
  },
})
export default class MenuPage extends Vue {
  menu: Menu;

  buttons: Button[];

  fio_dep: string;
}
</script>

<style lang="scss" scoped>
.groups-btns {
  padding: 0;
  margin-right: 0;
  margin-left: 0
}

.mb5 {
  margin-bottom: 5px;
}

.mb10 {
  margin-bottom: 5px;
}

.menu.dash-buttons > div.mb10 {
  margin-right: 0;
}

.menu.row.dash-buttons {
    margin-right: -2px;
    margin-left: -2px;
}
</style>
