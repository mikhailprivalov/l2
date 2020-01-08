const menuItems = Object.freeze({
  'primary receptions': 'Первичные приёмы',
  'laboratory': 'Лабораторные',
  'paraclinical': 'Параклинические',
  'consultation': 'Консультации',
  'diaries': 'Дневники',
  'vc': 'Врачебная комиссия',
  'bl': 'Больничные листы',
  'physiotherapy': 'Физиотерапия',
  'pharmacotherapy': 'Фармакотерапия',
  't, ad, p sheet': 't, ad, p – лист',
  'epicrisis': 'Эпикризы',
  'extracts': 'Выписки',
  'all': 'Показать всё',
})

export default {
  data() {
    return {
      menuItems,
      menuNeedPlus: {
        'primary receptions': true,
        laboratory: true,
        paraclinical: true,
        consultation: true,
        diaries: true,
        vc: true,
        bl: true,
        physiotherapy: true,
        pharmacotherapy: true,
        't, ad, p sheet': true,
        epicrisis: true,
        extracts: true,
      },
      plusDirectionsMode: {
        laboratory: true,
        paraclinical: true,
        consultation: true,
      },
      allowedOnlyOneEntry: {
        'primary receptions': true,
      }
    }
  }
}
