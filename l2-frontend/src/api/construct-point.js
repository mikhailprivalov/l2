import {generator} from './http-common'

export default generator({
  updateResearch: {
    url: 'researches/details',
    onReject: {ok: false},
  },
  researchDetails: {
    url: 'researches/update',
    onReject: {pk: -1, department: -1, title: '', short_title: '', code: ''},
  },
  updateTemplate: {
    url: 'researches/paraclinic_details',
    onReject: {groups: []},
  }
})
