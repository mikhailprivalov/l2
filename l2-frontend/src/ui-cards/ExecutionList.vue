<template>
  <fragment>
    <a href="#" @click.prevent="doOpen">
      Лист исполнения
    </a>
    <MountingPortal mountTo="#portal-place" name="ExecutionList" append v-if="open">
      <modal @close="open = false" show-footer="true" white-bg="true"
             max-width="710px" width="100%" marginLeftRight="auto">
        <span slot="header">Создание листа исполения</span>
        <div slot="body">
          <div class="filters">
            <div class="input-group">
              <span class="input-group-addon">Дата приёма материала</span>
              <date-range v-model="date_range"/>
            </div>
            <div style="margin-top: 10px">
              <researches-picker v-model="selected_researches"
                                 autoselect="none"
                                 :just_search="true"
                                 :hidetemplates="true"
                                 style="border-top: 1px solid #eaeaea;border-bottom: 1px solid #eaeaea;height: 350px;"
                                 :types-only="[2]"/>
            </div>
            <div style="margin-top: 10px">
              <button type="button" class="btn btn-primary-nb" style="margin-bottom: 10px"
                      @click="createlist(3)">
                Создать таблицу исполнения (по не подтверждённым)
              </button>
              <button type="button" class="btn btn-primary-nb" style="margin-bottom: 10px"
                      @click="createlist(1)">
                Создать лист по выбранному периоду
              </button>
            </div>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button @click="open = false" class="btn btn-primary-nb btn-blue-nb" type="button">
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </modal>
    </MountingPortal>
  </fragment>
</template>

<script>
import moment from "moment";

import Modal from "@/ui-cards/Modal";
import DateRange from "@/ui-cards/DateRange";
import ResearchesPicker from "@/ui-cards/ResearchesPicker";

export default {
  components: {ResearchesPicker, Modal, DateRange},
  name: 'ExecutionList',
  data() {
    return {
      open: false,
      date_range: [moment().format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
      selected_researches: [],
    };
  },
  methods: {
    doOpen() {
      this.open = true;
      this.selected_researches = [];
      this.date_range = [moment().format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')];
    },
    createlist(type) {
      let [datestart, dateend] = this.date_range;
      if (this.selected_researches.length === 0) {
        $.amaran({
          'theme': 'awesome wrn',
          'content': {
            title: 'Создание невозможно',
            message: 'Ничего не выбрано',
            info: '',
            icon: 'fa fa-exclamation'
          },
          'position': 'bottom right',
          delay: 6000
        })
        return
      }
      switch (type) {
        case 3:
          window.open(`/mainmenu/receive/execlist?type=nonconfirmed&datestart=${datestart}&dateend=${dateend}&researches=${JSON.stringify(this.selected_researches)}`, '_blank')
          break
        default:
          window.open(`/directions/execlist?type=${type}&datestart=${datestart}&dateend=${dateend}&researches=${JSON.stringify(this.selected_researches)}`, '_blank')
          break
      }
    },
  },
}
</script>
