import { generator } from './http-common';

export default generator({
  getBases: {
    method: 'get',
    url: 'bases',
    onReject: { bases: [] },
  },
});
