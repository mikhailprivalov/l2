import axios from 'axios'
import * as Cookies from 'es-cookie'
import {merge, pick} from 'lodash-es/object'

export const HTTP = axios.create({
  baseURL: window.location.origin + '/api',
  headers: {
    'X-CSRF-Token': Cookies.get('csrftoken')
  },
  params: {
    _: Math.floor((new Date().getTime()) / 100000)
  }
})

export const creator = ({method = 'post', url = null, urlFmt = null, onReject={}}, resultOnCatch = null) =>
  async (t = null, pickThis = null, moreData = {}) => {
    let data = t ? (pickThis ? merge(pick(t, Array.isArray(pickThis) ? pickThis : [pickThis]), moreData) : t) : moreData
    try {
      let response = {}
      if (urlFmt) {
        response = await HTTP.get(urlFmt.kwf(data))
      } else {
        response = await HTTP[method](url, data)
      }
      if (response.statusText === 'OK') {
        return response.data
      }
    } catch (e) {
      console.error(e)
    }
    return resultOnCatch || onReject
  }

export const generator = (points) => {
  const apiPoints = {};

  for (const k of Object.keys(points)) {
    apiPoints[k] = creator(points[k]);
  }

  return apiPoints;
};
