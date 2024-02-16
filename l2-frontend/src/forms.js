export default [
  {
    isGroup: true,
    title: 'Отказы',
    forms: [
      { url: '/forms/pdf?type=101.11&card_pk={card}', title: 'Отказ от видов мед. вмешательств (101.11)', type: '101.11' },
      { url: '/forms/pdf?type=101.19&card_pk={card}', title: 'Отказ от видов мед. вмешательств (101.19)', type: '101.19' },
    ],
  },
  { url: '/forms/pdf?type=101.10&card_pk={card}', title: 'Карта для диспансеризации', type: '101.10' },
  { url: '/forms/pdf?type=101.05&card_pk={card}', title: 'История изменений данных пациента', type: '101.05' },
  { url: '/forms/pdf?type=100.01&card_pk={card}', title: 'Паспорт здоровья', type: '100.01' },
  { url: '/forms/pdf?type=100.03&card_pk={card}', title: 'Титульный лист, Профосмотры', type: '100.03' },
  { url: '/forms/pdf?type=100.02&card_pk={card}', title: 'Титульный лист карты, 025/у', type: '100.02' },
  {
    isGroup: true,
    title: 'Согласия',
    forms: [
      { url: '/forms/pdf?type=101.25&card_pk={card}', title: 'Согласие на почечную терапию', type: '101.25' },
      { url: '/forms/pdf?type=101.24&card_pk={card}', title: 'Согласие на переливание крови', type: '101.24' },
      { url: '/forms/pdf?type=101.23&card_pk={card}', title: 'Согласие на телемедицинскую консультацию', type: '101.23' },
      { url: '/forms/pdf?type=101.22&card_pk={card}', title: 'Согласие на рентгенологическое исследование', type: '101.22' },
      { url: '/forms/pdf?type=101.13&card_pk={card}', title: 'Согласие на диспансеризацию', type: '101.13' },
      { url: '/forms/pdf?type=101.12&card_pk={card}', title: 'Согласие на прививку COVID-19', type: '101.12' },
      { url: '/forms/pdf?type=101.09&card_pk={card}', title: 'Согласие на прерывание беременности', type: '101.09' },
      { url: '/forms/pdf?type=101.06&card_pk={card}', title: 'Согласие COVID-19', type: '101.06' },
      { url: '/forms/pdf?type=101.14&card_pk={card}', title: 'Согласие на оперативное вмешательство', type: '101.14' },
      { url: '/forms/pdf?type=101.15&card_pk={card}', title: 'Согласие на анестезиологическое обеспечение', type: '101.15' },
      { url: '/forms/pdf?type=101.16&card_pk={card}', title: 'Согласие на препарат "вне инструкции"', type: '101.16' },
      { url: '/forms/pdf?type=101.17&card_pk={card}', title: 'Согласие на проведение МРТ', type: '101.17' },
      { url: '/forms/pdf?type=101.20&card_pk={card}', title: 'Согласие на мед. вмешательство (кт)', type: '101.20' },
      { url: '/forms/pdf?type=101.21&card_pk={card}', title: 'Согласие на мед. вмешательство (эндоскопия, узи)', type: '101.21' },
      { url: '/forms/pdf?type=101.29&card_pk={card}', title: 'Согласие на мед. вмешательство (R, КТ, ЭНД)', type: '101.29' },
      { url: '/forms/pdf?type=101.26&card_pk={card}', title: 'Согласие на мед. вмешательство (члх)', type: '101.26' },
      { url: '/forms/pdf?type=101.27&card_pk={card}', title: 'Передача работодателю заключения', type: '101.27' },
      {
        url: '/forms/pdf?type=101.01&individual={individual}',
        title: 'Согласие на ВИЧ-исследование',
        not_internal: true,
        type: '101.01',
      },
      { url: '/forms/pdf?type=101.30&card_pk={card}', title: 'Согласие на ВИЧ-исследование', type: '101.30' },
      { url: '/forms/pdf?type=101.03&card_pk={card}', title: 'Согласие на мед. вмешательство', type: '101.03' },
      { url: '/forms/pdf?type=101.28&card_pk={card}', title: 'Согласие на мед. вмешательство (травмпункт)', type: '101.28' },
      { url: '/forms/pdf?type=101.18&card_pk={card}', title: 'Согласие на мед. вмешательство', type: '101.18' },
      { url: '/forms/pdf?type=101.02&card_pk={card}', title: 'Согласие на обработку персональных данных', type: '101.02' },
    ],
  },
];

export const forDirs = [
  {
    url: '/forms/pdf?type=102.02&card_pk={card}&napr_id={dir}', title: 'Договор-печать', need_dirs: true, type: '102.02',
  },
];

export const form112 = [
  { url: '/forms/pdf?type=108.01&card_pk={card}', title: ' Ф.112' },
];

export const planOperations = [
  { url: '/forms/pdf?type=109.01&pks_plan={pks_plan}', title: ' План операций' },
];
