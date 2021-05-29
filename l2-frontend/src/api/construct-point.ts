import { generator } from './http-common';

export default generator({
  updateResearch: {
    url: 'researches/update',
    onReject: { ok: false },
  },
  researchDetails: {
    url: 'researches/details',
    onReject: {
      pk: -1, department: -1, title: '', short_title: '', code: '',
    },
  },
  hospServiceDetails: {
    url: 'researches/hosp-service-details',
    onReject: {
      pk: -1, department: -500, hide: true, main_service_pk: -1, slave_service_pk: -1,
    },
  },
  updateTemplate: {
    url: 'templates/update',
    onReject: { groups: [] },
  },
});
