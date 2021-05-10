import { generator } from './http-common';

export default generator({
  getCurrentUserInfo: {
    method: 'get',
    url: 'current-user-info',
    onReject: {
      auth: false, username: '', fio: '', groups: [], doc_pk: -1, department: { pk: -1, title: '' }, extended_departments: {},
    },
  },
  getDirectiveFrom: {
    method: 'get',
    url: 'directive-from',
    onReject: { data: [] },
  },
  loadUsers: {
    url: 'users',
  },
  loadUser: {
    url: 'user',
  },
  saveUser: {
    url: 'user-save',
  },
  loadLocation: {
    url: 'user-location',
  },
  getReserve: {
    url: 'user-get-reserve',
  },
  fillSlot: {
    url: 'user-fill-slot',
  },
  loadJobTypes: {
    url: 'job-types',
  },
  saveJob: {
    url: 'job-save',
  },
  loadJobs: {
    url: 'job-list',
  },
  jobCancel: {
    url: 'job-cancel',
  },
  loadReaderStatus: {
    url: 'reader-status',
  },
  loadUsersByGroup: {
    url: 'load-users-by-group',
  },
});
