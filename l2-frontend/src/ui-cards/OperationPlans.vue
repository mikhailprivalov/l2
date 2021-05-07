<template>
  <div v-frag>
    <a href="#" class="dropdown-toggle" @click.prevent
       v-tippy="{
                html: '#operations-view',
                reactive: true,
                interactive: true,
                arrow: true,
                animation: 'fade',
                duration: 0,
                theme: 'light',
                placement: 'bottom',
                trigger: 'click mouseenter',
                zIndex: 4999,
                popperOptions: {
                  modifiers: {
                    preventOverflow: {
                      boundariesElement: 'window'
                    },
                    hide: {
                      enabled: false
                    }
                  }
                },
             }">
      План операций пациента <span class="badge badge-light">{{data.length}}</span>
    </a>

    <div id="operations-view" class="tp">
      <table class="table table-condensed table-bordered">
        <thead>
        <tr>
          <th>История</th>
          <th>Дата</th>
          <th>Врач-хирург</th>
          <th>Операция</th>
          <th></th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="row in data" :class="{'cancel-row': row.cancel}" :key="row.pk_plan">
          <td>
            <LinkPlanOperations :direction="row.direction"/>
          </td>
          <td>
            {{row.date}}
          </td>
          <td>
            {{row.hirurg}}
          </td>
          <td>
            {{row.type_operation}}
          </td>
          <td>
            <a href="#" @click.prevent="edit_data(row)" v-if="can_edit_operations"><i class="fa fa-pencil"></i></a>
          </td>
        </tr>
        </tbody>
      </table>
      <br/>
      <a href="#" style="float: right" @click.prevent="add_data" v-if="can_edit_operations">Добавить</a>
    </div>
    <plan-operation-edit v-if="edit_plan_operations_old || edit_plan_operations" :card_pk="card_pk"
                         :patient_fio="patient_fio"
                         :direction="current_direction" :pk_plan="pk_plan" :pk_hirurg="pk_hirurg" :date="date"
                         :operation="operation"
                         :cancel_operation="cancel"
    />
  </div>
</template>

<script>
import plansPoint from '../api/plans-point';
import LinkPlanOperations from '../pages/Stationar/LinkPlanOperations.vue';

export default {
  name: 'OperationPlans',
  components: { LinkPlanOperations, PlanOperationEdit: () => import('@/modals/PlanOperationEdit') },
  data() {
    return {
      data: [],
      edit_plan_operations: false,
      edit_plan_operations_old: false,
      patient_fio: '',
      card_pk: null,
      current_direction: '',
      current_direction_history_open: '',
      pk_plan: null,
      pk_hirurg: null,
      date: null,
      operation: '',
      cancel: false,
    };
  },
  mounted() {
    this.$root.$on('hide_plan_operations', () => {
      this.edit_plan_operations = false;
      this.edit_plan_operations_old = false;
      this.load();
    });
    this.$root.$on('current_history_direction', (data) => {
      this.current_direction_history_open = data.history_num;
      this.card_pk = data.patient.card_pk;
      // eslint-disable-next-line prefer-destructuring
      this.patient_fio = data.patient.fio_age.split('+')[0];
      this.load();
    });
  },
  methods: {
    async load() {
      const { data } = await plansPoint.getPlanOperastionsPatient({ card_pk: this.card_pk });
      this.data = data;
    },
    add_data() {
      this.edit_plan_operations = true;
      this.pk_plan = -1;
      this.date = '';
      this.operation = '';
      this.current_direction = this.current_direction_history_open.toString();
    },
    edit_data(row) {
      this.pk_hirurg = row.hirurg_pk;
      const date_array = row.date.split('.');
      this.date = `${date_array[2]}-${date_array[1]}-${date_array[0]}`;
      this.current_direction = row.direction.toString();
      this.operation = row.type_operation;
      this.pk_plan = row.pk_plan;
      this.cancel = row.cancel;
      this.edit_plan_operations_old = true;
    },
  },
  computed: {
    can_edit_operations() {
      return (this.$store.getters.user_data.groups || []).includes('Управление планами операций');
    },
  },
};
</script>

<style scoped lang="scss">
  .cancel-row {
    td, th {
      opacity: .6;
      text-decoration: line-through;
    }

    &:hover {
      td, th {
        opacity: 1;
        text-decoration: none;
      }
    }
  }

  .size-btn {
    width: 50px;
  }

  .fv {
    cursor: pointer;

    &:hover span {
      text-shadow: 0 0 3px rgba(#049372, .4);
      color: #049372;
    }
  }

  i {
    vertical-align: middle;
    display: inline-block;
    margin-right: 3px;
  }

  .inFavorite i {
    color: #93046d;
  }

  .tp {
    text-align: left;
    line-height: 1.1;
    padding: 5px;

    table {
      margin: 0;
    }

    max-height: 600px;
    overflow-y: auto;
  }
</style>
