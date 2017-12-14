import {HTTP} from '../http-common'

async function getDepartments() {
  return await HTTP.get('departments')
}

export default {getDepartments}
