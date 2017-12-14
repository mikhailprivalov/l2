export default {
  async getDepartments() {
    return await $.ajax({url: '/', cache: false})
  }
}
