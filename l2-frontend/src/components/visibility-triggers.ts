import { flatten } from 'lodash/array';

import { CalculateVisibility } from '@/utils';

export const objFields = (groups: any): any => flatten(
  groups.map(({ fields }) => fields),
).reduce((a, b) => Object.assign(a, { [b.pk]: b }), {});

export const vGroup = (group: any, groups: any, patient = {}): any => {
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

// eslint-disable-next-line max-len
export const vField = (group: any, groups: any, formula: any, patient = {}): any => formula === '' || (CalculateVisibility(objFields(groups), formula, patient) && vGroup(group, groups, patient));
