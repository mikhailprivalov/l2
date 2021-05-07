<template>
  <div class="root">
    <SelectedPatient :card="selected_card"/>
    <div class="flex-columns">
      <div class="fixed-column">
        <CardSearch v-model="selected_card"/>
        <div class="column-header-w-btn">
          <div class="column-header-inner">Случаи</div>

          <button class="btn last btn-hd nbr" type="button">
            <i class="fa fa-plus"></i>
          </button>
        </div>
      </div>
      <div class="fixed-column">
        <div class="input-group-f">
          <input type="text" class="form-control bob nbr" v-model="directionQ" placeholder="Направление"
                 maxlength="128">
          <button class="btn last btn-blue-nb nbr" type="button">
            <i class="fa fa-search"></i>
          </button>
        </div>
        <div class="two-columns">
          <div>
            <div class="column-header">
              Посещения
            </div>
          </div>
          <div>
            <div class="column-header">
              Исследования
            </div>
          </div>
        </div>
      </div>
      <div class="flex-column"></div>
    </div>
  </div>
</template>

<script>
import SelectedPatient from '../components/SelectedPatient.vue';
import CardSearch from '../components/CardSearch.vue';

export default {
  name: 'cases',
  components: { SelectedPatient, CardSearch },
  data() {
    return {
      directionQ: '',
      selected_card: {
        pk: -1,
        num: '',
        base: '',
        is_rmis: false,
        fio: '',
        sex: '',
        bd: '',
        age: '',
      },
    };
  },
};
</script>

<style lang="scss" scoped>
  .root {
    margin-left: -5px;
    margin-right: -5px;
    height: calc(100% - 36px);
  }

  .flex-columns {
    display: flex;
    height: calc(100% - 30px);
    & > div {
      height: 100%;
    }
  }

  .fixed-column {
    flex: 0 0 20%;
    border-right: 1px solid #aab2bd;
  }

  .flex-column {
    flex: 1;
  }

  .input-group-f {
    display: flex;
    input {
      width: calc(100% - 38px);
    }
    button {
      width: 38px;
    }
  }

  .column-header, .column-header-w-btn {
    background: rgba(0, 0, 0, .05);
    font-size: 14px;
    text-transform: uppercase;
    text-overflow: ellipsis;
    overflow: hidden;
    width: 100%;
  }

  .column-header {
    text-align: center;
  }

  .column-header-w-btn {
    display: flex;
    justify-content: space-between;
  }

  .column-header-inner, .column-header {
    padding: 5px;
  }

  .two-columns {
    display: flex;
    height: calc(100% - 34px);
    & > div {
      flex: 0 0 50%;
      max-width: 50%;
      height: 100%;
      &:first-child {
        border-right: 1px solid #aab2bd;
      }
    }
  }

  .btn-hd {
    padding: 0;
    width: 38px;
    text-align: center;
    border: none;
    color: #141414;
    background: transparent;
    &:hover {
      background: rgba(0, 0, 0, .1);
      color: #0f0f0f;
    }
  }
</style>
