<template>
  <div v-frag>
    <div class="input-group">
      <input type="number" class="form-control" @keypress.enter="save" v-model="grade"      placeholder="Оценка"      style="width: 15%;" min="0"/>
      <input type="text"   class="form-control" @keypress.enter="save" v-model="comment"    placeholder="Комментарий" style="width: 85%;"/>
      <span class="input-group-btn">
        <button class="btn btn-blue-nb" title="Сохранить" @click="save(false)" v-tippy v-if="!loading">
          <i class="fas fa-save"></i>
        </button>
        <button class="btn btn-blue-nb" title="Отмена" @click="close()" v-tippy v-if="data.editing">
         <i class="fas fa-close">×</i>
        </button>
      </span>
    </div>
  </div>
</template>

<script lang="ts">
import Vue, { PropType } from 'vue';
import Component from 'vue-class-component';
import { EvaluationMonitoringGroup } from '@/types/evaluationMonitoring';
import * as actions from '@/store/action-types';

@Component({
  props: {
    data: {
      type: Object as PropType<EvaluationMonitoringGroup>,
      required: true,
    },
    canEdit: {
      type: Boolean,
    },
  },
  data() {
    return {
      grade: '',
      comment: '',
      loading: false,
    };
  },
  watch: {
    value: {
      immediate: true,
      handler() {
        this.grade = this.data.grade.grade;
        this.comment = this.data.grade.comment;
      },
    },
  },
})
export default class ExtraNotificationFastEditor extends Vue {
  canEdit: boolean;

  data: EvaluationMonitoringGroup;

  grade: number;

  comment: string;

  loading: boolean;

  $dialog: any;

  get value() {
    return 123;
  }

  get editing() {
    return true;
  }

  get valid() {
    return true;
  }

  async save(withConfirm = false) {
    if(!/^(\d+|\d+\.\d+|\d+\,\d+)$/.test(String(this.grade))) {
      this.$root.$emit('msg', 'error', 'Введите положительное число или ноль в поле оценки');
      return;
    }

    this.loading = true;
    await this.$store.dispatch(actions.INC_LOADING);

    const {
      ok, message, value,
    } = await this.$api('evaluation_monitoring/add_result', {
          result_id: this.data.fields[0].result_id,
          grade: this.grade,
          comment: this.comment,
    });
    this.$emit('sendData', this.data);
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loading = false;
    if(ok) {
      this.$root.$emit('msg', 'ok', message);
    } else {
      this.$root.$emit('msg', 'error', message);
    }  
  }

  close() {
    this.$emit('cancelEdit');
  }
}
</script>

<style lang="scss" scoped>
.inner-text {
  padding: 5px;
}

.form-control,
.btn {
  padding: 2px 12px;
  height: 30px;
}

.btn-2icons {
  .fas {
    display: inline-block;
    margin: 0 -5px;
    position: relative;

    &:first-child {
      opacity: 0.85;
      transform: scale(0.9);
    }

    &:last-child {
      filter: drop-shadow(0 0 1px #9da6b1);
    }
  }
}
</style>
