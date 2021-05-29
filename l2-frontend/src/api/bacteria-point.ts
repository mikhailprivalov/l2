import { generator } from './http-common';

export default generator({
  loadGroups: {
    url: 'bacteria/loadculture',
    onReject: { ok: false },
  },
  saveElement: {
    url: 'bacteria/saveculture',
  },
  saveGroup: {
    url: 'bacteria/savegroup',
  },
  updateGroup: {
    url: 'bacteria/updategroup',
  },
  addNewGroup: {
    url: 'bacteria/addnewgroup',
  },
  loadantibioticset: {
    url: 'bacteria/loadantibioticset',
  },
  loadCultures: {
    url: 'bacteria/loadculture',
  },
  loadSetElements: {
    url: 'bacteria/loadsetelements',
  },
  getBacGroups: {
    url: 'bacteria/get-bac-groups',
  },
  getBacByGroup: {
    url: 'bacteria/get-bac-by-group',
  },
  packageGroupCreate: {
    url: 'bacteria/package-group-create',
  },
  getAntibioticGroups: {
    url: 'bacteria/get-antibiotic-groups',
  },
});
