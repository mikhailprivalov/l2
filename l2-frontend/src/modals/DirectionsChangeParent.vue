<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="40%" min-width="40%" width="100%" marginLeftRight="auto" margin-top>
    <span slot="header">Изменить родителя</span>
    <div slot="body" style="min-height: 200px" class="container">
      <div class="box-1">
        <h6><strong>Подчиненные направления:</strong></h6>
          <li v-for="dir in dir_pks">
            {{dir}}
          </li>
      </div>
      <div class="box-2">
        <h6><strong>Главное направление:</strong></h6>
        <v-select :clearable="false" v-model="selectStationarDir" label="label" :options="types_options" :searchable="true" placeholder="Выберите группу"/>
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

  export default {
    name: "DirectionsChangeParent",
    components: {Modal, vSelect},
    props: {
      dir_pks: {
        type: Array,
        required: true
      }
    },
    data() {
      return {
        parent_dir: "",
        types_options: [{label: "2121", value: "23"}, {label: "21", value: "2"}, {label: "2121", value: "23"}, {label: "21", value: "2"},
        {label: "2121", value: "23"}, {label: "21", value: "2"}, {label: "2121", value: "23"}, {label: "21", value: "2"},
          {label: "2121", value: "23"}, {label: "21", value: "2"}],
        selectStationarDir: "",
      }
    },
    mounted() {
      this.selectStationarDir = this.types_options[1]
    },
    methods: {
      hide_modal() {
        console.log(this.dir_pks)
        this.$root.$emit('hide_pe');
        if (this.$refs.modal) {
          this.$refs.modal.$el.style.display = 'none'
        }
      },
      async updateParent() {
        this.$store.dispatch(action_types.INC_LOADING).then();
        const ok = True;
        if (ok) {
          okmessage('Группа сохранён', `${"111"}`)
        } else {
          errmessage('Ошибка', message)
        }
        this.$store.dispatch(action_types.DEC_LOADING).then();
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
