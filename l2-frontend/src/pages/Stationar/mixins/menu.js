export const menuItems = Object.freeze({
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
  assignments: 'Назначения',
  't, ad, p sheet': 't, ad, p – листы',
  forms: 'Формы',
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
        assignments: false,
        't, ad, p sheet': true,
        epicrisis: true,
        extracts: true,
        forms: true,
      },
      plusDirectionsMode: {
        laboratory: true,
        paraclinical: true,
        morfology: true,
        consultation: true,
        forms: true,
      },
      allowedOnlyOneEntry: {
        'primary receptions': true,
        extracts: true,
      },
    };
  },
};
