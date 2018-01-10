import {HTTP} from '../http-common'

async function getBases() {
  try {
    const response = await HTTP.get('bases')
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {bases: []}
}

export default {getBases}
