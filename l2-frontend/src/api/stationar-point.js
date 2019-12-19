import {generator} from './http-common'

export default generator({
  load: {
    url: 'stationar/load',
    onReject: {ok: false, message: ''}
  },
})
