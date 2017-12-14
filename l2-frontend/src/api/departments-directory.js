export default {
  async getDepartments() {
    const data = await $.ajax({url: '/', cache: false})
    return data
  }
}
