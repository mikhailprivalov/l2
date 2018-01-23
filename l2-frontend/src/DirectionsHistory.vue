<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <date-range style="width: 186px;" v-model="date_range"/>
      <div class="top-inner">
        <a href="#" @click.prevent="select_type(row.pk)" class="top-inner-select"
           :class="{ active: row.pk === active_type}"
           v-for="row in types" :title="row.title"><span>{{ row.title }}</span></a>
      </div>
    </div>
    <div class="content-picker">
    </div>
    <div class="bottom-picker">
      <div class="dropup" style="display: inline-block;width: 215px">
        <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                style="text-align: right!important;border-radius: 0">
          <span class="caret"></span> Действие с отмеченными
        </button>
        <ul class="dropdown-menu">
          <li><a href="#" @click.prevent>Повтор отправки результатов в РМИС</a></li>
          <li><a href="#" @click.prevent>Повтор отправки направлений в РМИС</a></li>
          <li><a href="#" @click.prevent>Скопировать исследования для назначения</a></li>
          <li><a href="#" @click.prevent>Печать результатов</a></li>
          <li><a href="#" @click.prevent>Печать штрих-кодов</a></li>
          <li><a href="#" @click.prevent>Печать направлений</a></li>
        </ul>
      </div>
      <div class="bottom-inner">
        <div>Направлений отмечено: {{checked.length}}</div>
      </div>
    </div>
  </div>
</template>

<script>
  import DateRange from './ui-cards/DateRange'

  export default {
    components: {DateRange},
    name: 'directions-history',
    data() {
      return {
        date_range: [getFormattedDate(today), getFormattedDate(today)],
        types: [
          {pk: 3, title: 'Направления пациента'},
          {pk: 0, title: 'Только выписанные'},
          {pk: 1, title: 'Материал в лаборатории'},
          {pk: 2, title: 'Результаты подтверждены'},
          {pk: 4, title: 'Созданы пользователем'}
        ],
        active_type: 3,
        checked: []
      }
    },
    methods: {
      select_type(pk) {
        this.active_type = pk
      }
    }
  }
</script>

<style scoped>

  .top-picker, .bottom-picker {
    height: 34px;
    background-color: #AAB2BD;
    position: absolute;
    left: 0;
    right: 0;
  }

  .top-picker {
    top: 0;
  }

  .top-picker /deep/ input {
    border-radius: 0;
    border: none;
    border-bottom: 1px solid #AAB2BD;
    background: #fff;
  }

  .top-picker /deep/ .input-group-addon {
    border: 1px solid #AAB2BD;
    border-top: none;
  }

  .top-inner, .content-picker, .content-none, .bottom-inner {
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    align-content: center;
    align-items: stretch;
    overflow-y: auto;
  }

  .content-picker {
    align-content: flex-start;
  }

  .content-none {
    align-items: center;
    align-content: center;
    justify-content: center;
  }

  .top-inner {
    position: absolute;
    left: 186px;
    top: 0;
    right: 0;
    height: 34px;
  }

  .top-inner-select, .research-select {
    align-self: stretch;
    display: flex;
    align-items: center;
    padding: 1px 2px 1px;
    color: #000;
    background-color: #fff;
    text-decoration: none;
    transition: .15s linear all;
    cursor: pointer;
    flex: 1;
    margin: 0;
    font-size: 12px;
    min-width: 0;
  }

  .top-inner-select {
    background-color: #AAB2BD;
    color: #fff
  }

  .research-select {
    flex: 0 1 auto;
    width: 25%;
    height: 34px;
    border: 1px solid #6C7A89 !important;
  }

  .top-inner-select.active, .research-select.active {
    background: #049372 !important;
    color: #fff;
  }

  .top-inner-select > span, .research-select span {
    display: block;
    text-overflow: ellipsis;
    overflow: hidden;
    word-break: keep-all;
    max-height: 2.2em;
    line-height: 1.1em;
  }

  .top-inner-select:hover {
    background-color: #434a54;
  }

  .research-select:hover {
    box-shadow: inset 0 0 8px rgba(0, 0, 0, .8) !important;
  }

  .content-picker, .content-none {
    position: absolute;
    top: 34px;
    bottom: 34px;
    left: 0;
    right: 0;
    overflow-y: auto;
  }

  .bottom-picker {
    bottom: 0;
  }

  .bottom-inner {
    position: absolute;
    color: #fff;
    height: 34px;
    right: 0;
    left: 215px;
    top: 0;
    justify-content: flex-end;
    align-content: center;
    align-items: center;
    padding-right: 5px;
  }
</style>
