import axions from 'axios'
import * as Cookies from 'es-cookie'

export const HTTP = axions.create({
  baseURL: window.location.origin + '/api',
  headers: {
    'X-CSRF-Token': Cookies.get('csrftoken')
  }
})
