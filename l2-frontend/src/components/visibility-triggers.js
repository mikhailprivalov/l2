import { flatten } from 'lodash/array';
import { CalculateVisibility } from '../utils';

export const objFields = (groups) => flatten(
  groups.map(({ fields }) => fields),
).reduce((a, b) => Object.assign(a, { [b.pk]: b }), {});

export const vGroup = (group, groups, patient = {}) => {
  const fields = objFields(groups);
  const { visibility: formula } = group;
  if (formula !== '' && !CalculateVisibility(fields, formula, patient)) {
    return false;
  }
  for (const field of group.fields) {
    if (field.visibility === '' || CalculateVisibility(fields, field.visibility, patient)) {
      return true;
    }
  }
  return group.fields.length === 0;
};

export const vField = (
  group, groups, formula, patient = {},
) => formula === '' || (CalculateVisibility(objFields(groups), formula, patient) && vGroup(group, groups, patient));
