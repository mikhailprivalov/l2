<template>
  <fragment>
    <div class="root" ref="root" v-if="pk" :key="pk">
      <table class="table table-bordered table-sm-pd">
        <thead>
        <tr>
          <td colspan="4" class="cl-td">
            <button class="btn btn-blue-nb header-button" @click="clearAll" :disabled="confirmed">
              Очистить всё
            </button>
            <div style="padding: 5px;font-weight: bold;">
              {{ research.title }}
            </div>
          </td>
        </tr>
        <tr class="table-header">
          <th style="width: 29%">Фракция</th>
          <th :colspan="noRefs ? 3 : 1">Значение</th>
          <th style="width: 23%" v-if="!noRefs">Нормы М</th>
          <th style="width: 23%" v-if="!noRefs">Нормы Ж</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="r in result">
          <td>
            <label class="fraction-title" :for="`fraction-${r.fraction.pk}`">{{ r.fraction.title }}</label>
          </td>
          <BloodTypeField
            v-if="research.template === 2"
            :readonly="confirmed || !loaded"
            :r="r"
          />
          <TextInputField
            v-else
            :readonly="confirmed || !loaded"
            :move-focus-next="moveFocusNext"
            :r="r"
            :allDirPks="allDirPks"
            :dirData="dirData"
          />
          <Ref :data="r.ref.m" v-if="!noRefs"/>
          <Ref :data="r.ref.f" v-if="!noRefs"/>
        </tr>
        <tr v-if="research.can_comment">
          <td><label class="fraction-title" for="result_comment">Комментарий</label></td>
          <td colspan="3">
            <textarea class="noresize form-control result-field"
                      :readonly="confirmed || !loaded"
                      v-autosize="comment" v-model="comment" id="result_comment"></textarea>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
    <div class="bottom-buttons">
      <template v-if="loaded">
        <template v-if="!confirmed">
          <button class="btn btn-blue-nb btn-right" @click="saveAndConfirm()">
            Сохранить и подтвердить
          </button>
          <button class="btn btn-blue-nb btn-right" :disabled="!saved" @click="confirm()">
            Подтвердить
          </button>
          <button class="btn btn-blue-nb btn-right" @click="save()">
            Сохранить
          </button>
        </template>
        <template v-else>
          <button class="btn btn-blue-nb btn-right" :disabled="!allow_reset_confirm" @click="resetConfirm()">
            Сброс подтверждения
          </button>
        </template>
      </template>
    </div>
  </fragment>
</template>
<script>
import * as action_types from "@/store/action-types";
import api from "@/api";

import Ref from "@/pages/LaboratoryResults/Ref";
import TextInputField from "@/pages/LaboratoryResults/TextInputField";
import BloodTypeField from "@/pages/LaboratoryResults/BloodTypeField";

export default {
  name: 'ResultsForm',
  components: {TextInputField, BloodTypeField, Ref},
  mounted() {
    this.$root.$on('laboratory:results:open-form', (pk, allDirPks, dirData) => {
      this.loadForm(pk);
      this.allDirPks = allDirPks;
      this.dirData = dirData;
    });
  },
  data() {
    return {
      loaded: false,
      confirmed: false,
      saved: false,
      allow_reset_confirm: false,
      pk: null,
      research: {},
      comment: '',
      result: [],
      allDirPks: [],
      dirData: {},
    };
  },
  computed: {
    noRefs() {
      return this.research.no_units_and_ref || this.research.template === 2;
    },
  },
  methods: {
    async loadForm(pk) {
      this.loaded = false;
      if (pk === -1) {
        this.pk = null;
        this.research = {};
        this.comment = '';
        this.result = [];
        this.confirmed = false;
        this.saved = false;
        this.allow_reset_confirm = false;
        return;
      }
      await this.$store.dispatch(action_types.INC_LOADING);
      const {data} = await api('laboratory/form', {pk});
      this.pk = data.pk;
      this.research = data.research;
      this.comment = data.comment;
      this.result = data.result;
      this.confirmed = data.confirmed;
      this.saved = data.saved;
      this.allow_reset_confirm = data.allow_reset_confirm;
      this.loaded = true;
      $(this.$refs.root).scrollTop(0);
      if (!data.confirmed) {
        setTimeout(() => {
          const $rf = $('.result-field:not([readonly]):not([disabled])');
          if ($rf.length) {
            const idx = data.result.findIndex(r => !Boolean(r.value));
            if (idx !== -1) {
              $rf.eq(idx).focus();
            }
          }
        }, 0);
      }
      await this.$store.dispatch(action_types.DEC_LOADING);
    },
    async clearAll() {
      try {
        await this.$dialog.confirm('Вы действительно очистить все значения?')
      } catch (_) {
        return
      }
      for (const i of this.result) {
        i.value = '';
      }
    },
    async save(withoutReloading = false) {
      await this.$store.dispatch(action_types.INC_LOADING);
      const {ok, message} = await api('laboratory/save', this, ['pk', 'result', 'comment']);
      if (!ok) {
        errmessage(message);
      } else {
        okmessage('Сохранено');
      }
      if (!withoutReloading) {
        this.$root.$emit('laboratory:reload-direction:with-open-first');
      }
      await this.$store.dispatch(action_types.DEC_LOADING);
      return ok;
    },
    async confirm() {
      await this.$store.dispatch(action_types.INC_LOADING);
      const {ok, message} = await api('laboratory/confirm', this, 'pk');
      if (!ok) {
        errmessage(message);
      } else {
        okmessage('Подтверждено');
      }
      this.$root.$emit('laboratory:reload-direction:with-open-first');
      await this.$store.dispatch(action_types.DEC_LOADING);
      return ok;
    },
    async saveAndConfirm() {
      const saveResult = await this.save(true);
      if (!saveResult) {
        return;
      }

      await this.confirm();
    },
    async resetConfirm() {
      try {
        await this.$dialog.confirm('Подтвердите сброс')
      } catch (_) {
        return
      }
      await this.$store.dispatch(action_types.INC_LOADING);
      const {ok, message} = await api('laboratory/reset-confirm', this, 'pk');
      if (!ok) {
        errmessage(message);
      } else {
        okmessage('Подтверждение сброшено');
      }
      this.$root.$emit('laboratory:reload-direction:with-open-pk', this.pk);
      await this.$store.dispatch(action_types.DEC_LOADING);
    },
    moveFocusNext(e) {
      const $rf = $('.result-field:not([readonly]):not([disabled])');
      const index = $rf.index(e.target) + 1;
      if ($rf.eq(index).length) {
        $rf.eq(index).focus();
      } else {
        this.save();
      }
    }
  },
}
</script>

<style scoped lang="scss">
.root {
  position: absolute;
  top: 0 !important;
  right: 0;
  left: 0;
  bottom: 34px !important;
  overflow-x: visible;
  overflow-y: auto;
}

.fraction-title {
  font-weight: normal;
  font-size: 14px;
  display: block;
  min-height: 100%;
  height: 100%;
  margin: 0;
  cursor: pointer !important;
}

.header-button {
  width: 100%;
  max-width: 150px;
  float: right;
}

.table-header th {
  padding: 2px 2px 2px 8px;
  position: sticky;
  top: -1px;
  background-color: white;
  z-index: 2;
  box-shadow: 2px 0 2px rgba(0, 0, 0, .1);
}
</style>
