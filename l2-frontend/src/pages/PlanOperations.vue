<template>
  <div>
    <h3>{{title}}</h3>
    <table class="table table-bordered">
      <colgroup>
        <col width='30'/>
        <col width='70'/>
        <col width='100'/>
        <col width='170'/>
        <col width='100'/>
        <col width='100'/>
        <col width='100'/>
      </colgroup>
      <thead>
      <tr>
        <th>Дата</th>
        <th>№ истории</th>
        <th>ФИО пациента</th>
        <th>Вид операции</th>
        <th>Врач-хирург</th>
        <th>Отделение</th>
        <th>Анестезиолог</th>
      </tr>
      </thead>
      <tbody>
<!--      <tr v-for="(val, index) in tb_data">-->
<!--        <td class="cl-td">-->
<!--          <div class="input-group">-->
<!--            <div class="input-group-btn">-->
<!--              <button type="button" class="btn btn-blue-nb nbr" @click="up_row(index)"-->
<!--                      :disabled="is_first_in_template(index)">-->
<!--                <i class="glyphicon glyphicon-arrow-up"></i>-->
<!--              </button>-->
<!--              <button type="button" class="btn btn-blue-nb" @click="down_row(index)"-->
<!--                      :disabled="is_last_in_template(index)">-->
<!--                <i class="glyphicon glyphicon-arrow-down"></i>-->
<!--              </button>-->
<!--            </div>-->
<!--            <input type="text" class="form-control nbr" v-model="val.title" placeholder="Введите наименование">-->
<!--          </div>-->
<!--        <td class="cl-td">-->
<!--          <select class="form-control nbr" v-model="val.type">-->
<!--            <option :value="t" v-for="t in types">{{t}}</option>-->
<!--          </select>-->
<!--        </td>-->
<!--        <td class="text-center cl-td">-->
<!--          <label>-->
<!--            <input type="checkbox" v-model="val.default">-->
<!--          </label>-->
<!--        </td>-->
<!--        <td class="text-center cl-td">-->
<!--          <button class="btn btn-blue-nb" @click="delete_row(index)" v-tippy="{ placement : 'bottom'}"-->
<!--                  title="Удалить строку">-->
<!--            <i class="fa fa-times"/>-->
<!--          </button>-->
<!--        </td>-->
<!--      </tr>-->
      </tbody>
    </table>
    <button class="btn btn-blue-nb add-row" @click="add_data">
      Добавить
    </button>
  </div>

</template>

<script>
  export default {
    name: "PlanOperations",
    data() {
      return {
        title: 'План операций',
      }
    },
    methods:{
      add_data() {
        return ''
      }
    }
  }
</script>

<style scoped>
  .content-edit {
    height: 330px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    position: relative;
    border-radius: 4px;
    padding: 5px;
  }

</style>
