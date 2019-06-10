import {HTTP} from '../http-common'

async function searchCard(type, query, list_all_cards = false, inc_rmis = false) {
  try {
    const response = await HTTP.post('patients/search-card', {type, query, list_all_cards, inc_rmis})
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

async function sendCard(card_pk, family, name, patronymic,
                        birthday, sex, individual_pk, new_individual, base_pk,
                        fact_address, main_address, work_place, main_diagnosis, work_position,
                        work_place_db, custom_workplace, district, gin_district, phone) {
  try {
    const response = await HTTP.post('patients/card/save', {card_pk, family, name,
      patronymic, birthday, sex, individual_pk, new_individual, base_pk, work_position,
      fact_address, main_address, work_place, main_diagnosis, work_place_db, custom_workplace,
      district, gin_district, phone})
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

async function editDoc(pk, type, serial, number, is_active, individual_pk, date_start, date_end, who_give, card_pk) {
  try {
    const response = await HTTP.post('patients/individuals/edit-doc', {
      pk, type, serial, number, date_start, date_end, who_give, is_active, individual_pk, card_pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function editAgent(key, parent_card_pk, card_pk, doc, clear) {
  try {
    const response = await HTTP.post('patients/individuals/edit-agent', {
      key, card_pk, doc, clear, parent_card_pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function updateCdu(card_pk, doc_pk) {
  try {
    const response = await HTTP.post('patients/individuals/update-cdu', {
      card_pk, doc_pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function updateWIA(card_pk, key) {
  try {
    const response = await HTTP.post('patients/individuals/update-wia', {
      card_pk, key,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function syncRmis(card_pk) {
  try {
    const response = await HTTP.post('patients/individuals/sync-rmis', {
      card_pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function loadDreg(card_pk) {
  try {
    const response = await HTTP.post('patients/individuals/load-dreg', {
      card_pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function loadBenefit(card_pk) {
  try {
    const response = await HTTP.post('patients/individuals/load-benefit', {
      card_pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function loadDregDetail(pk) {
  try {
    const response = await HTTP.post('patients/individuals/load-dreg-detail', {
      pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function loadBenefitDetail(pk) {
  try {
    const response = await HTTP.post('patients/individuals/load-benefit-detail', {
      pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function loadAnamnesis(card_pk) {
  try {
    const response = await HTTP.post('patients/individuals/load-anamnesis', {
      card_pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function saveAnamnesis(card_pk, text) {
  try {
    const response = await HTTP.post('patients/individuals/save-anamnesis', {
      card_pk, text,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function saveDreg(card_pk, pk, data) {
  try {
    const response = await HTTP.post('patients/individuals/save-dreg', {
      data,
      card_pk,
      pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

async function saveBenefit(card_pk, pk, data) {
  try {
    const response = await HTTP.post('patients/individuals/save-benefit', {
      data,
      card_pk,
      pk,
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {}
}

export default {searchCard, searchIndividual, searchL2Card, syncRmis,
  getCard, sendCard, individualsSearch, individualSex, editDoc, updateCdu, updateWIA,
  editAgent, loadAnamnesis, saveAnamnesis, loadDreg, saveDreg, loadDregDetail,
  loadBenefit, loadBenefitDetail, saveBenefit,
}
