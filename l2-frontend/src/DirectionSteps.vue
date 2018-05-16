<template>
  <el-steps :active="step" simple finish-status="success">
    <div class="hidden" id="tip-patient"><div class="el-tip">Выполните поиск карты пациента</div></div>
    <div class="hidden" id="tip-issled"><div class="el-tip">Выберите исследования</div></div>
    <div class="hidden" id="tip-diagnos"><div class="el-tip">Заполните диагноз</div></div>
    <div class="hidden" id="tip-fin"><div class="el-tip">Выберите источник финансирования</div></div>

    <el-step title="Пациент" icon="el-icon-document" v-tippy="{html: '#tip-patient', placement: 'bottom-start', animation : 'fade'}"></el-step>
    <el-step title="Исследования" icon="el-icon-menu" v-tippy="{html: '#tip-issled', placement: 'bottom-start', animation : 'fade'}"></el-step>
    <el-step title="Диагноз" icon="el-icon-edit" v-tippy="{html: '#tip-diagnos', placement: 'bottom-start', animation : 'fade'}"></el-step>
    <el-step title="Источник финансирования" icon="el-icon-more" v-tippy="{html: '#tip-fin', placement: 'bottom-start', animation : 'fade'}"></el-step>
  </el-steps>
</template>

<script>
  export default {
    name: 'direction-steps',
    data() {
      return {
        step: 0
      }
    },
    created() {
      const vm = this
      this.$root.$on('set-step', (i) => {
        vm.step = i
      })
    }
  }
</script>

<style scoped lang="scss">

  @media (max-width: 1116px) {
    /deep/.el-steps--simple {
      padding: 5px !important;
    }

    /deep/ .el-step__title {
      font-size: 10px !important;
    }

    /deep/ .el-step.is-simple .el-step__icon-inner[class*=el-icon]:not(.is-status) {
      font-size: 14px;
    }
  }

  @media (min-width: 1117px) {
    /deep/.el-steps--simple {
      padding: 5px 20px !important;
    }

    /deep/ .el-step__title {
      font-size: 12px !important;
    }
  }

  /deep/.el-steps--simple {
    margin: 3px !important;
    background: transparent;
    max-width: 800px;
    width: 100%;
  }

  /deep/ .el-step__main {
    overflow: hidden;
  }

  /deep/ .el-step__title {
    font-weight: 200;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /deep/ .el-step__head:not(.is-success):not(.is-wait) .el-step__icon,
  /deep/ .el-step__title.is-process {
    color: #fff;
    border-color: #fff;
  }

  /deep/ .el-step__line {
    display: none;
  }

  /deep/ .el-step.is-simple .el-step__arrow::after, /deep/ .el-step.is-simple .el-step__arrow::before {
    background: #fff;
  }
</style>

<style lang="scss">
  .el-tip {
    font-size: 16px;
  }
</style>
