import axios from 'axios'
import * as Cookies from 'es-cookie'

export const HTTP = axios.create({
  baseURL: window.location.origin + '/api',
  headers: {
    'X-CSRF-Token': Cookies.get('csrftoken')
  },
  params: {
    _: new Date().getTime()
  }
})
