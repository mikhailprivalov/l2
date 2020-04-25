import {generator} from './http-common'

export default generator({
  loadGroups: {
    url: 'bacteria/loadculture',
    onReject: {ok: false},
  },
  saveElement: {
    url: 'bacteria/saveculture',
    onReject: {pk: -1, department: -1, title: '', short_title: '', code: ''},
  },
  saveGroup: {
    url: 'bacteria/savegroup',
    onReject: {pk: -1, department: -1, title: '', short_title: '', code: ''},
  }
})
