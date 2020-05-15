<template>
  <div style="height: 100%;width: 100%;position: relative;min-height: 100px;">
    <div class="input-select">
      <v-select :clearable="false" label="title" :options="bacteriesGroups" :searchable="true"
                class="inner-select"
                placeholder="Выберите группу"
                v-model="selectedGroup"
      />
      <v-select :clearable="false" label="title" :options="bacteries" :searchable="true"
                class="inner-select"
                placeholder="Выберите микроорганизм"
                v-model="selectedBactery"
      />
      <button class="btn btn-blue-nb" @click="addBactery">
        Добавить
      </button>
    </div>
    <div v-for="bactery in bacteriesResult" class="bactery">
      <div class="bactery-title">
        <span title="Удалить" class="bactery-delete" @click="deleteBac(bactery.bacteryPk)" v-tippy>
          <i class="fa fa-times"></i>
        </span>
        <span class="bactery-title-inner">
          {{bactery.bacteryGroupTitle}} {{bactery.bacteryTitle}}
        </span>
      </div>
      <div class="bactery-body">
        <div class="input-select">
          <v-select :clearable="false" label="title" :options="antibiotics.groups" :searchable="true"
                    class="inner-select"
                    placeholder="Выберите группу"
                    v-model="bactery.selectedGroup"
                    @input="updateSelectedAntibiotic(bactery)"
          />
          <v-select :clearable="false" label="title" :options="antibiotics.groupsObj[bactery.selectedGroup.pk]"
                    :searchable="true"
                    class="inner-select"
                    placeholder="Выберите антибиотик"
                    v-model="bactery.selectedAntibiotic"
          />
          <button class="btn btn-blue-nb" @click="loadAntibiotic(bactery)">
            Добавить
          </button>
        </div>
        <hr />
        <div class="input-select">
          <v-select :clearable="false" label="title" :options="antibiotics.sets" :searchable="true"
                    class="inner-select"
                    placeholder="Выберите набор"
                    v-model="bactery.selectedSet"
          />
          <button class="btn btn-blue-nb" @click="loadSet(bactery)">
            Загрузить набор
          </button>
        </div>

        <table class="table table-bordered table-condensed" style="max-width: 665px;margin-top: 15px">
          <colgroup>
            <col style="width: 34px" />
            <col />
            <col style="width: 148px"  />
            <col style="width: 148px" />
          </colgroup>
          <thead>
          <tr>
            <th colspan="2">Название</th>
            <th>Чувствительность</th>
            <th>Диаметр</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="a in bactery.antibiotics">
            <td class="cl-td">
              <button title="Удалить" class="btn last btn-blue-nb nbr" type="button" v-tippy>
                <i class="fa fa-times"></i>
              </button>
            </td>
            <td>
              {{antibiotics.antibiotics[a.pk]}}
            </td>
            <td class="cl-td">
              <radio-field v-model="a.sri" :variants="sri" />
            </td>
            <td class="cl-td">
              <input v-model="a.dia" class="form-control" />
            </td>
          </tr>
          <tr v-if="bactery.antibiotics.length === 0">
            <td colspan="4" class="text-center">
              антибиотики не выбраны
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
  import vSelect from 'vue-select'
  import bacteria_point from '../api/bacteria-point'
  import * as action_types from '../store/action-types'
  import RadioField from "../fields/RadioField";

  const getDefaultElement = () => ({
    pk: -1,
    title: '',
  })

  export default {
    name: 'BacMicroForm',
    components: {RadioField, vSelect},
    props: {
      value: {
        type: Array,
        default: () => [],
        required: false,
      },
      confirmed: {
        type: Boolean,
        default: false,
      }
    },
    data() {
      return {
        sri: ['S', 'R', 'I'],
        val: [...this.value],
        bacteriesGroups: [],
        bacteries: [],
        selectedGroup: getDefaultElement(),
        selectedBactery: getDefaultElement(),
        bacteriesResult: [],
        antibiotics: {
          groups: [],
          groupsObj: {},
          antibiotics: {},
          sets: [],
        }
      }
    },
    async mounted() {
      await this.$store.dispatch(action_types.INC_LOADING)
      this.bacteriesGroups = (await bacteria_point.getBacGroups()).groups
      this.antibiotics = await bacteria_point.getAntibioticGroups()
      this.selectedGroup = this.bacteriesGroups[0] || getDefaultElement()
      await this.$store.dispatch(action_types.DEC_LOADING)
    },
    methods: {
      async load_bac_by_group() {
        await this.$store.dispatch(action_types.INC_LOADING)
        this.bacteries = (await bacteria_point.getBacByGroup({groupId: this.selectedGroup.pk})).list
        this.selectedBactery = this.bacteries[0] || getDefaultElement()
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      addBactery() {
        for (const bactery of this.bacteriesResult) {
          if (bactery.bacteryPk === this.selectedBactery.pk) {
            return;
          }
        }
        this.bacteriesResult.push({
          bacteryPk: this.selectedBactery.pk,
          bacteryTitle: this.selectedBactery.title,
          bacteryGroupTitle: this.selectedGroup.title,
          selectedGroup: this.antibiotics.groups[0],
          selectedAntibiotic: this.antibiotics.groupsObj[this.antibiotics.groups[0].pk][0],
          selectedSet: this.antibiotics.sets[0],
          antibiotics: [],
        })
      },
      async deleteBac(pk) {
        try {
          await this.$dialog.confirm('Подтвердите удаление')
        } catch (_) {
          return
        }

        this.bacteriesResult = this.bacteriesResult.filter(br => br.bacteryPk !== pk);
      },
      loadSet(bactery) {
        for (const id of bactery.selectedSet.ids) {
          this.addAntibiotic(bactery, id)
        }
      },
      loadAntibiotic(bactery) {
        this.addAntibiotic(bactery, bactery.selectedAntibiotic.pk)
      },
      addAntibiotic(bactery, pk) {
        for (const a of bactery.antibiotics) {
          if (a.pk === pk) {
            return
          }
        }

        bactery.antibiotics.push({
          pk,
          sri: 'S',
          dia: '',
        })
      },
      updateSelectedAntibiotic(bactery) {
        bactery.selectedAntibiotic = this.antibiotics.groupsObj[bactery.selectedGroup.pk][0]
      },
    },
    watch: {
      val: {
        deep: true,
        handler() {
          this.$emit('input', this.val)
        },
      },
      selectedGroup: {
        deep: true,
        handler() {
          this.load_bac_by_group()
        },
      },
    },
  }
</script>

<style scoped lang="scss">
  .inner-select, .input-select .btn {
    display: inline-block;
    max-width: 330px;
    width: 30%;
    vertical-align: middle;
    height: 32px;
  }

  .inner-select {
    background: #fff!important;
  }

  .bactery {
    margin: 10px 0;
    border: 1px solid #049372;
    border-radius: 5px;
    overflow: visible;

    &-title {
      color: #fff;
      background: #049372;
      line-height: 20px;
      border-radius: 4px 4px 0 0;
      overflow: hidden;

      span {
        display: inline-block;
      }
    }

    &-delete {
      padding: 0 4px;
      cursor: pointer;

      &:hover {
        background: #03614b;
      }
    }
  }

  .bactery-body {
    padding: 5px;

    hr {
      margin: 5px 0;
    }
  }
</style>
