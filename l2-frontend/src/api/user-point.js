import {HTTP} from '../http-common'

async function getCurrentUserInfo() {
  try {
    const response = await HTTP.get('current-user-info')
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {"auth": false, username: "", fio: "", groups: [], doc_pk: -1, department: {pk: -1, title: ""}, extended_departments: {}}
}

async function getDirectiveFrom() {
  try {
    const response = await HTTP.get('directive-from')
    if (response.statusText === 'OK') {
      return response.data.data
    }
  } catch (e) {
  }
  return []
}

async function loadUsers() {
  try {
    const response = await HTTP.post('users')
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function loadUser(pk) {
  try {
    const response = await HTTP.post('user', {
      pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function saveUser(pk, user_data) {
  try {
    const response = await HTTP.post('user-save', {
      pk, user_data,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function loadLocation(date) {
  try {
    const response = await HTTP.post('user-location', {
      date,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function getReserve(pk, patient) {
  try {
    const response = await HTTP.post('user-get-reserve', {
      pk, patient,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function fillSlot(slot) {
  try {
    const response = await HTTP.post('user-fill-slot', {
      slot,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

export default {getCurrentUserInfo, getDirectiveFrom, loadUsers, loadUser, saveUser, loadLocation, getReserve, fillSlot}
