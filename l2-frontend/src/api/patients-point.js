import {HTTP} from '../http-common'

async function searchCard(type, query, list_all_cards = false) {
  try {
    const response = await HTTP.post('patients/search-card', {type, query, list_all_cards})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return []
}

async function searchIndividual(query) {
  try {
    const response = await HTTP.post('patients/search-individual', {query: query})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return []
}

export default {searchCard, searchIndividual}
