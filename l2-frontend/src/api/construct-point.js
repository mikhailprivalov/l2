import {HTTP} from '../http-common'

async function updateResearch(pk, department, title, short_title, code, info, hide) {
  try {
    const response = await HTTP.post('researches/update', {pk, department, title, short_title, code, info, hide})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false}
}

async function researchDetails(pk) {
  try {
    const response = await HTTP.post('researches/details', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {pk: -1, department: -1, title: '', short_title: '', code: ''}
}

export default {updateResearch, researchDetails}
