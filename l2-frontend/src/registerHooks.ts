import Vue from 'vue';
import { POSITION, TYPE } from 'vue-toastification/src/ts/constants';

import { sendEvent } from '@/metrics';
import ChatToast from '@/ui-cards/Chat/ChatToast.vue';
import * as actions from '@/store/action-types';
import directionsPoint from '@/api/directions-point';

function printForm(tpl: string, pks: number[]) {
  if (!pks || !Array.isArray(pks) || pks.length === 0) {
    return;
  }
  window.open(tpl.replace('{pks}', JSON.stringify(pks)), '_blank');
}

export default (instance: Vue): void => {
  instance.$root.$on('no-loader-in-header', status => instance.$store.dispatch(actions.SET_LOADER_IN_HEADER, !status));

  instance.$root.$on('print:directions', pks => {
    printForm('/directions/pdf?napr_id={pks}', pks);
    sendEvent('print', {
      type: 'directions',
      pks,
    });
  });

  instance.$root.$on('print:hosp', pks => {
    printForm('/barcodes/hosp?napr_id={pks}', pks);
    sendEvent('print', {
      type: 'hosp',
      pks,
    });
  });

  instance.$root.$on('print:directions:contract', pks => {
    printForm('/directions/pdf?napr_id={pks}&contract=1', pks);
    sendEvent('print', {
      type: 'directions-contract',
      pks,
    });
  });

  instance.$root.$on('print:directions:appendix', pks => {
    printForm('/directions/pdf?napr_id={pks}&appendix=1', pks);
    sendEvent('print', {
      type: 'appendix',
      pks,
    });
  });

  instance.$root.$on('print:barcodes', pks => {
    printForm('/barcodes/tubes?napr_id={pks}', pks);
    sendEvent('print', {
      type: 'barcodes',
      pks,
    });
  });

  instance.$root.$on('print:barcodes:iss', pks => {
    printForm('/barcodes/tubes?iss_ids={pks}', pks);
    sendEvent('print', {
      type: 'barcodes:iss',
      pks,
    });
  });

  instance.$root.$on('print:results', pks => {
    const url = `/ui/results/preview?pk={pks}&hosp=${window.location.href.includes('/stationar') ? 1 : 0}&sort=${0}`;
    printForm(url, pks);
    sendEvent('print', {
      type: 'results',
      pks,
    });
  });

  instance.$root.$on('print:example', pks => {
    const url = '/ui/results/preview?pk={pks}&portion=1';
    printForm(url, pks);
    sendEvent('print', { type: 'example', pks });
  });

  instance.$root.$on('print:directions_list', pks => {
    printForm('/statistic/xls?pk={pks}&type=directions_list', pks);
    sendEvent('print', { type: 'directions_list', pks });
  });

  instance.$root.$on('msg', (type, message, timeout: number | void | null, payload: any | void) => {
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

    sendEvent('toast', {
      type,
      message,
    });

    if (type === 'message' && payload) {
      instance.$toast({
        component: ChatToast,
        props: payload,
        listeners: {
          openDialog: () => {
            instance.$store.dispatch(actions.CHATS_OPEN_DIALOG_BY_ID, { dialogId: payload.dialogId });
          },
        },
      }, {
        toastClassName: 'empty-toast',
        position: POSITION.BOTTOM_LEFT,
        timeout: timeout || 6000,
        closeOnClick: false,
        icon: false,
        closeButton: false,
        pauseOnHover: true,
        hideProgressBar: true,
      });
      return;
    }

    instance.$toast(message, {
      type: t,
      position: POSITION.BOTTOM_RIGHT,
      timeout: timeout || 6000,
      closeOnClick: false,
      pauseOnHover: true,
      pauseOnFocusLoss: false,
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
      hospital_override: hospitalOverride = -1,
      monitoring = false,
      priceCategory = null,
    }) => {
      sendEvent('generate-directions', {
        type,
        cardPk,
        finSourcePk,
        diagnos,
        researches,
        operator,
        ofname,
        historyNum,
        comments,
        counts,
        forRmis,
        rmisData,
        vichCode,
        count,
        discount,
        needContract,
        parentIss,
        kk,
        localizations,
        serviceLocations,
        directionPurpose,
        directionsCount,
        externalOrganization,
        parentSlaveHosp,
        hospitalDepartmentOverride,
        hospitalOverride,
        monitoring,
        priceCategory,
      });

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
          hospital_override: hospitalOverride,
          priceCategory,
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
            } else if (type === 'complect-document') {
              instance.$root.$emit('print:directions:appendix', data.directions);
            } else if (type === 'barcode') {
              instance.$root.$emit('msg', 'ok', `Направления созданы: ${data.directions.join(', ')}
              ${data.messageLimit}`);
              instance.$root.$emit('print:barcodes', data.directions, data.directionsStationar);
            } else if (type === 'just-save') {
              instance.$root.$emit('msg', 'ok', `Направления созданы: ${data.directions.join(', ')}
              ${data.messageLimit}`);
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
