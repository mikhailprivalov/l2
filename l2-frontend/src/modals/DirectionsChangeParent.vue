<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="50%" min-width="800px" width="50%"
         marginLeftRight="auto" margin-top="48px">
    <span slot="header">Изменить родителя</span>
    <div slot="body" style="min-height: 340px">
      <h6><strong>Пациент: </strong>{{patientFio}}</h6>
      <div class="row" id="row-box">
        <div class="col-xs-6">
          <h6><strong>Изменить принадлежность:</strong></h6>
          <ul>
            <li v-for="dir in directions_checked" :key="dir.pk">
              <div v-if="dir.has_hosp" class="invalid" v-tippy="{ placement : 'bottom'}"
                 title="История болезни не может подчиняться">
                <span style="text-decoration: line-through;"><strong>{{dir.pk}}</strong>- {{dir.researches}}</span>
              </div>
              <div v-else-if="dir.parent.parent_is_hosp || dir.parent.parent_is_doc_refferal">
                <i class="fa fa-exclamation-triangle fa-lg" style="color: #d35400"></i><strong>{{dir.pk}}</strong> -
                {{dir.researches}}
                <!-- eslint-disable-next-line max-len -->
                <a :href="`/mainmenu/stationar#{%22pk%22:${dir.parent.pk},%22opened_list_key%22:null,%22opened_form_pk%22:null,%22every%22:false}`"
                  v-if="dir.parent.parent_is_hosp" class="invalid" target="_blank">
                  (Принадлежит И/Б № {{dir.parent.pk}} - {{dir.parent.parent_title}})
                </a>
                <a @click="dir.parent.is_confirm ? show_results(dir.parent) : null"
                   v-if="dir.parent.parent_is_doc_refferal"
                   target="_blank">
                  <!-- eslint-disable-next-line max-len -->
                  <span :class="[{invalid: dir.parent.is_confirm}, {isDisabled: !dir.parent.is_confirm}]"> (Создано в амбулаторном приеме: {{dir.parent.pk}} - {{dir.parent.parent_title}})</span>
                </a>
              </div>
              <div v-else><strong>{{dir.pk}}</strong> - {{dir.researches}}</div>
            </li>
          </ul>
        </div>
        <div class="col-xs-6" id="box-right">
          <h6><strong>Главное направление:</strong></h6>
          <v-select :clearable="false" v-model="selectStationarDir" label="label" :options="dirs_options"
                    :searchable="true" placeholder="Выберите историю болезни"/>
        </div>
      </div>
    </div>

    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button type="button" @click="updateParent" class="btn btn-primary-nb btn-blue-nb">
            Сохранить
          </button>
        </div>
        <div class="col-xs-4">
          <button type="button" @click="hide_modal" class="btn btn-primary-nb btn-blue-nb">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
import vSelect from 'vue-select';
import Modal from '../ui-cards/Modal.vue';
import * as actions from '../store/action-types';
import 'vue-select/dist/vue-select.css';
import patientsPoint from '../api/patients-point';
import directionsPoint from '../api/directions-point';

export default {
  name: 'DirectionsChangeParent',
  components: { Modal, vSelect },
  props: {
    directions_checked: {
      type: Array,
      required: true,
    },
    card_pk: {
      type: Number,
      default: -1,
      required: false,
    },
    kk: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      parent_dir: '',
      dirs_options: [],
      selectStationarDir: [],
      card: '',
      patientFio: '',
      slave_dirs: [],
    };
  },
  mounted() {
    this.load_data();
  },
  methods: {
    show_results(row) {
      if (row.has_descriptive) {
        this.$root.$emit('print:results', [row.pk]);
      } else {
        this.$root.$emit('show_results', row.pk);
      }
    },
    hide_modal() {
      this.$root.$emit('hide_pe');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.searchL2Card(this, 'card_pk').then(({ results: [data] }) => {
        this.patientFio = `${data.family} ${data.name} ${data.twoname}`;
      });
      await directionsPoint.getHospSetParent({ patient: this.card_pk }).then(({ directions }) => {
        this.dirs_options = [];
        for (const direction of directions) {
          const label = `${direction.dir_num}: ${direction.researche_titles} (от ${direction.date})`;
          this.dirs_options.push({ label, value: direction.iss_id });
        }
        this.dirs_options.push({ label: '0: Сбросить подчинение', value: -1 });
      });
      this.slave_dirs = [];
      for (const dir of this.directions_checked) {
        this.slave_dirs.push(dir.pk);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async updateParent() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await directionsPoint.updateParent({
        parent: this.selectStationarDir.value,
        slave_dirs: this.slave_dirs,
      });
      if (ok) {
        window.okmessage('Cохранено');
        this.hide_modal();
      } else {
        window.errmessage('Ошибка', message);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit(`researches-picker:refresh${this.kk}`);
    },
  },
};
</script>

<style scoped lang="scss">
  .invalid {
    color: #d35400;
    cursor: pointer;
  }

  .isDisabled {
    cursor: not-allowed;
    opacity: 0.7;
    color: #d35400;
  }

  #row-box {
    display: flex;
  }

  #box-right {
    border-left: 1px solid silver;
  }

  ul {
    font-size: 13px;
    padding: 0;
  }

  li {
    list-style-type: none;
    padding: 5px;
  }

</style>
