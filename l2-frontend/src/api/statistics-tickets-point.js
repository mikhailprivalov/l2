import {HTTP} from '../http-common'

async function getTicketsTypes() {
  try {
    const response = await HTTP.get('statistics-tickets/types')
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {visit: [], result: []}
}


export default {getTicketsTypes}
