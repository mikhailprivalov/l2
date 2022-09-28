<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="50%"
    min-width="800px"
    width="50%"
    margin-left-right="auto"
    margin-top="48px"
    @close="hide_modal"
  >
    <span slot="header">Изменить родителя</span>
    <div
      slot="body"
      style="min-height: 340px"
    >
      <h6><strong>Пациент: </strong>{{ patientFio }}</h6>
      <div
        id="row-box"
        class="row"
      >
        <div class="col-xs-6">
          <h6><strong>Изменить принадлежность:</strong></h6>
          <ul>
            <li
              v-for="dir in directions_checked"
              :key="dir.pk"
            >
              <div
                v-if="dir.has_hosp"
                v-tippy="{ placement: 'bottom' }"
                class="invalid"
                title="История болезни не может подчиняться"
              >
                <span
                  style="text-decoration: line-through"
                ><strong>{{ dir.pk }}</strong>- {{ dir.researches }}</span>
              </div>
              <div v-else-if="dir.parent.parent_is_hosp || dir.parent.parent_is_doc_refferal">
                <i
                  class="fa fa-exclamation-triangle fa-lg"
                  style="color: #d35400"
                /><strong>{{ dir.pk }}</strong> -
                {{ dir.researches }}
                <a
                  v-if="dir.parent.parent_is_hosp"
                  :href="/*eslint-disable-line max-len*/ `/ui/stationar#{%22pk%22:${dir.parent.pk},%22opened_list_key%22:null,%22opened_form_pk%22:null,%22every%22:false}`"
                  class="invalid"
                  target="_blank"
                >
                  (Принадлежит И/Б № {{ dir.parent.pk }} - {{ dir.parent.parent_title }})
                </a>
                <a
                  v-if="dir.parent.parent_is_doc_refferal"
                  target="_blank"
                  @click="dir.parent.is_confirm ? show_results(dir.parent) : null"
                >
                  <span :class="[{ invalid: dir.parent.is_confirm }, { isDisabled: !dir.parent.is_confirm }]">
                    (Создано в амбулаторном приеме: {{ dir.parent.pk }} - {{ dir.parent.parent_title }})</span>
                </a>
              </div>
              <div v-else>
                <strong>{{ dir.pk }}</strong> - {{ dir.researches }}
              </div>
            </li>
          </ul>
        </div>
        <div
          id="box-right"
          class="col-xs-6"
        >
          <h6><strong>Главное направление:</strong></h6>
          <v-select
            v-model="selectStationarDir"
            :clearable="false"
            label="label"
            :options="dirs_options"
            :searchable="true"
            placeholder="Выберите историю болезни"
          />
        </div>
      </div>
    </div>

    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            @click="updateParent"
          >
            Сохранить
          </button>
        </div>
        <div class="col-xs-4">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            @click="hide_modal"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import vSelect from 'vue-select';

import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';
import 'vue-select/dist/vue-select.css';
import patientsPoint from '@/api/patients-point';
import directionsPoint from '@/api/directions-point';

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
        this.$root.$emit('msg', 'ok', 'Cохранено');
        this.hide_modal();
      } else {
        this.$root.$emit('msg', 'error', `Ошибка\n${message}`);
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
