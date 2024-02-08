import { useStore } from '@/store';
import * as actions from '@/store/action-types';

export default () => {
  const store = useStore();

  return {
    inc() {
      store.dispatch(actions.INC_LOADING).then();
    },
    dec() {
      store.dispatch(actions.DEC_LOADING).then();
    },
  };
};
