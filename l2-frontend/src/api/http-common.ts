import axios from 'axios';
import * as Cookies from 'es-cookie';
import { merge, pick } from 'lodash/object';

import { valuesToString } from '@/utils';

export const HTTP = axios.create({
  baseURL: `${window.location.origin}/api`,
});

export const smartCall = async ({
  method = 'post', url, urlFmt = null, onReject = {}, ctx = null, moreData = {}, pickKeys, formData = null, raiseError = false,
}: any): Promise<any> => {
  let data;
  if (ctx) {
    data = pickKeys ? merge(pick(ctx, Array.isArray(pickKeys) ? pickKeys : [pickKeys]), moreData) : ctx;
  } else {
    data = moreData;
  }

  if (window.prefetch) {
    const prefetchedResult = window.prefetch.popRouteCache(url, data);
    if (prefetchedResult) {
      return prefetchedResult;
    }
  }

  try {
    let response;
    if (urlFmt) {
      response = await HTTP.get(valuesToString(urlFmt, data));
    } else if (formData) {
      if (data && Object.keys(data).length) {
        const blob = new Blob([JSON.stringify(data)], {
          type: 'application/json',
        });
        formData.append('form', blob);
      }
      response = await HTTP.post(url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    } else {
      response = await HTTP[method](url, data, {
        headers: {
          'X-CSRFToken': Cookies.get('csrftoken'),
        },
      });
    }
    if (response.statusText === 'OK') {
      return response.data;
    }
  } catch (e) {
    if (raiseError) {
      throw e;
    } else {
      // eslint-disable-next-line no-console
      console.error(e);
    }
  }
  return onReject;
};

export const creator = ({
  method = 'post', url = null, urlFmt = null, onReject = {},
}: any, resultOnCatch: any = null): any => (ctx = null, pickKeys = null, moreData = {}) => smartCall({
  method,
  url,
  urlFmt,
  onReject: resultOnCatch || onReject,
  ctx,
  moreData,
  pickKeys,
});

export const generator = (points: any): any => {
  const apiPoints = {};

  for (const k of Object.keys(points)) {
    apiPoints[k] = creator(points[k]);
  }

  return apiPoints;
};
