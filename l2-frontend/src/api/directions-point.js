import {HTTP} from '../http-common'

async function sendDirections(card_pk, diagnos, fin_source, history_num, ofname_pk, researches, comments, for_rmis, rmis_data, vich_code, count, discount) {
  try {
    const response = await HTTP.post('directions/generate', {
      card_pk,
      diagnos,
      fin_source,
      history_num,
      ofname_pk,
      researches,
      comments,
      for_rmis,
      rmis_data,
      vich_code,
      count,
      discount,
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

async function getParaclinicForm(pk) {
  try {
    const response = await HTTP.post('directions/paraclinic_form', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: ''}
}

async function paraclinicResultSave(data, with_confirm) {
  try {
    const response = await HTTP.post('directions/paraclinic_result', {data, with_confirm})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: ''}
}

async function paraclinicResultConfirm(iss_pk) {
  try {
    const response = await HTTP.post('directions/paraclinic_result_confirm', {iss_pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: ''}
}

async function paraclinicResultConfirmReset(iss_pk) {
  try {
    const response = await HTTP.post('directions/paraclinic_result_confirm_reset', {iss_pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: ''}
}

async function paraclinicResultUserHistory(date) {
  try {
    const response = await HTTP.post('directions/paraclinic_result_history', {date})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {directions: []}
}

async function getDirectionsServices(pk) {
  try {
    const response = await HTTP.post('directions/services', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: "Ошибка запроса"}
}

async function getMarkDirectionVisit(pk, cancel) {
  try {
    const response = await HTTP.post('directions/mark-visit', {pk, cancel})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: "Ошибка запроса"}
}

async function visitJournal(date) {
  try {
    const response = await HTTP.post('directions/visit-journal', {date})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {data: []}
}

async function lastResult(individual, research) {
  try {
    const response = await HTTP.post('directions/last-result', {individual, research})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false}
}

async function getResultsReport(individual, params, date_start, date_end) {
  try {
    const response = await HTTP.post('directions/results-report', {individual, params, date_start, date_end})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false}
}

async function getRmisDirections(pk) {
  try {
    const response = await HTTP.post('directions/rmis-directions', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {rows: []}
}

async function getRmisDirection(pk) {
  try {
    const response = await HTTP.post('directions/rmis-direction', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function paraclinicResultPatientHistory(pk) {
  try {
    const response = await HTTP.post('directions/patient-history', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function paraclinicDataByFields(pk) {
  try {
    const response = await HTTP.post('directions/data-by-fields', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}


export default {
  sendDirections,
  getHistory,
  cancelDirection,
  getResults,
  getParaclinicForm,
  paraclinicResultSave,
  paraclinicResultConfirm,
  paraclinicResultConfirmReset,
  paraclinicResultUserHistory,
  getDirectionsServices,
  getMarkDirectionVisit,
  visitJournal,
  lastResult,
  getResultsReport,
  getRmisDirections,
  getRmisDirection,
  paraclinicResultPatientHistory,
  paraclinicDataByFields,
}
