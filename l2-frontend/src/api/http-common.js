import axios from 'axios';
import * as Cookies from 'es-cookie';
import { merge, pick } from 'lodash/object';

export const HTTP = axios.create({
  baseURL: `${window.location.origin}/api`,
  headers: {
    'X-CSRF-Token': Cookies.get('csrftoken'),
  },
});

export const smartCall = async ({
  method = 'post', url, urlFmt = null, onReject = {}, ctx = null, moreData = {}, pickKeys,
}) => {
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
      response = await HTTP.get(urlFmt.kwf(data));
    } else {
      response = await HTTP[method](url, data);
    }
    if (response.statusText === 'OK') {
      return response.data;
    }
  } catch (e) {
    console.error(e);
  }
  return onReject;
};

export const creator = ({
  method = 'post', url = null, urlFmt = null, onReject = {},
}, resultOnCatch = null) => (ctx = null, pickKeys = null, moreData = {}) => smartCall({
  method,
  url,
  urlFmt,
  onReject: resultOnCatch || onReject,
  ctx,
  moreData,
  pickKeys,
});

export const generator = (points) => {
  const apiPoints = {};

  for (const k of Object.keys(points)) {
    apiPoints[k] = creator(points[k]);
  }

  return apiPoints;
};
