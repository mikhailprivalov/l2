<template>
  <div style="height: 100%;width: 100%;position: relative;min-height: 100px;">
    <div class="input-select flex-select">
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
        <div class="bactery-selects">
          <div class="row">
            <div class="col-xs-6 two">
              <v-select :clearable="false" label="title" :options="antibiotics.sets" :searchable="true"
                        class="inner-select"
                        placeholder="Выберите набор"
                        v-model="bactery.selectedSet"
              />
              <button class="btn btn-blue-nb" @click="loadSet(bactery)">
                Загрузить набор
              </button>
            </div>
            <div class="col-xs-6 three">
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
          </div>
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
              <button title="Удалить" class="btn last btn-blue-nb nbr" type="button" v-tippy
                      @click="deleteAnti(bactery, a.pk)">
                <i class="fa fa-times"></i>
              </button>
            </td>
            <td>
              {{antibiotics.antibiotics[a.pk]}}
            </td>
            <td class="cl-td">
              <radio-field v-model="a.sri" :variants="sri" redesigned />
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
  import 'vue-select/dist/vue-select.css';
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
      deleteAnti(bactery, pk) {
        bactery.antibiotics = bactery.antibiotics.filter(a => a.pk !== pk)
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
  .flex-select {
    padding-left: 11px;
    width: 670px;
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    align-content: stretch;
    align-items: stretch;
    .inner-select, .input-select .btn {
      align-self: stretch;
      flex: 1;
    }
    .inner-select {
      margin-right: 5px;
    }
  }

  .inner-select, .input-select .btn {
    display: inline-block;
    vertical-align: middle;
  }

  .inner-select, .input-select .btn {
    height: 32px;
  }

  .bactery-selects {
    position: sticky;
    top: 80px;
    background: #fff;
    padding-bottom: 5px;
    padding-top: 5px;
    border-bottom: solid 1px lightgray;
    z-index: 1;

    .row {
      max-width: 700px;
    }

    .two, .three {
      display: flex;
      flex-wrap: wrap;
      justify-content: stretch;
      align-content: stretch;
      align-items: stretch;
    }

    .two {
      padding-right: 5px;
      border-right: 1px solid lightgray;
    }

    .three {
      padding-left: 5px;
    }

    .inner-select, .btn {
      align-self: stretch;
      height: 32px;
      margin: 0 5px;
      max-width: 100%;
    }

    .inner-select {
      flex: 1;
    }

    .btn {
      flex: 0;
    }
  }

  .inner-select {
    background: #fff!important;
  }

  .bactery {
    margin: 10px 0;
    border: 1px solid #048493;
    border-radius: 5px;
    overflow: visible;

    &-title {
      z-index: 2;
      position: sticky;
      top: 60px;
      color: #fff;
      background: #048493;
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
        background: #0c7e8b;
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
