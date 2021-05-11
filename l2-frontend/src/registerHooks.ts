import Vue from 'vue';

import * as actions from './store/action-types';
import directionsPoint from './api/directions-point';

function printForm(tpl: string, pks: number[]) {
  if (!pks || !Array.isArray(pks) || pks.length === 0) {
    return;
  }
  window.open(tpl.replace('{pks}', JSON.stringify(pks)), '_blank');
}

export default (instance: Vue): void => {
  instance.$root.$on('no-loader-in-header', (status) => instance.$store.dispatch(actions.SET_LOADER_IN_HEADER, !status));

  instance.$root.$on('print:directions', (pks) => printForm('/directions/pdf?napr_id={pks}', pks));

  instance.$root.$on('print:hosp', (pks) => printForm('/barcodes/hosp?napr_id={pks}', pks));

  instance.$root.$on('print:directions:contract', (pks) => printForm('/directions/pdf?napr_id={pks}&contract=1', pks));

  instance.$root.$on('print:barcodes', (pks) => printForm('/barcodes/tubes?napr_id={pks}', pks));

  instance.$root.$on('print:barcodes:iss', (pks) => printForm('/barcodes/tubes?iss_ids={pks}', pks));

  instance.$root.$on('print:results', (pks) => {
    const url = `/results/preview?pk={pks}&hosp=${window.location.href.includes('/stationar') ? 1 : 0}`;
    printForm(url, pks);
  });

  instance.$root.$on('print:directions_list', (pks) => printForm('/statistic/xls?pk={pks}&type=directions_list', pks));

  instance.$root.$on('generate-directions', ({
    type,
    card_pk: cardPk,
    fin_source_pk: finSourcePk,
    diagnos,
    researches,
    operator,
    ofname,
    history_num: historyNum,
    comments,
    counts,
    for_rmis: forRmis,
    rmis_data: rmisData,
    callback,
    vich_code: vichCode,
    count,
    discount,
    need_contract: needContract,
    parent_iss: parentIss = null,
    kk = '',
    localizations = {},
    service_locations: serviceLocations = {},
    direction_purpose: directionPurpose = 'NONE',
    directions_count: directionsCount = 1,
    external_organization: externalOrganization = 'NONE',
    parent_slave_hosp: parentSlaveHosp = null,
    direction_form_params: directionFormParams = {},
    current_global_direction_params: currentGlobalDirectionParams = {},
    hospital_department_override: hospitalDepartmentOverride = -1,
  }) => {
    if (cardPk === -1) {
      window.errmessage('Не выбрана карта');
      return;
    }
    if (finSourcePk === -1) {
      window.errmessage('Не выбран источник финансирования');
      return;
    }
    if (Object.keys(researches).length === 0) {
      window.errmessage('Не выбраны исследования');
      return;
    }
    if (operator && ofname < 0) {
      window.errmessage('Не выбрано, от чьего имени выписываются направления');
      return;
    }
    instance.$store.dispatch(actions.INC_LOADING);
    directionsPoint.sendDirections({
      card_pk: cardPk,
      diagnos,
      fin_source: finSourcePk,
      history_num: historyNum,
      ofname_pk: ofname,
      researches,
      comments,
      for_rmis: forRmis,
      rmis_data: rmisData,
      vich_code: vichCode,
      count,
      discount,
      parent_iss: parentIss,
      counts,
      localizations,
      service_locations: serviceLocations,
      direction_purpose: directionPurpose,
      directions_count: directionsCount,
      external_organization: externalOrganization,
      parent_slave_hosp: parentSlaveHosp,
      direction_form_params: directionFormParams,
      current_global_direction_params: currentGlobalDirectionParams,
      hospital_department_override: hospitalDepartmentOverride,
    }).then((data) => {
      instance.$store.dispatch(actions.DEC_LOADING);

      if (data.ok) {
        if (type === 'create_and_open') {
          instance.$root.$emit('open-direction-form', data.directions[0]);

          window.okmessage('Направления создано', `Номер: ${data.directions[0]}`);
        } else if (type === 'direction') {
          if (needContract) {
            instance.$root.$emit('print:directions:contract', data.directions);
          } else {
            instance.$root.$emit('print:directions', data.directions);
          }
        } else if (type === 'barcode') {
          instance.$root.$emit('print:barcodes', data.directions, data.directionsStationar);
        } else if (type === 'just-save' || type === 'barcode') {
          window.okmessage('Направления созданы', `Номера: ${data.directions.join(', ')}`);
        }
        instance.$root.$emit(`researches-picker:clear_all${kk}`);
        instance.$root.$emit(`researches-picker:directions_created${kk}`);
      } else {
        window.errmessage('Направления не созданы', data.message);
      }
      if (callback) callback();
    });
  });
};
