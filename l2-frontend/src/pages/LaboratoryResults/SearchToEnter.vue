<template>
  <div>
    <div class="filters">
      <form autocomplete="off" @submit.prevent>
        <input autocomplete="false" name="hidden" type="text" style="display: none;"/>
        <div class="input-group">
          <span class="input-group-btn">
            <button type="button" class="btn btn-blue-nb">Направление</button>
          </span>
          <span class="input-group-btn">
            <button type="button" style="margin-right: -1px;" class="btn btn-blue-nb">Ёмкость</button>
          </span>
          <input type="text" maxlength="13" class="form-control" autofocus/>
          <span class="input-group-btn">
            <button style="margin-right: -1px;" type="button" class="btn btn-blue-nb">Поиск</button>
          </span>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: "SearchToEnter"
}
</script>

<style scoped lang="scss">
.filters {
  background-color: #edeeef;

  form {
    .btn, .form-control {
      border-radius: 0 !important;
      padding: 6px 4px !important;
      font-size: 12px;
      height: 34px;
    }
  }
}
</style>
