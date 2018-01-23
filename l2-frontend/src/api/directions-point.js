import {HTTP} from '../http-common'

async function sendDirections(card_pk, diagnos, fin_source, history_num, ofname_pk, researches, comments) {
  try {
    const response = await HTTP.post('directions/generate', {
      card_pk,
      diagnos,
      fin_source,
      history_num,
      ofname_pk,
      researches,
      comments
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, directions: [], message: ""}
}

export default {sendDirections}
