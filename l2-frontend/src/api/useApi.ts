import { ref, watch } from 'vue';

import { smartCall } from './http-common';

type CallParams = {
  path: string;
  data?: Record<string, any>,
  disableReactiveRequest?: boolean,
  disableRaiseError?: boolean,
  onReject?: any,
}

// eslint-disable-next-line no-shadow
export const enum ApiStatus {
  IDLE = 'idle',
  LOADING = 'loading',
  SUCCESS = 'success',
  ERROR = 'error',
}

const EMPTY = {};

export default function useApi(params: CallParams) {
  const data = ref<any>(null);
  const status = ref(ApiStatus.IDLE);

  const {
    path,
    data: requestData,
    disableReactiveRequest,
    disableRaiseError,
    onReject = EMPTY,
  } = params;

  const call = async () => {
    status.value = ApiStatus.LOADING;
    try {
      data.value = await smartCall({
        url: path,
        ctx: requestData,
        raiseError: !disableRaiseError,
        onReject,
      });
      status.value = ApiStatus.SUCCESS;
    } catch (e) {
      status.value = ApiStatus.ERROR;
      throw e;
    }
  };

  watch(params, async () => {
    if (!disableReactiveRequest) {
      await call();
    }
  }, {
    deep: true,
  });

  return {
    data,
    status,
    call,
  };
}
