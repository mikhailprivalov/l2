export type ParaclinicInputFieldRow = {
  pk: number | null
  order: number
  lines: number

  for_extract_card: boolean
  sign_organization: boolean

  title: string
  short_title: string
  default: string
  visibility: string
  hide: boolean

  values_to_input: unknown[]

  field_type: number
  can_edit: boolean
  required: boolean
  not_edit: boolean
  operator_enter_param: boolean
  is_diag_table: boolean
  for_talon: boolean
  for_med_certificate: boolean

  helper: string
  new_value: string
  attached: string | null
  controlParam: string

  patientControlParam: number
  cdaOption: number
  patternParam: number

  newGroupId: number | null
}
