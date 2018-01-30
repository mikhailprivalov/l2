import {HTTP} from '../http-common'

async function sendDirections(card_pk, diagnos, fin_source, history_num, ofname_pk, researches, comments) {
  try {
    const response = await HTTP.post('directions/generate', {
      card_pk,
      diagnos,
      fin_source,
      history_num,
      ofname_pk,
      researches,
      comments
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, directions: [], message: ''}
}

async function getHistory(type, patient, date_from, date_to) {
  try {
    const response = await HTTP.post('directions/history', {
      type,
      patient,
      date_from,
      date_to
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {directions: []}
}

async function cancelDirection(pk) {
  try {
    const response = await HTTP.post('directions/cancel', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {cancel: false}
}

async function getResults(pk) {
  try {
    const response = await HTTP.post('directions/results', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false}
}

export default {sendDirections, getHistory, cancelDirection, getResults}
