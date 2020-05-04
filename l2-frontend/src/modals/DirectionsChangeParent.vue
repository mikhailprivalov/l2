<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="50%" min-width="50%" width="100%" marginLeftRight="auto" margin-top>
    <span slot="header">Изменить родителя</span>
    <div slot="body" style="min-height: 240px" >
      <div class="container">
        <h6><strong>Пациент: </strong>{{patientFio}}</h6>
      </div>
      <div class="container">
        <div class="box-1">
          <h6><strong>Выбраны для подчинения:</strong></h6>
            <li v-for="dir in direction_checked">
              <p v-if="dir.has_hosp" style="color: #881c2f" v-tippy="{ placement : 'bottom'}" title="История болезни не может подчиняться">
                <strike> <strong>{{dir.pk}}</strong>- {{dir.researches}}</strike>
              </p>
              <p v-else><strong>{{dir.pk}}</strong> - {{dir.researches}}</p>
            </li>
        </div>

        <div class="box-2">
          <h6><strong>Главное направление:</strong></h6>
          <v-select :clearable="false" v-model="selectStationarDir" label="label" :options="dirs_options" :searchable="true" placeholder="Выберите историю болезни"/>
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
            Отмена
          </button>
        </div>
      </div>
    </div>
  </modal>

</template>

<script>
  import Modal from '../ui-cards/Modal'
  import * as action_types from "../store/action-types";
  import vSelect from 'vue-select'
  import patients_point from "../api/patients-point";
  import directions_point from "../api/directions-point";

  export default {
    name: "DirectionsChangeParent",
    components: {Modal, vSelect},
    props: {
      dir_pks: {
        type: Array,
        required: true
      },
      direction_checked:{
        type: Array,
        required: true
      },
      card_pk: {type: Number,
        default: -1,
        required: false,
      },
    },
    data() {
      return {
        parent_dir: "",
        dirs_options: [],
        selectStationarDir: [],
        card: "",
        patientFio: "",
        slave_dirs: []
      }
    },
    mounted() {
      this.load_data();
    },
    methods: {
      hide_modal() {
        this.$root.$emit('hide_pe');
        if (this.$refs.modal) {
          this.$refs.modal.$el.style.display = 'none'
        }
      },
      load_data(){
      patients_point.searchL2Card({card_pk: this.card_pk}).then((result) => {
        let data = result.results[0];
        this.patientFio = data.family + " " + data.name + " " + data.twoname
      });
      directions_point.getHospSetParent({"patient":this.card_pk}).then(data => {
        let directions = data.directions;
        this.dirs_options = [];
        for (let i of directions){
          let label = i.dir_num + ": " + i.researche_titles + " (от " + i.date + ")";
          this.dirs_options.push({"label": label , "value": i.iss_id})
        }
        this.dirs_options.push({"label": "0: Сбросить подчинение" , "value": -1})
      });
        this.slave_dirs = [];
        for (let dir of this.direction_checked) {
          if (!dir.has_hosp){
            this.slave_dirs.push(dir.pk)
          }
        }
    },
      async updateParent() {
        this.$store.dispatch(action_types.INC_LOADING).then();
        const {ok, message} = await directions_point.updateParent({'parent': this.selectStationarDir.value,
          'slave_dirs': this.slave_dirs });
        if (ok) {
          okmessage('Cохранено')
        } else {
          errmessage('Ошибка', message)
        }
        this.$store.dispatch(action_types.DEC_LOADING).then()
      },
    }
  }
</script>

<style scoped lang="scss">
  .container {
    width: 100%;
    height: 100%;
    display: flex;
  }

  .container div {
    margin: 3px;
  }

  .box-1{
    flex: 1
  }

  .box-2{
    flex: 1;
    border-left: 1px solid silver;
    padding-left: 20px;
  }

  li {
    list-style-type: none; /* Заглавные буквы */
    padding: 5px;
   }

</style>
