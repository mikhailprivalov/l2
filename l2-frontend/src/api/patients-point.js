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
    const response = await HTTP.post('patients/search-individual', {query})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return []
}

async function searchL2Card(card_pk) {
  try {
    const response = await HTTP.post('patients/search-l2-card', {card_pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return []
}

async function getCard(card_pk) {
  try {
    const response = await HTTP.get('patients/card/' + card_pk)
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return []
}

async function sendCard(card_pk, family, name, patronymic, birthday, sex, individual_pk, new_individual, base_pk) {
  try {
    const response = await HTTP.post('patients/card/save', {card_pk, family, name,
      patronymic, birthday, sex, individual_pk, new_individual, base_pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function individualsSearch(family, name, patronymic, birthday, sex) {
  try {
    const response = await HTTP.post('patients/individuals/search', {family, name, patronymic, birthday, sex})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function individualSex(t, v) {
  try {
    const response = await HTTP.post('patients/individuals/sex', {t, v})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {sex: 'м'}
}

async function editDoc(pk, type, serial, number, is_active, individual_pk) {
  try {
    const response = await HTTP.post('patients/individuals/edit-doc', {pk, type, serial, number, is_active, individual_pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

export default {searchCard, searchIndividual, searchL2Card,
  getCard, sendCard, individualsSearch, individualSex, editDoc}
