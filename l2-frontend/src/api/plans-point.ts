import { generator } from './http-common';

export default generator({
  planOperationsSave: {
    url: 'plans/plan-operations-save',
  },
  getPlanOperastionsPatient: {
    url: 'plans/get-plan-operations-by-patient',
  },
  getPlansByParams: {
    url: 'plans/get-plan-by-params',
  },
  getDepartmentsOperate: {
    url: 'plans/departments-can-operate',
  },
  changeAnestesiolog: {
    url: 'plans/change-anestesiolog',
  },
  planOperationsCancel: {
    url: 'plans/plan-operations-cancel',
  },
});
