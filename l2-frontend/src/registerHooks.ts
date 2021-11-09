import Vue from 'vue';

import { POSITION, TYPE } from 'vue-toastification/src/ts/constants';
import * as actions from './store/action-types';
import directionsPoint from './api/directions-point';

function printForm(tpl: string, pks: number[]) {
  if (!pks || !Array.isArray(pks) || pks.length === 0) {
    return;
  }
  window.open(tpl.replace('{pks}', JSON.stringify(pks)), '_blank');
}

export default (instance: Vue): void => {
  instance.$root.$on('no-loader-in-header', status => instance.$store.dispatch(actions.SET_LOADER_IN_HEADER, !status));

  instance.$root.$on('print:directions', pks => printForm('/directions/pdf?napr_id={pks}', pks));

  instance.$root.$on('print:hosp', pks => printForm('/barcodes/hosp?napr_id={pks}', pks));

  instance.$root.$on('print:directions:contract', pks => printForm('/directions/pdf?napr_id={pks}&contract=1', pks));

  instance.$root.$on('print:barcodes', pks => printForm('/barcodes/tubes?napr_id={pks}', pks));

  instance.$root.$on('print:barcodes:iss', pks => printForm('/barcodes/tubes?iss_ids={pks}', pks));

  instance.$root.$on('print:results', pks => {
    const url = `/results/preview?pk={pks}&hosp=${window.location.href.includes('/stationar') ? 1 : 0}`;
    printForm(url, pks);
  });

  instance.$root.$on('print:example', pks => {
    const url = '/results/preview?pk={pks}&portion=1';
    printForm(url, pks);
  });

  instance.$root.$on('print:directions_list', pks => printForm('/statistic/xls?pk={pks}&type=directions_list', pks));

  instance.$root.$on('msg', (type, message, timeout: number | void) => {
    let t = TYPE.DEFAULT;

    if (type === 'error') {
      t = TYPE.ERROR;
    } else if (type === 'ok') {
      t = TYPE.SUCCESS;
    } else if (type === 'warning') {
      t = TYPE.WARNING;
    } else if (type === 'info') {
      t = TYPE.INFO;
    }

    instance.$toast(message, {
      type: t,
      position: POSITION.BOTTOM_RIGHT,
      timeout: timeout || 6000,
      closeOnClick: false,
      pauseOnHover: true,
      icon: true,
    });
  });

  instance.$root.$on(
    'generate-directions',
    ({
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
      monitoring = false,
    }) => {
      if (cardPk === -1 && !monitoring) {
        instance.$root.$emit('msg', 'error', 'Не выбрана карта');
        return;
      }
      if (finSourcePk === -1 && !monitoring) {
        instance.$root.$emit('msg', 'error', 'Не выбран источник финансирования');
        return;
      }
      if (Object.keys(researches).length === 0) {
        instance.$root.$emit('msg', 'error', 'Не выбраны исследования');
        return;
      }
      if (operator && ofname < 0 && !monitoring) {
        instance.$root.$emit('msg', 'error', 'Не выбрано, от чьего имени выписываются направления');
        return;
      }
      instance.$store.dispatch(actions.INC_LOADING);
      directionsPoint
        .sendDirections({
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
        })
        .then(data => {
          instance.$store.dispatch(actions.DEC_LOADING);

          if (data.ok) {
            if (type === 'create_and_open') {
              instance.$root.$emit('open-direction-form', data.directions[0]);

              instance.$root.$emit('msg', 'ok', `Направление создано: ${data.directions[0]}`);
            } else if (type === 'direction') {
              if (needContract) {
                instance.$root.$emit('print:directions:contract', data.directions);
              } else {
                instance.$root.$emit('print:directions', data.directions);
              }
            } else if (type === 'barcode') {
              instance.$root.$emit('print:barcodes', data.directions, data.directionsStationar);
            } else if (type === 'just-save' || type === 'barcode') {
              instance.$root.$emit('msg', 'ok', `Направления созданы: ${data.directions.join(', ')}`);
            } else if (type === 'save-and-open-embedded-form' && monitoring) {
              instance.$root.$emit('embedded-form:open', data.directions[0]);
            }
            instance.$root.$emit(`researches-picker:clear_all${kk}`);
            instance.$root.$emit(`researches-picker:directions_created${kk}`);
          } else {
            instance.$root.$emit('msg', 'error', `Направления не созданы: ${data.message}`);
          }
          if (callback) callback();
        });
    },
  );
};
