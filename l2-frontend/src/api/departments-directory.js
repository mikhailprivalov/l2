import {generator} from './http-common'

export default generator({
  getDepartments: {
    method: 'get',
    url: 'departments',
    onReject: {can_edit: false, departments: [], types: []}
  },
  sendDepartments: {
    url: 'departments',
    onReject: {ok: false, message: ''},
  }
})
