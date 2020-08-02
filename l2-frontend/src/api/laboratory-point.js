import {generator} from './http-common'

export default generator({
  getFractions: {
    url: 'laboratory/fractions',
    onReject: {fractions: [], title: 'error'},
  },
  saveFsli: {
    url: 'laboratory/save-fsli',
  },
})
