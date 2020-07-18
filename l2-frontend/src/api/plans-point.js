import {generator} from './http-common'

export default generator({
  planOperationsSave: {
    url: 'plans/plan-operations-save',
  },
  getPlanOperastionsPatient: {
    url: 'plans/get-plan-operations-by-patient',
  },

  getPlansByParams: {
    url: 'plans/get-plan-by-params',
  }
})
