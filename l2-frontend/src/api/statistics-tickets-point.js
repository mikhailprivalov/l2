import {HTTP} from '../http-common'

async function getTicketsTypes() {
  try {
    const response = await HTTP.get('statistics-tickets/types')
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {visit: [], result: [], cause: [], outcome: [], exclude: []}
}

async function sendTicket(card_pk, visit, info, first_time, primary_visit, disp, result, outcome, disp_diagnos, exclude) {
  try {
    const response = await HTTP.post('statistics-tickets/send', {
      card_pk,
      visit,
      info,
      first_time,
      primary_visit,
      disp,
      result,
      outcome,
      disp_diagnos,
      exclude
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {pk: false}
}

async function loadTickets(date) {
  try {
    const response = await HTTP.post('statistics-tickets/get', {date})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {data: []}
}

async function invalidateTicket(pk, invalid) {
  try {
    const response = await HTTP.post('statistics-tickets/invalidate', {pk, invalid})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: 'Ошибка запроса'}
}


export default {getTicketsTypes, sendTicket, loadTickets, invalidateTicket}
