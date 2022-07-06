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
  getPlansHospitalizationByParams: {
    url: 'plans/get-plan-hospitalization',
  },
  cancelPlansHospitalization: {
    url: 'plans/cancel-plan-hospitalization',
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
  getOffsetHoursForPlanOperations: {
    url: 'plans/get-offset-hours-plan-operations',
  },
});
