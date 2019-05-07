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

async function getResearchesParams(pks) {
  try {
    const response = await HTTP.post('researches/params', {pks})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {researches: []}
}

async function getFastTemplates(pk, all) {
  try {
    const response = await HTTP.post('researches/fast-templates', {pk, all})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {researches: []}
}

async function getTemplateData(pk) {
  try {
    const response = await HTTP.post('researches/fast-template-data', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {researches: []}
}

async function saveFastTemplate(pk, data, research_pk) {
  try {
    const response = await HTTP.post('researches/fast-template-save', {pk, data, research_pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {researches: []}
}

export default {getTemplates, getResearches, getResearchesByDepartment,
  getResearchesParams, getFastTemplates, getTemplateData,
  saveFastTemplate,
}
