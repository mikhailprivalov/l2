const menuItems = Object.freeze({
  'primary receptions': 'Первичные приёмы',
  laboratory: 'Лабораторные',
  paraclinical: 'Параклинические',
  morfology: 'Морфология',
  consultation: 'Консультации',
  diaries: 'Дневники',
  vc: 'Врачебная комиссия',
  operation: 'Операции',
  bl: 'Больничные листы',
  physiotherapy: 'Физиотерапия',
  pharmacotherapy: 'Фармакотерапия',
  't, ad, p sheet': 't, ad, p – листы',
  epicrisis: 'Эпикризы',
  extracts: 'Выписки',
  all: 'Показать всё',
});

export default {
  data() {
    return {
      menuItems,
      menuNeedPlus: {
        'primary receptions': true,
        laboratory: true,
        paraclinical: true,
        morfology: true,
        consultation: true,
        diaries: true,
        vc: true,
        operation: true,
        bl: true,
        physiotherapy: true,
        pharmacotherapy: false,
        't, ad, p sheet': true,
        epicrisis: true,
        extracts: true,
      },
      plusDirectionsMode: {
        laboratory: true,
        paraclinical: true,
        morfology: true,
        consultation: true,
      },
      allowedOnlyOneEntry: {
        'primary receptions': true,
        extracts: true,
      },
    };
  },
};
