export default {
  pagination: {
    goto: 'Перейти на',
    page: '',
    itemsPerPage: ' на стр',
    total: function total(_total) {
      return `Всего записей: ${_total}`;
    },
    prev5: 'Назад на 5 страниц',
    next5: 'Вперёд на 5 страниц',
  },
  table: {
    confirmFilter: 'Подтвердить',
    resetFilter: 'Сбросить',
    cut: 'Вырезать',
    copy: 'Скопировать',
    insertRowAbove: 'Вставить строку выше',
    insertRowBelow: 'Вставить строку ниже',
    removeRow: 'Удалить строку $1',
    emptyRow: 'Очистить строку $1',
    emptyColumn: 'Очистить колонку $1',
    emptyCell: 'Очистить ячейку',
    leftFixedColumnTo: 'Left fixed column to',
    cancelLeftFixedColumnTo: 'Cancel left fixed column to',
    rightFixedColumnTo: 'Right fixed column to',
    cancelRightFixedColumnTo: 'Cancel right fixed column to',
  },
};
