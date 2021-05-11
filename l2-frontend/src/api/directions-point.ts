import { generator } from './http-common';

export default generator({
  sendDirections: {
    url: 'directions/generate',
    onReject: { ok: false, directions: [], message: '' },
  },
  getHistory: {
    url: 'directions/history',
    onReject: { directions: [] },
  },
  getHospSetParent: {
    url: 'directions/hosp_set_parent',
  },
  updateParent: {
    url: 'directions/update_parent',
  },
  cancelDirection: {
    url: 'directions/cancel',
    onReject: { cancel: false },
  },
  getResults: {
    url: 'directions/results',
    onReject: { ok: false },
  },
  getParaclinicForm: {
    url: 'directions/paraclinic_form',
    onReject: { ok: false, message: '' },
  },
  anesthesiaResultSave: {
    url: 'directions/anesthesia_result',
    onReject: { ok: false, message: '' },
  },
  anesthesiaLoadData: {
    url: 'directions/anesthesia_load',
    onReject: { ok: false, message: '' },
  },
  paraclinicResultSave: {
    url: 'directions/paraclinic_result',
    onReject: { ok: false, message: '' },
  },
  paraclinicResultConfirm: {
    url: 'directions/paraclinic_result_confirm',
    onReject: { ok: false, message: '' },
  },
  paraclinicResultConfirmReset: {
    url: 'directions/paraclinic_result_confirm_reset',
    onReject: { ok: false, message: '' },
  },
  paraclinicResultUserHistory: {
    url: 'directions/paraclinic_result_history',
    onReject: { directions: [] },
  },
  getDirectionsServices: {
    url: 'directions/services',
    onReject: { ok: false, message: 'Ошибка запроса' },
  },
  getMarkDirectionVisit: {
    url: 'directions/mark-visit',
    onReject: { ok: false, message: 'Ошибка запроса' },
  },
  drectionReceiveMaterial: {
    url: 'directions/receive-material',
    onReject: { ok: false, message: 'Ошибка запроса' },
  },
  visitJournal: {
    url: 'directions/visit-journal',
    onReject: { data: [] },
  },
  recvJournal: {
    url: 'directions/recv-journal',
    onReject: { data: [] },
  },
  lastResult: {
    url: 'directions/last-result',
    onReject: { ok: false },
  },
  getResultsReport: {
    url: 'directions/results-report',
    onReject: { ok: false },
  },
  getRmisDirections: {
    url: 'directions/rmis-directions',
    onReject: { rows: [] },
  },
  getRmisDirection: {
    url: 'directions/rmis-direction',
  },
  paraclinicResultPatientHistory: {
    url: 'directions/patient-history',
  },
  paraclinicDataByFields: {
    url: 'directions/data-by-fields',
  },
  lastFractionResult: {
    url: 'directions/last-fraction-result',
  },
  lastFieldResult: {
    url: 'directions/last-field-result',
  },
  sendAMD: {
    url: 'directions/send-amd',
  },
  resetAMD: {
    url: 'directions/reset-amd',
  },
  getPurposes: {
    url: 'directions/purposes',
  },
  getExternalOrgranizations: {
    url: 'directions/external-organizations',
  },
  directionInFavorites: {
    url: 'directions/direction-in-favorites',
  },
  allDirectionsInFavorites: {
    url: 'directions/all-directions-in-favorites',
  },
  planExamination: {
    url: 'directions/plan-examinations',
  },
  getPlanExaminationPatient: {
    url: 'directions/get-plan-operation-by-patient',
  },
  getDirectionsTypeDate: {
    url: 'directions/directions-type-date',
  },

});
