import { ref, watch } from 'vue';

import { smartCall } from './http-common';

type CallParams = {
  path: string;
  data?: Record<string, any>,
  disableReactiveRequest?: boolean,
  disableRaiseError?: boolean,
  onReject?: any,
}

interface Options {
  defaultData?: any,
  validateRequestData?: Record<string, (param: any) => boolean>
}

// eslint-disable-next-line no-shadow
export const enum ApiStatus {
  IDLE = 'idle',
  LOADING = 'loading',
  SUCCESS = 'success',
  REQUEST_ERROR = 'requestError',
  VALIDATION_ERROR = 'validationError',
}

const EMPTY = {};

export default function useApi<T>(params: CallParams, options?: Options) {
  const data = ref<T>(options?.defaultData ?? null);
  const status = ref<ApiStatus>(ApiStatus.IDLE);

  const {
    path,
    data: requestData,
    disableReactiveRequest,
    disableRaiseError,
    onReject = EMPTY,
  } = params;

  const call = async () => {
    if (options?.validateRequestData) {
      for (const key of Object.keys(options.validateRequestData)) {
        if (!requestData || !options.validateRequestData[key](requestData[key])) {
          status.value = ApiStatus.VALIDATION_ERROR;
          return;
        }
      }
    }

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
      status.value = ApiStatus.REQUEST_ERROR;
      throw e;
    }
  };

  watch(() => params, async () => {
    if (!disableReactiveRequest) {
      await call();
    }
  }, {
    deep: true,
    immediate: !disableReactiveRequest,
  });

  return {
    data,
    status,
    call,
  };
}
