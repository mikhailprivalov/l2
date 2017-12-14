async function getDepartments() {
  return await $.ajax({url: '/', cache: false})
}

export default {getDepartments}
