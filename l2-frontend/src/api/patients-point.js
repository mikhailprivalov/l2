import { creator } from './http-common';

const searchCard = creator({ url: 'patients/search-card' }, []);

const searchIndividual = creator({ url: 'patients/search-individual' }, []);

const searchL2Card = creator({ url: 'patients/search-l2-card' }, []);

const getCard = creator({ urlFmt: 'patients/card/{card_pk}' }, []);

const sendCard = creator({ url: 'patients/card/save' }, {});

const individualsSearch = creator({ url: 'patients/individuals/search' }, {});

const individualSex = creator({ url: 'patients/individuals/sex' }, { sex: 'м' });

const editDoc = creator({ url: 'patients/individuals/edit-doc' }, {});

const editAgent = creator({ url: 'patients/individuals/edit-agent' }, {});

const updateCdu = creator({ url: 'patients/individuals/update-cdu' }, {});

const updateWIA = creator({ url: 'patients/individuals/update-wia' }, {});

const syncRmis = creator({ url: 'patients/individuals/sync-rmis' }, {});

const syncTfoms = creator({ url: 'patients/individuals/sync-tfoms' }, {});

const loadVaccine = creator({ url: 'patients/individuals/load-vaccine' }, {});

const loadAmbulatoryData = creator({ url: 'patients/individuals/load-ambulatory-data' }, {});

const loadAmbulatoryHistory = creator({ url: 'patients/individuals/load-ambulatory-history' }, {});

const loadBenefit = creator({ url: 'patients/individuals/load-benefit' }, {});

const loadVaccineDetail = creator({ url: 'patients/individuals/load-vaccine-detail' }, {});

const loadAmbulatoryDataDetail = creator({ url: 'patients/individuals/load-ambulatorydata-detail' }, {});

const loadBenefitDetail = creator({ url: 'patients/individuals/load-benefit-detail' }, {});

const loadAnamnesis = creator({ url: 'patients/individuals/load-anamnesis' }, {});

const saveAnamnesis = creator({ url: 'patients/individuals/save-anamnesis' }, {});

const saveVaccine = creator({ url: 'patients/individuals/save-vaccine' }, {});

const saveAmbulatoryData = creator({ url: 'patients/individuals/save-ambulatory-data' }, {});

const saveBenefit = creator({ url: 'patients/individuals/save-benefit' }, {});

const createIndividualFromCard = creator({ url: 'patients/create-l2-individual-from-card' }, {});

export default {
  searchCard,
  searchIndividual,
  searchL2Card,
  syncRmis,
  syncTfoms,
  getCard,
  sendCard,
  individualsSearch,
  individualSex,
  editDoc,
  updateCdu,
  updateWIA,
  editAgent,
  loadAnamnesis,
  saveAnamnesis,
  loadVaccine,
  saveVaccine,
  loadVaccineDetail,
  loadBenefit,
  loadBenefitDetail,
  saveBenefit,
  saveAmbulatoryData,
  loadAmbulatoryData,
  loadAmbulatoryDataDetail,
  loadAmbulatoryHistory,
  createIndividualFromCard,
};
