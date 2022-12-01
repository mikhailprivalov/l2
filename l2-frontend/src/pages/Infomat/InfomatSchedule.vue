<template>
  <div class="infomat-root">
    <ol>
      <li>
        Вход пациента:
        <ol>
          <li>по ручному вводу полиса</li>
          <li>по сканированию карты</li>
          <li>в любой момент пользовательского пути до подтверждения записи</li>
        </ol>
      </li>
      <li>
        Выход пользователя:
        <ol>
          <li>по кнопке</li>
          <li>по таймауту</li>
          <li>после записи</li>
        </ol>
      </li>
      <li>
        Загрузка категорий ресурсов записей
      </li>
      <li>
        Выбор даты
      </li>
      <li>
        Отображение доступных врачей
      </li>
      <li>
        Выбор врача
      </li>
      <li>
        Отображение доступных временных слотов
      </li>
      <li>
        Выбор временного слота
      </li>
      <li>
        Запись на выбранный слот
      </li>
      <li>
        Печать талона
      </li>
      <li>
        Предварительная загрузка сеток расписания и вывод из кэша
      </li>
      <li>
        Фоновая проверка, что данные на экране обновились
      </li>
      <li>
        Опциональная запись к любому врачу по дате и времени (отображение времени вместо врачей после выбора даты)
      </li>
    </ol>
  </div>
</template>

<script lang="ts">
export default {
  name: 'InfomatSchedule',
  data() {
    return {
      cardData: null,
      lastActionAt: null,
    };
  },
  mounted() {
    this.$root.$on('infomat-action', () => {
      this.lastActionAt = new Date();
    });
  },
};
</script>

<style scoped lang="scss">
.infomat-root {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #fff;
}
</style>
