type CardNumber = string;
type CardId = number;
type IndividualId = number;
type BaseId = number;
type Phone = string;

export interface Document {
  pk: number;
  serial: string;
  number: string;
  date_end: string | null;
  date_start: string | null;
  who_give: string;
  is_active: boolean;
  document_type_id: number;
  type_title: string;
  from_rmis: boolean;
  rmis_uid: string | null;
}

interface InputData {
  fio_age?: string;
  card?: CardNumber;
  card_pk?: CardId;
  individual_pk?: IndividualId;
  base?: BaseId;
}

export interface SimplePatient {
  family: string;
  name: string;
  twoname: string;
  age: string;
  birthday: string;
  fio_age: string;
  docs: Document[];
  phones: Phone[];
  disp_data: any;
  pk: number;
  individual_pk: number;
  base_pk: number;
  num: string;
  type_title: string;
  main_diagnosis: string;
  sex: string;
  status_disp: string;
  is_rmis: boolean;
  isArchive: boolean;
}

export default class Patient {
  fio_age: string | void;

  card: CardNumber | void;

  cardId: CardId | void;

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
