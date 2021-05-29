import { generator } from './http-common';

export default generator({
  getTemplates: {
    method: 'get',
    url: 'researches/templates',
    onReject: { templates: {} },
  },
  getResearches: {
    method: 'get',
    url: 'researches/all',
    onReject: { researches: [] },
  },
  getResearchesByDepartment: {
    url: 'researches/by-department',
    onReject: { researches: [] },
  },
  getResearchesParams: {
    url: 'researches/params',
  },
  getFastTemplates: {
    url: 'researches/fast-templates',
  },
  getTemplateData: {
    url: 'researches/fast-template-data',
  },
  saveFastTemplate: {
    url: 'researches/fast-template-save',
  },
  fractionTitle: {
    url: 'researches/fraction-title',
  },
  fieldTitle: {
    url: 'researches/field-title',
  },
  getFieldsAndGroups: {
    url: 'researches/fields-and-groups-titles',
  },
  getResearchesDispensary: {
    url: 'researches/research-dispensary',
  },
});
