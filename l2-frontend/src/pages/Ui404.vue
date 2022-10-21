<template>
  <div class="container">
    <div class="row">
      <div class="col-md-12">
        <div class="error-template">
          <h1>
            Oops!
          </h1>
          <h2>
            Ошибка 404
          </h2>
          <div class="error-details">
            Извините, страница не найдена!
          </div>
          <div class="error-actions">
            <router-link
              to="/"
              class="btn btn-blue-nb btn-lg"
            >
              <span class="glyphicon glyphicon-home" />
              Вернуться на главную
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'Ui404',
};
</script>
