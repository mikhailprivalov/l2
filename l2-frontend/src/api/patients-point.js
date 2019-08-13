import {creator} from './http-common'

const searchCard = creator({url: 'patients/search-card'}, [])

const searchIndividual = creator({url: 'patients/search-individual'}, [])

const searchL2Card = creator({url: 'patients/search-l2-card'}, [])

const getCard = creator({urlFmt: 'patients/card/{card_pk}'}, [])

const sendCard = creator({url: 'patients/card/save'}, {})

const individualsSearch = creator({url: 'patients/individuals/search'}, {})

const individualSex = creator({url: 'patients/individuals/sex'}, {sex: 'м'})

const editDoc = creator({url: 'patients/individuals/edit-doc'}, {})

const editAgent = creator({url: 'patients/individuals/edit-agent'}, {})

const updateCdu = creator({url: 'patients/individuals/update-cdu'}, {})

const updateWIA = creator({url: 'patients/individuals/update-wia'}, {})

const syncRmis = creator({url: 'patients/individuals/sync-rmis'}, {})

const loadDreg = creator({url: 'patients/individuals/load-dreg'}, {})

const loadBenefit = creator({url: 'patients/individuals/load-benefit'}, {})

const loadDregDetail = creator({url: 'patients/individuals/load-dreg-detail'}, {})

const loadBenefitDetail = creator({url: 'patients/individuals/load-benefit-detail'}, {})

const loadAnamnesis = creator({url: 'patients/individuals/load-anamnesis'}, {})

const saveAnamnesis = creator({url: 'patients/individuals/save-anamnesis'}, {})

const saveDreg = creator({url: 'patients/individuals/save-dreg'}, {})

const saveBenefit = creator({url: 'patients/individuals/save-benefit'}, {})

export default {
  searchCard, searchIndividual, searchL2Card, syncRmis,
  getCard, sendCard, individualsSearch, individualSex, editDoc, updateCdu, updateWIA,
  editAgent, loadAnamnesis, saveAnamnesis, loadDreg, saveDreg, loadDregDetail,
  loadBenefit, loadBenefitDetail, saveBenefit,
}
