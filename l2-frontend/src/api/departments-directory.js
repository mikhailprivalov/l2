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

export default {getDepartments}
