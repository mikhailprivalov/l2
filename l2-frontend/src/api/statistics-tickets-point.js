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

async function sendTicket(card_pk, visit, info, first_time, primary_visit, disp, result) {
  try {
    const response = await HTTP.post('statistics-tickets/send', {card_pk, visit, info, first_time, primary_visit, disp, result})
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
  return {ok: false}
}


export default {getTicketsTypes, sendTicket, loadTickets, invalidateTicket}
