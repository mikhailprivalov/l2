export interface FinSource {
  pk: number,
  title: string,
  default_diagnos: string,
}

export interface Base {
  pk: number,
  title: string,
  code: string,
  hide: boolean,
  history_number: boolean,
  internal_type: boolean,
  fin_sources: FinSource[],
}
