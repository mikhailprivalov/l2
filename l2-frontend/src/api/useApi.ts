import { Ref, ref, watch } from 'vue';

import { smartCall } from './http-common';

type CallParams = {
  path: string;
  data?: Record<string, any>,
  disableReactiveRequest?: boolean,
  enableRaiseError?: boolean,
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

export default function useApi<T>(params: Ref<CallParams>, options?: Options) {
  const data = ref(options?.defaultData ?? null) as Ref<T> | Ref<null>;
  const status = ref<ApiStatus>(ApiStatus.IDLE);

  const call = async (): Promise<T | null> => {
    if (options?.validateRequestData) {
      for (const key of Object.keys(options.validateRequestData)) {
        if (!params.value.data || !options.validateRequestData[key](params.value.data[key])) {
          status.value = ApiStatus.VALIDATION_ERROR;
          return options?.defaultData ?? null;
        }
      }
    }

    status.value = ApiStatus.LOADING;
    try {
      data.value = await smartCall({
        url: params.value.path,
        ctx: params.value.data,
        raiseError: params.value.enableRaiseError,
        onReject: params.value.onReject ?? options?.defaultData ?? EMPTY,
      }) as T | null;
      status.value = ApiStatus.SUCCESS;

      return data.value;
    } catch (e) {
      status.value = ApiStatus.REQUEST_ERROR;
      throw e;
    }
  };

  const reset = () => {
    status.value = ApiStatus.IDLE;
    data.value = options?.defaultData ?? null;
  };

  watch(() => params, async () => {
    if (!params.value.disableReactiveRequest) {
      await call();
    }
  }, {
    deep: true,
    immediate: !params.value.disableReactiveRequest,
  });

  return {
    data,
    status,
    call,
    reset,
  };
}
