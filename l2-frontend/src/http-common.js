import axions from 'axios'
import * as Cookies from 'es-cookie'

export const HTTP = axions.create({
  baseURL: 'http://demo6916661.mockable.io', //window.location.origin,
  headers: {
    'X-CSRF-Token': Cookies.get('csrftoken')
  }
})
