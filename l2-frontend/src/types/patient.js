export default class Patient {
  constructor(data) {
    this.fio_age = data.fio_age;
    this.card = data.card;
    this.cardId = data.card_pk;
    this.base = data.base;
  }
}
