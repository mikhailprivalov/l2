import {HTTP} from '../http-common'

async function getDepartments() {
  try {
    const response = await HTTP.get('departments')
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {can_edit: false, departments: [], types: []}
}

async function sendDepartments(type, data) {
  try {
    const response = await HTTP.post('departments', {type: type, data: data})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: ''}
}

export default {getDepartments, sendDepartments}
