import {HTTP} from '../http-common'

async function getTemplates() {
  try {
    const response = await HTTP.get('researches/templates')
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {templates: {}}
}

async function getResearches() {
  try {
    const response = await HTTP.get('researches/all')
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {researches: {}}
}

async function getResearchesByDepartment(department) {
  try {
    const response = await HTTP.post('researches/by-department', {department})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {researches: []}
}

export default {getTemplates, getResearches, getResearchesByDepartment}
