import { generator } from './http-common';

export default generator({
  load: {
    url: 'stationar/load',
    onReject: { ok: false, message: '' },
  },
  counts: {
    url: 'stationar/counts',
    onReject: {},
  },
  hospServicesByType: {
    url: 'stationar/hosp-services-by-type',
    onReject: { data: [] },
  },
  makeService: {
    url: 'stationar/make-service',
    onReject: { pk: -1 },
  },
  directionsByKey: {
    url: 'stationar/directions-by-key',
    onReject: { data: [] },
  },
  aggregateLaboratory: {
    url: 'stationar/aggregate-laboratory',
    onReject: {},
  },
  aggregateDesc: {
    url: 'stationar/aggregate-desc',
    onReject: {},
  },
  aggregateTADP: {
    url: 'stationar/aggregate-tadp',
    onReject: {},
  },
  changeDepartment: {
    url: 'stationar/change-department',
    onReject: {},
  },
});
