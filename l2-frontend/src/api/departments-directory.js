import {HTTP} from '../http-common'

async function getDepartments() {
  try {
    const response = await HTTP.get('departments')
    if (response.statusText === 'OK') {
      return response.data.departments
    }
  } catch () {
  }
  return []
}

export default {getDepartments}
