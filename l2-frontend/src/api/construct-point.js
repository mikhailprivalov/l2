import {HTTP} from '../http-common'

async function updateResearch(pk, department, title, short_title, code, info, hide, groups) {
  try {
    const response = await HTTP.post('researches/update', {pk, department, title, short_title, code, info, hide, groups})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false}
}

async function updateTemplate(pk, title, researches, global) {
  try {
    const response = await HTTP.post('templates/update', {pk, title, researches, global})
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

async function researchParaclinicDetails(pk) {
  try {
    const response = await HTTP.post('researches/paraclinic_details', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {groups: []}
}

export default {updateResearch, researchDetails, updateTemplate}
