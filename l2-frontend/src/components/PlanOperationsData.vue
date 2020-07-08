<template>
    <div>
     <div class="form-row">
        <div class="row-t">Пациент (карта)</div>
      </div>
      <div class="form-row">
        <div class="row-t">История</div>
      </div>
      <div class="form-row">
        <div class="row-t">Дата операции</div>
      </div>
      <div class="form-row">
        <div class="row-t">Врач-хирург</div>
      </div>
      <div class="form-row">
        <div class="row-t">Вид операции</div>
      </div>
      <div class="row color-bottom">
        <div style="float: right; margin-right: 10px; padding-right: 10px" >
              <button class="btn btn-blue-nb btn-sm" style="border-radius: 0px">
                Сохранить в план
              </button>
              <button class="btn btn-blue-nb btn-sm" style="border-radius: 0px">
                Удалить из плана
              </button>
          </div>
      </div>
    </div>

</template>

<script>
    export default {
        name: "PlanOperationsData"
    }
</script>

<style scoped lang="scss">
  .color-bottom {
    border-bottom: 1px solid #434a54;
  }

  select.form-control {
    padding: 0;
    overflow: visible;
  }

  .nonPrior {
    opacity: .7;

    &:hover {
      opacity: 1;
    }
  }

  .prior {
    background-color: rgba(#000, .05);
  }

  .modal-mask {
    align-items: stretch !important;
    justify-content: stretch !important;
  }

  /deep/ .panel-flt {
    margin: 41px;
    align-self: stretch !important;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  /deep/ .panel-body {
    flex: 1;
    padding: 0;
    height: calc(100% - 91px);
    min-height: 200px;
  }

  .form-row {
    width: 100%;
    display: flex;
    border-bottom: 1px solid #434a54;

    &:first-child:not(.nbt-i) {
      border-top: 1px solid #434a54;
    }

    justify-content: stretch;

    .row-t {
      background-color: #AAB2BD;
      padding: 7px 0 0 10px;
      width: 35%;
      flex: 0 35%;
      color: #fff;
    }

    .input-group {
      flex: 0 65%;
    }

    input, .row-v, /deep/ input {
      background: #fff;
      border: none;
      border-radius: 0 !important;
      width: 65%;
      flex: 0 65%;
      height: 34px;
    }

    &.sm-f {
      .row-t {
        padding: 2px 0 0 10px;
      }

      input, .row-v, /deep/ input {
        height: 26px;
      }
    }

    /deep/ input {
      width: 100% !important;
    }

    .row-v {
      padding: 7px 0 0 10px;
    }

    /deep/ .input-group {
      border-radius: 0;
    }

    /deep/ ul {
      width: auto;
      font-size: 13px;
    }

    /deep/ ul li {
      overflow: hidden;
      text-overflow: ellipsis;
      padding: 2px .25rem;
      margin: 0 .2rem;

      a {
        padding: 2px 10px;
      }
    }
  }

  .col-form {
    &.left {
      padding-right: 0 !important;

      .row-t, input, .row-v, /deep/ input {
        border-right: 1px solid #434a54 !important;
      }

      .form-row .input-group {
        width: 65%;
      }
    }

    &:not(.left):not(.mid) {
      padding-left: 0 !important;

      .row-t {
        border-right: 1px solid #434a54;
      }
    }
  }

  .info-row {
    padding: 7px;
  }

  .individual {
    cursor: pointer;

    &:hover {
      background-color: rgba(0, 0, 0, .15);
    }
  }

  .str /deep/ .input-group {
    width: 100%;
  }

  .lst {
    margin: 0;
    line-height: 1;
  }

  .c-pointer {
    &, & strong, &:hover {
      cursor: pointer!important;
    }
  }
</style>
