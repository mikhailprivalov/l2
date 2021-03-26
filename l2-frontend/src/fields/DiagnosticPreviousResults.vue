<template>
  <div>
    <table class="table table-bordered table-condensed" style="table-layout: fixed" v-for="(val, index) in tb_data">
      <colgroup>
        <col width='50%'/>
        <col width='20%'/>
        <col />
        <col width='36'/>
      </colgroup>
      <tbody>
      <tr>
        <td class="cl-td"><input type="text" class="form-control" :readonly="disabled" placeholder="Услуга" v-model="val.researchTitle"></td>
        <td class="cl-td"><input type="text" class="form-control" :readonly="disabled" placeholder="Дата" v-model="val.date"></td>
        <td class="cl-td"><input type="text" class="form-control" :readonly="disabled" placeholder="Врач" v-model="val.docConfirm"></td>
        <td class="cl-td">
          <button class="btn btn-blue-nb" @click="delete_row(index)" :disabled="disabled"
                  v-tippy="{ placement : 'bottom'}"
                  title="Удалить строку">
            <i class="fa fa-times"/>
          </button>
        </td>
      </tr>
      <tr>
        <td colspan="4" class="cl-td">
          <textarea rows="3" name="text" class="form-control" :readonly="disabled" placeholder="Описание"
           v-model="val.value"></textarea></td>
      </tr>
      </tbody>
    </table>
    <button class="btn btn-blue-nb add-row" @click="add_new_row" :disabled="disabled">
      Добавить
    </button>
  </div>

</template>

<script>
import api from "@/api";

const makeDefaultRow = () => ({researchTitle: "", date: "", docConfirm: "", value: ""});

export default {
name: "DiagnosticPreviousResults",
   props: {
    value: {
      required: false,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    }
  },
  data() {
    return {
      result: [],
      tb_data: [],
    }
  },
  mounted() {
    this.$root.$on('protocol:paraclinicResult', (direction) => {
      this.insertParaclinicResult(direction)
    })
  },
  methods: {
    add_new_row() {
      this.tb_data.push(makeDefaultRow());
    },
    delete_row(index) {
      this.tb_data.splice(index, 1);
    },
    delete_rows() {
      this.tb_data = []
    },
    changeValue(newVal) {
      this.$emit('modified', newVal)
    },
    async insertParaclinicResult(direction) {
      const result_data = await api('directions/result-patient-by-direction',
        {'isLab': false, 'isDocReferral': false, 'isParaclinic': true, 'dir': direction});
      this.result = result_data.results[0] || {};

      for (let r of Object.values(this.result.researches)) {
          this.tb_data.push({
            "researchTitle": r.title,
            "date": r.dateConfirm,
            "docConfirm": r.fio,
          })
      }
    }
  },
  watch: {
    tb_data: {
      handler() {
        this.changeValue(JSON.stringify(this.tb_data))
      },
      immediate: true,
    },
  },
  model: {
    event: `modified`
  },
}

</script>

<style scoped>

</style>
