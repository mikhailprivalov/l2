import {HTTP} from '../http-common'

async function getCurrentUserInfo() {
  try {
    const response = await HTTP.get('current-user-info')
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {"auth": false, username: "", fio: "", groups: [], doc_pk: -1, department: {pk: -1, title: ""}}
}

export default {getCurrentUserInfo}
