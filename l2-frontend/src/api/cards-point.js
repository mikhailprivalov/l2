import {HTTP} from '../http-common'

async function getBases() {
  try {
    const response = await HTTP.get('bases')
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {can_edit: false, departments: [], types: []}
}

export default {getBases}
