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
          {{bactery.bacteryGroupTitle}} – {{bactery.bacteryTitle}}
        </span>
      </div>
      <br/>
      <br/>
      <br/>
      <br/>
    </div>
  </div>
</template>

<script>
  import vSelect from 'vue-select'
  import bacteria_point from '../api/bacteria-point'
  import * as action_types from '../store/action-types'

  const getDefaultElement = () => ({
    pk: -1,
    title: '',
  })

  export default {
    name: 'BacMicroForm',
    components: {vSelect},
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
        val: [...this.value],
        bacteriesGroups: [],
        bacteries: [],
        selectedGroup: getDefaultElement(),
        selectedBactery: getDefaultElement(),
        bacteriesResult: [],
      }
    },
    async mounted() {
      await this.$store.dispatch(action_types.INC_LOADING)
      this.bacteriesGroups = (await bacteria_point.getBacGroups()).groups
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

  .bactery {
    margin: 10px 0;
    border: 1px solid #049372;
    background: linear-gradient(to bottom, #fff 0%, #fff 50%, #04937233 100%);
    border-radius: 5px;
    overflow: hidden;

    &-title {
      color: #fff;
      background: #049372;
      line-height: 20px;

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
</style>
