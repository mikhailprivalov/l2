<template>
  <fragment>
    <a href="#" class="dropdown-toggle" @click.prevent
       v-tippy="{
                html: '#favorites-view',
                reactive: true,
                interactive: true,
                arrow: true,
                animation: 'fade',
                duration: 0,
                theme: 'light',
                placement: 'bottom',
                trigger: 'click mouseenter',
                show : !edit_plan_operations,
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
      План операций <span class="badge badge-light">{{data.length}}</span>
    </a>

    <div id="favorites-view" class="tp">
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
        <tr v-for="row in data">
          <td>
            <LinkPlanOperations :direction="row.direction" />
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
            <a href="#"><i class="fa fa-pencil"></i></a>
          </td>
        </tr>
        </tbody>
      </table>
      <br/>
      <a href="#" style="float: right"  @click.prevent="add_data">Добавить</a>
    </div>
    <plan-operation-edit v-if="edit_plan_operations" :card_pk="card_pk" :patient_fio="patient_fio"  :direction="current_direction" :pk_plan="pk_plan"/>
  </fragment>
</template>

<script>
  import directions_point from "../api/directions-point";
  import LinkPlanOperations from "../pages/Stationar/LinkPlanOperations";
  import PlanOperationEdit from '../modals/PlanOperationEdit'

  export default {
    name: "OperationPlans",
    components: {LinkPlanOperations, PlanOperationEdit},
    data() {
      return {
        data: [],
        edit_plan_operations: false,
        patient_fio: '',
        card_pk: '',
        current_direction: '',
        pk_plan: ''
      }
    },
    mounted() {
      this.$root.$on('hide_plan_operations', () => {
        this.edit_plan_operations = false
        this.load();
      });
      this.$root.$on('current_history_direction', (data) => {
        this.current_direction = data.history_num
        this.card_pk = data.patient.card_pk
        this.patient_fio = data.patient.fio_age.split('+')[0]
        this.load();
      });
    },

    methods: {
      async load() {
        const {data} = await directions_point.getPlanExaminationPatient({'card_pk': this.card_pk})
        this.data = data;
      },
      add_data() {
        this.edit_plan_operations = true
        this.pk_plan = -1
      }
    }
  }
</script>

<style scoped lang="scss">
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
