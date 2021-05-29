type CardNumber = string;
type CardId = number;
type IndividualId = number;
type BaseId = number;

interface InputData {
  fio_age?: string;
  card?: CardNumber;
  card_pk?: CardId;
  individual_pk?: IndividualId;
  base?: BaseId;
}

export default class Patient {
  // eslint-disable-next-line camelcase
  fio_age: string | void;

  card: CardNumber | void;

  cardId: CardId | void;

  // eslint-disable-next-line camelcase
  card_pk: CardId | void;

  individualId: IndividualId | void;

  base: BaseId | void;

  constructor(data: InputData) {
    this.fio_age = data.fio_age;
    this.card = data.card;
    this.cardId = data.card_pk;
    this.card_pk = data.card_pk;
    this.individualId = data.individual_pk;
    this.base = data.base;
  }
}
