import {CalculateVisibility} from '../utils'
import {flatten} from 'lodash/array'

export const vField = (groups, formula) => formula === '' || CalculateVisibility(objFields(groups), formula)

export const vGroup = (group, groups, formula) => {
  const fields = objFields(groups);
  if(formula !== '' && !CalculateVisibility(fields, formula)) {
    return false;
  }
  for (const field of group.fields) {
    if (field.visibility === '' || CalculateVisibility(fields, field.visibility)) {
      return true;
    }
  }
  return group.fields.length === 0;
}

export const objFields = (groups) => flatten(groups.map(({fields}) => fields)).reduce((a, b) => ({
  ...a,
  [b.pk]: b
}), {})
