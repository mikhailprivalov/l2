import {HTTP} from '../http-common'

async function getDepartments() {
  const response = await HTTP.get('departments')
  if (response.statusText === 'OK') {
    return response.data.departments
  }
  return []
}

export default {getDepartments}
