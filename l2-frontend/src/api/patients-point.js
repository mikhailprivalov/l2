import {HTTP} from '../http-common'

async function searchCard(t, query) {
  try {
    const response = await HTTP.post('patients/search-card', {type: t, query: query})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return []
}

export default {searchCard}
