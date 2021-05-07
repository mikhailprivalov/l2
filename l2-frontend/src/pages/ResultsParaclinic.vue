<template>
  <div ref="root" class="results-root">
    <div :class="{has_loc, opened: sidebarIsOpened || !data.ok}" class="results-sidebar">
      <div class="sidebar-top">
        <div class="input-group">
          <span class="input-group-btn" v-if="l2_microbiology">
            <label class="btn btn-blue-nb nbr height34" style="padding: 5px 11px;"
                   title="Использовать номер микробиологического анализа" v-tippy>
              <input type="checkbox" v-model="iss_search"/>
            </label>
          </span>
          <input type="text" class="form-control" v-model="pk" @keyup.enter="load" autofocus
                 :placeholder="iss_search ? 'Номер м/б анализа' : 'Номер направления'"/>
          <span class="input-group-btn">
            <button class="btn last btn-blue-nb nbr" type="button" @click="load" style="margin-right: -1px">
              Поиск
            </button>
          </span>
        </div>
      </div>
      <div class="sidebar-bottom-top">
        <span>Результаты за</span>
        <date-field-nav :brn="false" :def="date" :val.sync="date" w="100px"/>
      </div>
      <div class="directions" :class="{noStat: !stat_btn_d, has_loc, stat_btn: stat_btn_d}">
        <div class="inner">
          <div class="direction" v-for="direction in directions_history" :key="direction.pk">
            <div>
              {{direction.patient}}, {{direction.card}}
            </div>
            <div v-for="i in direction.iss" :key="`${i.title}_${i.saved}_${i.confirmed}`" class="research-row">
              <div class="row">
                <div class="col-xs-8">
                  {{i.title}}
                </div>
                <div class="col-xs-4 text-right">
                  <iss-status :i="i" short/>
                </div>
              </div>
            </div>
            <hr/>
            <template v-if="direction.amd !== 'not_need'">
              <div v-if="direction.amd === 'need'" class="amd amd-need">АМД: не отправлено</div>
              <div v-else-if="direction.amd === 'ok'" class="amd amd-ok">АМД: отправлено
                ({{direction.amd_number}})
              </div>
              <div v-else-if="direction.amd === 'error'" class="amd amd-error">АМД: ошибка</div>
              <div v-else-if="direction.amd === 'planned'" class="amd amd-planned">АМД: запланировано</div>
              <hr/>
            </template>
            <div class="row">
              <div class="col-xs-4"><a href="#" @click.prevent="load_pk(direction.pk)">Просмотр</a></div>
              <div class="col-xs-4 text-center">
                <a :href="`/forms/pdf?type=105.02&napr_id=[${direction.pk}]`"
                   target="_blank" v-if="direction.all_confirmed && stat_btn">Статталон</a>
              </div>
              <div class="col-xs-4 text-right">
                <a href="#" @click.prevent="print_results(direction.pk)" v-if="direction.all_confirmed">Печать</a>
              </div>
            </div>
          </div>
          <div class="text-center" style="margin: 5px" v-if="directions_history.length === 0">
            Нет данных
          </div>
        </div>
        <div class="rmis_loc" v-if="has_loc">
          <div class="title">
            <div class="loader" v-if="location.loading"><i class="fa fa-spinner"></i></div>
            Очередь за <input :readonly="location.loading"
                              class="inline-form"
                              required
                              type="date" v-model="td"/>
          </div>
          <div class="inner" :class="{stat_btn: stat_btn_d}">
            <table class="table table-bordered table-hover">
              <colgroup>
                <col width="38"/>
                <col/>
                <col width="16"/>
              </colgroup>
              <tbody>
              <tr v-for="r in location.data"
                  :key="`${r.slot}_${r.status && r.status.direction}`"
                  :class="{
                    current: r.slot === slot.id
                    || (data.ok && r.status.direction && r.status.direction === data.direction.pk && !slot.id)
                  }"
                  @click="r.status.code > 0 ? open_fill_slot(r.status.direction) : open_slot(r)"
                  v-tippy="{ placement : 'top', arrow: true, animation: 'fade' }"
                  :title="{
                  1: 'Направление зарегистрировано',
                  2: 'Результат подтверждён'}[r.status.code] || 'Не обработано'">
                <td>{{r.timeStart}}</td>
                <td>{{r.patient}}</td>
                <td>
                  <span class="slot"
                        :class="`slot-${r.status.code}`">
                    <i class="fa fa-circle"></i>
                  </span>
                </td>
              </tr>
              <tr v-if="!location.init">
                <td colspan="3" style="text-align: center">
                  загрузка...
                </td>
              </tr>
              <td colspan="3" style="text-align: center" v-else-if="(location.data || []).length === 0">
                нет данных на дату
              </td>
              </tbody>
            </table>
          </div>
        </div>
        <div v-if="directions_history.length > 0 && (stat_btn || amd)"
             class="side-bottom"
             :class="{
                'side-bottom_all': stat_btn && amd,
                'side-bottom_stat': stat_btn && !amd,
                'side-bottom_amd': !stat_btn && amd
             }"
        >
          <a v-if="stat_btn" class="btn btn-blue-nb"
             :href="`/forms/preview?type=105.01&date=${date_to_form}`" target="_blank">печать статталонов</a>
          <a v-if="amd" class="btn btn-blue-nb"
             href="#" @click.prevent="send_amd" target="_blank">отправить в амд</a>
        </div>
      </div>
    </div>
    <div class="burger" :class="{active: sidebarIsOpened && data.ok}"
         @click="sidebarIsOpened = !sidebarIsOpened">
      <span class="burger-inner" v-if="data.ok">
        <i class="fa fa-bars"></i>&nbsp;&nbsp;
        {{sidebarIsOpened ? 'закрыть поиск и результаты' : 'открыть поиск и результаты'}}
      </span>
      <div class="burger-lines" v-if="data.ok"/>
    </div>
    <div class="backdrop" v-if="sidebarIsOpened || !data.ok" @click="sidebarIsOpened = false">
      <div class="backdrop-inner" v-if="data.ok">
        <div>
          <div style="font-weight: bold;">Загруженное направление:</div>
          <div>
            №{{data.direction.pk}} от {{data.direction.date}}
          </div>
          <div>{{data.patient.fio_age}}</div>
          <div v-for="row in data.researches" :key="row.pk">
              Услуга: {{row.research.title}}
          </div>
        </div>
      </div>
      <div class="backdrop-inner" v-else>
        <div>направление не загружено</div>
      </div>
    </div>
    <div class="results-content" v-if="data.ok">
      <div class="results-top">
        <div class="row">
          <div class="col-xs-6">
            <div>
              Направление
              №<a href="#" class="a-under" @click.prevent="print_direction(data.direction.pk)">{{data.direction.pk}}</a>
              от
              {{data.direction.date}}
            </div>
            <div>{{data.patient.fio_age}}</div>
            <div class="text-ell" :title="data.direction.diagnos" v-if="data.direction.diagnos !== ''">Диагноз:
              {{data.direction.diagnos}}
            </div>
          </div>
          <div class="col-xs-5">
            <div v-if="!data.patient.imported_from_rmis">Источник финансирования: {{data.direction.fin_source}}</div>
            <div>Карта: {{data.patient.card}}
              <a href="#"
                 v-if="data.card_internal && data.has_doc_referral"
                 v-tippy="{ placement : 'bottom', arrow: true, reactive : true,
                   interactive : true, html: '#template-anamnesis' }"
                 @show="load_anamnesis"
                 @click.prevent="edit_anamnesis"><i class="fa fa-book"></i></a>
              <span class="visible-small">&nbsp;</span>
              <div id="template-anamnesis"
                   v-if="data.card_internal"
                   :class="{hidden: !data.ok || !data.has_doc_referral || !data.card_internal}">
                <strong>Анамнез жизни</strong><br/>
                <span v-if="anamnesis_loading">загрузка...</span>
                <pre v-else
                     style="padding: 5px;text-align: left;white-space: pre-wrap;word-break: keep-all;max-width:600px"
                >{{anamnesis_data.text || 'нет данных'}}</pre>
              </div>
              <a style="margin-left: 3px"
                 href="#"
                 v-if="data.card_internal && (data.has_doc_referral || data.has_paraclinic)"
                 v-tippy="{ placement : 'bottom', arrow: true, reactive : true,
                   interactive : true, html: '#template-dreg' }"
                 :class="{dreg_nex: !data.patient.has_dreg, dreg_ex: data.patient.has_dreg }"
                 @show="load_dreg_rows"
                 @click.prevent="dreg = true"><i class="fa fa-database"></i></a>
              <span class="visible-small">&nbsp;</span>
              <div id="template-dreg"
                   v-if="data.card_internal"
                   :class="{hidden: !data.ok || (!data.has_doc_referral && !data.has_paraclinic) || !data.card_internal}">
                <strong>Диспансерный учёт</strong><br/>
                <span v-if="dreg_rows_loading">загрузка...</span>
                <ul v-else style="padding-left: 25px;text-align: left">
                  <li v-for="r in dreg_rows" :key="r.pk">
                    {{r.diagnos}} – {{r.date_start}} <span v-if="r.illnes">– {{r.illnes}}</span>
                  </li>
                  <li v-if="dreg_rows.length === 0">нет активных записей</li>
                </ul>
              </div>
              <a style="margin-left: 3px"
                 href="#"
                 :class="{dreg_nex: !data.patient.has_benefit, dreg_ex: data.patient.has_benefit }"
                 v-if="data.card_internal && data.has_doc_referral"
                 v-tippy="{ placement : 'bottom', arrow: true, reactive : true,
                   interactive : true, html: '#template-benefit' }"
                 @show="load_benefit_rows"
                 @click.prevent="benefit = true"><i class="fa fa-cubes"></i></a>
              <span class="visible-small">&nbsp;</span>
              <div id="template-benefit" :class="{hidden: !data.ok || !data.has_doc_referral || !data.card_internal}"
                   v-if="data.card_internal">
                <strong>Льготы пациента</strong><br/>
                <span v-if="benefit_rows_loading">загрузка...</span>
                <ul v-else style="padding-left: 25px;text-align: left">
                  <li v-for="r in benefit_rows" :key="r.pk">
                    {{r.benefit}} – {{r.date_start}} – {{r.registration_basis}}
                  </li>
                  <li v-if="benefit_rows.length === 0">нет активных записей</li>
                </ul>
              </div>
              <a style="margin-left: 3px"
                 href="#"
                 :class="{[`disp_${data.status_disp}`]: true}"
                 v-if="data.card_internal && data.has_doc_referral"
                 @click.prevent
                 v-tippy="{ placement : 'bottom', arrow: true, reactive : true,
                    theme : 'light bordered',
                    html: '#template-disp',
                    interactive : true }">Д</a>
              <div id="template-disp"
                   class="disp"
                   v-if="data.card_internal && data.status_disp !== 'notneed' && data.has_doc_referral">
                <strong>Диспансеризация</strong><br/>
                <ul style="padding-left: 25px;text-align: left">
                  <li v-for="d in data.disp_data" :key="`${d[0]}_${d[5]}`">
                      <span :class="{disp_row: true, [!!d[2] ? 'disp_row_finished' : 'disp_row_need']: true}">
                        <span v-if="!d[2]">требуется</span>
                        <a v-else href="#" @click.prevent="show_results([d[2]])" class="not-black">
                          пройдено
                        </a>
                      </span>

                    <a href="#" @click.prevent="add_researches(data.researches[0], [d[0]])">
                      {{d[5]}}
                    </a>
                  </li>
                </ul>
                <div>
                  <a href="#"
                     class="btn btn-blue-nb"
                     v-if="data.status_disp === 'need'"
                     @click.prevent="add_researches(data.researches[0], data.disp_data.filter(d => !d[2]).map(d => d[0]))">
                    Выбрать требуемые
                  </a>
                  <a href="#"
                     class="btn btn-blue-nb"
                     v-else
                     @click.prevent="show_results(data.disp_data.map(d => d[2]))">
                    Печать всех результатов
                  </a>
                </div>
              </div>
              <medical-certificates :med_certificates="data.medical_certificates" :direction="data.direction.pk"/>
              <rmis-link :is-schedule="false"/>
              <ResultsByYear :card_pk="data.patient.card_pk" isDocReferral/>
              <ResultsByYear :card_pk="data.patient.card_pk" isParaclinic/>
              <ResultsByYear :card_pk="data.patient.card_pk" isLab/>
            </div>
            <div class="text-ell" :title="data.patient.doc" v-if="!data.patient.imported_from_rmis">Лечащий врач:
              {{data.patient.doc}}
            </div>
            <div v-else>Организация: {{data.patient.imported_org}}</div>
          </div>
          <div class="col-xs-1">
            <button type="button" class="close" @click="clear()">
              <span>&times;</span>
            </button>
          </div>
        </div>
      </div>
      <div class="results-editor">
        <div v-for="row in data.researches" :key="row.pk">
          <div class="research-title">
            <div class="research-left">
              {{row.research.title}}
              <span class="comment" v-if="row.research.comment"> [{{row.research.comment}}]</span>
              <dropdown :visible="research_open_history === row.pk"
                        :position='["left", "bottom", "left", "top"]'
                        v-if="!data.has_microbiology"
                        @clickout="hide_results">
                <a style="font-weight: normal"
                   href="#" @click.prevent="open_results(row.pk)">
                  (другие результаты)
                </a>
                <div class="results-history" slot="dropdown">
                  <ul>
                    <li v-for="r in research_history" :key="r.pk">
                      Результат от {{r.date}}
                      <a href="#" @click.prevent="print_results(r.direction)">печать</a>
                      <a href="#" @click.prevent="copy_results(row, r.pk)" v-if="!row.confirmed">скопировать</a>
                    </li>
                    <li v-if="research_history.length === 0">результатов не найдено</li>
                  </ul>
                </div>
              </dropdown>
            </div>
            <div class="research-right">
              <template v-if="data.direction.all_confirmed">
                <a :href="`/forms/pdf?type=105.02&napr_id=[${data.direction.pk}]`"
                   class="btn btn-blue-nb" target="_blank" v-if="stat_btn">Статталон</a>
                <a href="#" class="btn btn-blue-nb"
                   @click.prevent="print_results(data.direction.pk)">Печать</a>
              </template>
              <template v-if="!data.has_microbiology">
                <a :href="row.pacs" class="btn btn-blue-nb" v-if="!!row.pacs"
                   target="_blank"
                   title="Снимок" v-tippy>
                  &nbsp;<i class="fa fa-camera"></i>&nbsp;
                </a>
                <template v-if="!row.confirmed">
                  <button class="btn btn-blue-nb" @click="save(row)" v-if="!row.confirmed"
                          title="Сохранить без подтверждения" v-tippy>
                    &nbsp;<i class="fa fa-save"></i>&nbsp;
                  </button>
                  <button class="btn btn-blue-nb" @click="clear_vals(row)" title="Очистить протокол" v-tippy>
                    &nbsp;<i class="fa fa-times"></i>&nbsp;
                  </button>
                  <div class="right-f" v-if="fte">
                    <select-picker-m v-model="templates[row.pk]"
                                     :search="true"
                                     :options="row.templates.map(x => ({label: x.title, value: x.pk}))"/>
                  </div>
                  <button class="btn btn-blue-nb" @click="load_template(row, templates[row.pk])" v-if="fte">
                    Загрузить шаблон
                  </button>
                </template>
              </template>
            </div>
          </div>
          <DescriptiveForm
            :research="row.research"
            :confirmed="row.confirmed"
            :patient="data.patient"
            :change_mkb="change_mkb(row)"
          />
          <div class="group" v-if="!data.has_microbiology && (!row.confirmed || row.more.length > 0)">
            <div class="group-title">Дополнительные услуги</div>
            <div class="row">
              <div class="col-xs-6"
                   v-if="!row.confirmed"
                   style="height: 200px;border-right: 1px solid #eaeaea;padding-right: 0;">
                <researches-picker v-model="row.more" :hidetemplates="true"
                                   :readonly="row.confirmed"
                                   :just_search="true"
                                   :filter_types="[2, 7]"/>
              </div>
              <div :class="row.confirmed ? 'col-xs-12' : 'col-xs-6'"
                   :style="'height: 200px;' + (row.confirmed ? '' : 'padding-left: 0')">
                <selected-researches :researches="row.more"
                                     :readonly="row.confirmed" :simple="true"/>
              </div>
            </div>
          </div>
          <template v-if="data.has_microbiology">
            <div class="group" v-if="row.tube">
              <div class="fields">
                <div class="field">
                  <div class="field-title" style="flex: 1 0 120px">
                    Номер анализа
                  </div>
                  <div class="field-value" style="padding: 3px">
                    <span class="tube-pk">{{row.tube.pk}}</span>
                  </div>
                </div>
                <div class="field">
                  <div class="field-title" style="flex: 1 0 120px">
                    Ёмкость
                  </div>
                  <div class="field-value" style="padding: 3px">
                    <span
                      :style="{
                      width: '10px',
                      height: '10px',
                      background: row.tube.color,
                      border: '1px solid #aaa',
                      display: 'inline-block' }"></span>
                    {{row.tube.type}}, дата забора {{row.tube.get}}
                    <a href="#" class="a-under" @click.prevent="print_tube_iss(row.tube.pk)">печать ш/к</a>
                  </div>
                </div>
              </div>
            </div>
            <BacMicroForm
              :confirmed="row.confirmed"
              v-model="row.microbiology.bacteries"
              :cultureCommentsTemplates="row.microbiology.cultureCommentsTemplates"
            />
            <div class="group">
              <div class="group-title">Заключение</div>
              <div class="fields">
                <div :class="{disabled: row.confirmed}"
                 v-on="{
                  mouseenter: enter_field(row.microbiology.conclusionTemplates.length > 0),
                  mouseleave: leave_field(row.microbiology.conclusionTemplates.length > 0),
                 }" class="field">
                    <FastTemplates
                      :update_value="updateValue(row.microbiology, 'conclusion')"
                      :value="row.microbiology.conclusion || ''"
                      :values="row.microbiology.conclusionTemplates"
                      :confirmed="row.confirmed"
                    />
                    <div class="field-value">
                      <textarea rows="5" class="form-control"
                                :readonly="row.confirmed" v-model="row.microbiology.conclusion"
                      />
                    </div>
                </div>
              </div>
            </div>
          </template>
          <div class="group" v-if="row.research.is_doc_refferal && row.recipe">
            <div class="group-title">Рецепты</div>
            <div class="row">
              <div class="col-xs-12">
                <div class="sd">
                  <recipe-input v-model="row.recipe" :pk="row.pk" :confirmed="row.confirmed"/>
                </div>
              </div>
            </div>
          </div>
          <div class="group" v-if="row.research.is_doc_refferal">
            <div class="group-title">Направления в рамках приёма</div>
            <div class="row">
              <div class="col-xs-12">
                <div class="sd">
                  <directions-history :iss_pk="row.pk" kk="cd"/>
                </div>
                <div class="sd empty" v-if="!row.confirmed">
                  <button @click="create_directions(row)"
                          class="btn btn-primary-nb btn-blue-nb" type="button">
                    <i class="fa fa-plus"></i> создать направления
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="group" v-if="row.research.is_doc_refferal && stat_btn">
            <div class="group-title">Данные статталона</div>
            <div class="fields">
              <div class="field">
                <div class="field-title">
                  Цель посещения
                </div>
                <div class="field-value">
                  <select v-model="row.purpose" :disabled="row.confirmed">
                    <option v-for="o in row.purpose_list" :value="o.pk" :key="o.pk">
                      {{o.title}}
                    </option>
                  </select>
                </div>
              </div>
              <div class="field">
                <label class="field-title" for="first-time">
                  Впервые
                </label>
                <div class="field-value">
                  <input type="checkbox" id="first-time" v-model="row.first_time" :disabled="row.confirmed"/>
                </div>
              </div>
              <div class="field">
                <div class="field-title">
                  Результат обращения
                </div>
                <div class="field-value">
                  <select v-model="row.result" :disabled="row.confirmed">
                    <option v-for="o in row.result_list" :value="o.pk" :key="o.pk">
                      {{o.title}}
                    </option>
                  </select>
                </div>
              </div>
              <div class="field">
                <div class="field-title">
                  Исход
                </div>
                <div class="field-value">
                  <select v-model="row.outcome" :disabled="row.confirmed">
                    <option v-for="o in row.outcome_list" :value="o.pk" :key="o.pk">
                      {{o.title}}
                    </option>
                  </select>
                </div>
              </div>
              <div class="field">
                <div class="field-title">
                  Заключительный диагноз
                </div>
                <div class="field-value mkb10" v-if="!row.confirmed">
                  <m-k-b-field v-model="row.diagnos"/>
                </div>
                <div class="field-value" v-else>
                  <input v-model="row.diagnos" class="form-control" :readonly="true"/>
                </div>
              </div>
              <div class="field" v-if="row.research.is_doc_refferal">
                <div class="field-title">
                  Дата осмотра
                </div>
                <label class="field-value">
                  <input :max="tdm()" :min="td_m_year" :readonly="row.confirmed" class="form-control"
                         required style="width: 160px" type="date" v-model="row.examination_date"/>
                </label>
              </div>
              <div class="field">
                <div class="field-title">
                  Место оказания
                </div>
                <div class="field-value">
                  <select v-model="row.place" :disabled="row.confirmed">
                    <option v-for="o in row.place_list" :value="o.pk" :key="o.pk">
                      {{o.title}}
                    </option>
                  </select>
                </div>
              </div>
              <div class="field">
                <div class="field-title">
                  Источник финансирования
                </div>
                <div class="field-value">
                  <select v-model="row.fin_source" :disabled="row.confirmed">
                    <option v-for="o in row.fin_source_list" :value="o.pk" :key="o.pk">
                      {{o.title}}
                    </option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          <div class="group" v-if="!data.has_microbiology">
            <div class="fields">
              <div class="field">
                <label class="field-title" for="onco">
                  Подозрение на онко
                </label>
                <div class="field-value">
                  <input type="checkbox" id="onco" v-model="row.maybe_onco" :disabled="row.confirmed"/>
                </div>
              </div>
            </div>
          </div>
          <div class="control-row">
            <div class="res-title">{{row.research.title}}:</div>
            <iss-status :i="row"/>
            <button class="btn btn-blue-nb" @click="save(row)" v-if="!row.confirmed">Сохранить</button>
            <button class="btn btn-blue-nb" @click="save_and_confirm(row)" v-if="!row.confirmed && can_confirm"
                    :disabled="!r(row)">
              Сохранить и подтвердить
            </button>
            <button class="btn btn-blue-nb" @click="reset_confirm(row)"
                    v-if="row.confirmed && row.allow_reset_confirm && can_confirm">
              Сброс подтверждения
            </button>
            <template v-if="amd">
              <div class="amd amd-planned" v-if="data.direction.amd === 'planned'">АМД: запланировано</div>
              <div class="amd amd-error" v-if="data.direction.amd === 'error' && row.confirmed">АМД: ошибка</div>
              <div class="amd amd-need" v-if="data.direction.amd === 'need' && row.confirmed">АМД: не отправлено</div>
              <div class="amd amd-ok" v-if="data.direction.amd === 'ok'">АМД: отправлено
                ({{data.direction.amd_number}})
              </div>
              <button class="btn btn-blue-nb" @click="reset_amd([data.direction.pk])"
                      v-if="can_reset_amd && data.direction.amd !== 'not_need' && data.direction.amd !== 'need'">
                Сброс статуса АМД
              </button>
              <button class="btn btn-blue-nb" @click="send_to_amd([data.direction.pk])"
                      v-if="data.direction.amd === 'need' || data.direction.amd === 'error'">
                Отправить в АМД
              </button>
            </template>
            <div class="status-list" v-if="!r(row) && !row.confirmed">
              <div class="status status-none">Не заполнено:</div>
              <div class="status status-none" v-for="rl in r_list(row)" :key="rl">{{rl}};</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="results-content" v-else></div>
    <modal v-if="anamnesis_edit" ref="modalAnamnesisEdit" @close="hide_modal_anamnesis_edit" show-footer="true"
           white-bg="true" max-width="710px" width="100%" marginLeftRight="auto" margin-top>
      <span slot="header">Редактор анамнеза жизни – карта {{data.patient.card}}, {{data.patient.fio_age}}</span>
      <div slot="body" style="min-height: 140px" class="registry-body">
          <textarea v-model="anamnesis_data.text" rows="14" class="form-control"
                    placeholder="Анамнез жизни"></textarea>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="hide_modal_anamnesis_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
              Отмена
            </button>
          </div>
          <div class="col-xs-4">
            <button @click="save_anamnesis()" class="btn btn-primary-nb btn-blue-nb" type="button">
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </modal>
    <modal @close="hide_modal_create_directions" margin-top marginLeftRight="auto"
           max-width="1400px" ref="modalCD" show-footer="true" v-if="create_directions_for > -1" white-bg="true"
           width="100%">
      <span slot="header">Создание направлений – карта {{data.patient.card}}, {{data.patient.fio_age}}</span>
      <div class="registry-body" slot="body" style="min-height: 140px">
        <div class="row">
          <div class="col-xs-6"
               style="height: 450px;border-right: 1px solid #eaeaea;padding-right: 0;">
            <researches-picker v-model="create_directions_data"
                               kk="cd" style="border-top: 1px solid #eaeaea;border-bottom: 1px solid #eaeaea;"
                               :filter_types="[7]" />
          </div>
          <div class="col-xs-6" style="height: 450px;padding-left: 0;">
            <selected-researches
              kk="cd"
              :base="bases_obj[data.patient.base]"
              :researches="create_directions_data"
              :main_diagnosis="create_directions_diagnosis"
              :valid="true"
              :card_pk="data.patient.card_pk"
              :initial_fin="data.direction.fin_source_id"
              :parent_iss="create_directions_for"
              :clear_after_gen="true"
              style="border-top: 1px solid #eaeaea;border-bottom: 1px solid #eaeaea;"
            />
          </div>
        </div>
        <div v-if="create_directions_data.length > 0"
             style="margin-top: 5px;text-align: left">
          <table class="table table-bordered lastresults">
            <colgroup>
              <col width="180">
              <col>
              <col width="110">
              <col width="110">
            </colgroup>
            <tbody>
            <last-result :individual="data.patient.individual_pk" :key="p" v-for="p in create_directions_data"
                         :noScroll="true"
                         :research="p"/>
            </tbody>
          </table>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="hide_modal_create_directions" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </modal>
    <modal v-if="!!slot.id" ref="modalSlot" @close="close_slot"
           margin-top="50px"
           show-footer="true" white-bg="true" max-width="710px" width="100%" marginLeftRight="auto">
      <span slot="header">Слот {{slot.id}}</span>
      <div slot="body" style="min-height: 200px;background-color: #fff" class="registry-body">
        <div class="text-center" v-if="Object.keys(slot.data).length === 0">загрузка...</div>
        <div class="text-left" v-else>
          <h3 style="margin-top: 0;">Талон № {{slot.data.pk}}</h3>
          <h5>{{slot.data.datetime}}</h5>
          РМИС UID пациента: <a :href="`/mainmenu/directions?rmis_uid=${slot.data.patient_uid}`"
                                target="_blank">{{slot.data.patient_uid}}</a><br/>
          <div v-if="!slot.data.direction">Нет связанного назначения. Выберите ниже:</div>
          <div v-else>Выбранное назначение для талона:</div>
          <div class="content-picker">
            <research-pick :class="{ active: row.pk === slot.data.direction_service }" :research="row"
                           @click.native="select_research(row.pk)"
                           class="research-select"
                           v-for="row in userServicesFiltered"
                           :key="row.pk" />
            <div v-if="userServicesFiltered.length === 0">нет данных</div>
          </div>
          <div class="text-center" style="margin-top: 10px;">
            <button @click="fill_slot"
                    :disabled="slot.data.direction_service === -1"
                    v-if="!slot.data.direction"
                    class="btn btn-primary-nb btn-blue-nb" type="button">
              Сохранить назначение и заполнить протокол
            </button>
            <button @click="open_fill_slot(slot.data.direction)" v-else class="btn btn-primary-nb btn-blue-nb"
                    type="button">
              Перейти к протоколу
            </button>
          </div>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="close_slot" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </modal>
    <d-reg :card_pk="data.patient.card_pk" :card_data="data.patient" v-if="dreg"/>
    <benefit :card_pk="data.patient.card_pk" :card_data="data.patient" v-if="benefit" :readonly="true"/>
    <results-viewer :pk="show_results_pk" v-if="show_results_pk > -1"/>
  </div>
</template>

<script>
import moment from 'moment';
import dropdown from 'vue-my-dropdown';
import { mapGetters } from 'vuex';
import { vField, vGroup } from '@/components/visibility-triggers';
import { enter_field, leave_field } from '@/forms/utils';
import api from '@/api';
import ResultsByYear from '@/ui-cards/PatientResults/ResultsByYear.vue';
import RmisLink from '@/ui-cards/RmisLink.vue';
import patientsPoint from '../api/patients-point';
import * as actions from '../store/action-types';
import directionsPoint from '../api/directions-point';
import SelectPickerM from '../fields/SelectPickerM.vue';
import researchesPoint from '../api/researches-point';
import Modal from '../ui-cards/Modal.vue';
import MKBField from '../fields/MKBField.vue';
import DateFieldNav from '../fields/DateFieldNav.vue';
import DReg from '../modals/DReg.vue';
import ResearchesPicker from '../ui-cards/ResearchesPicker.vue';
import SelectedResearches from '../ui-cards/SelectedResearches.vue';
import usersPoint from '../api/user-point';
import ResearchPick from '../ui-cards/ResearchPick.vue';
import Benefit from '../modals/Benefit.vue';
import DirectionsHistory from '../ui-cards/DirectionsHistory/index.vue';
import RecipeInput from '../ui-cards/RecipeInput.vue';
import ResultsViewer from '../modals/ResultsViewer.vue';
import LastResult from '../ui-cards/LastResult.vue';
import IssStatus from '../ui-cards/IssStatus.vue';
import DescriptiveForm from '../forms/DescriptiveForm.vue';
import BacMicroForm from '../forms/BacMicroForm.vue';
import UrlData from '../UrlData';
import MedicalCertificates from '../ui-cards/MedicalCertificates.vue';
import FastTemplates from '../forms/FastTemplates.vue';

export default {
  name: 'results-paraclinic',
  components: {
    FastTemplates,
    BacMicroForm,
    DescriptiveForm,
    DateFieldNav,
    Modal,
    MKBField,
    ResearchesPicker,
    SelectedResearches,
    dropdown,
    SelectPickerM,
    DReg,
    ResearchPick,
    Benefit,
    DirectionsHistory,
    ResultsViewer,
    LastResult,
    RecipeInput,
    IssStatus,
    MedicalCertificates,
    ResultsByYear,
    RmisLink,
  },
  data() {
    return {
      pk: '',
      iss_search: false,
      data: { ok: false, direction: {} },
      date: moment().format('DD.MM.YYYY'),
      td: moment().format('YYYY-MM-DD'),
      tnd: moment().add(1, 'day').format('YYYY-MM-DD'),
      td_m_year: moment().subtract(1, 'year').format('YYYY-MM-DD'),
      directions_history: [],
      prev_scroll: 0,
      prev_scrollHeightTop: 0,
      changed: false,
      inserted: false,
      anamnesis_edit: false,
      anamnesis_data: {
        text: '',
      },
      anamnesis_loading: false,
      new_anamnesis: null,
      research_open_history: null,
      research_history: [],
      templates: {},
      benefit: false,
      benefit_rows_loading: false,
      benefit_rows: [],
      dreg: false,
      dreg_rows_loading: false,
      dreg_rows: [],
      location: {
        loading: false,
        init: false,
        data: [],
      },
      slot: {
        id: null,
        data: {},
      },
      create_directions_for: -1,
      create_directions_data: [],
      create_directions_diagnosis: '',
      show_results_pk: -1,
      loc_timer: null,
      inited: false,
      medical_certificatesicates_rows: [],
      sidebarIsOpened: false,
    };
  },
  watch: {
    date() {
      this.load_history();
    },
    user_data: {
      async handler({ rmis_location }) {
        if (!this.location.init && rmis_location) {
          await this.load_location();
          this.location.init = true;
        }
      },
      immediate: true,
    },
    has_loc: {
      async handler(h) {
        if (h) {
          await this.$store.dispatch(actions.INC_LOADING);
          await this.$store.dispatch(actions.GET_RESEARCHES);
          await this.$store.dispatch(actions.DEC_LOADING);
        }
      },
      immediate: true,
    },
    td: {
      handler() {
        this.load_location();
      },
    },
    navState() {
      if (this.inited) {
        UrlData.set(this.navState);
      }

      UrlData.title(this.data.ok ? this.data.direction.pk : null);
    },
  },
  mounted() {
    window.$(window).on('beforeunload', () => {
      if (this.has_changed) {
        return 'Возможно имеются несохраненные изменения! Вы уверены, что хотите покинуть страницу?';
      }

      return undefined;
    });
    this.load_history();
    this.$root.$on('hide_dreg', () => {
      this.load_dreg_rows();
      this.dreg = false;
    });
    this.$root.$on('hide_benefit', () => {
      this.load_benefit_rows();
      this.benefit = false;
    });

    this.$root.$on('show_results', (pk) => {
      this.show_results_pk = pk;
    });

    this.$root.$on('hide_results', () => {
      this.show_results_pk = -1;
    });

    const storedData = UrlData.get();
    if (storedData && typeof storedData === 'object' && storedData.pk) {
      this.load_pk(storedData.pk).then(() => {
        this.inited = true;
      });
    } else {
      this.inited = true;
    }

    this.$root.$on('open-direction-form', (pk) => this.load_pk(pk));
  },
  methods: {
    async load_location() {
      if (!this.has_loc) {
        return;
      }
      if (!this.loc_timer) {
        this.loc_timer = setInterval(() => this.load_location(), 120000);
      }
      this.location.loading = true;
      try {
        this.location.data = (await usersPoint.loadLocation({ date: this.td }).catch((e) => {
          console.error(e);
          return { data: [] };
        })).data;
      } catch (e) {
        console.error(e);
        this.location.data = [];
      }
      this.location.loading = false;
    },
    tdm() {
      return moment().add(1, 'day').format('YYYY-MM-DD');
    },
    print_tube_iss(pk) {
      this.$root.$emit('print:barcodes:iss', [pk]);
    },
    async load_dreg_rows() {
      this.dreg_rows_loading = true;
      this.dreg_rows = (
        await api('patients/individuals/load-dreg', this.data.patient, 'card_pk')
      ).rows.filter((r) => !r.date_end);
      this.data.patient.has_dreg = this.dreg_rows.length > 0;
      this.dreg_rows_loading = false;
    },
    async load_benefit_rows() {
      this.benefit_rows_loading = true;
      this.benefit_rows = (await patientsPoint.loadBenefit(this.data.patient, 'card_pk')).rows.filter((r) => !r.date_end);
      this.data.patient.has_benefit = this.benefit_rows.length > 0;
      this.benefit_rows_loading = false;
    },
    async load_anamnesis() {
      this.anamnesis_loading = true;
      this.anamnesis_data = await patientsPoint.loadAnamnesis(this.data.patient, 'card_pk');
      this.anamnesis_loading = false;
    },
    change_mkb(row) {
      return (field) => {
        if (field.value && !row.confirmed && row.research.is_doc_refferal && this.stat_btn) {
          const ndiagnos = field.value.split(' ')[0] || '';
          if (ndiagnos !== row.diagnos && ndiagnos.match(/^[A-Z]\d{1,2}(\.\d{1,2})?$/gm)) {
            window.okmessage('Диагноз в данных статталона обновлён', ndiagnos);
            // eslint-disable-next-line no-param-reassign
            row.diagnos = ndiagnos;
          }
        }
      };
    },
    open_results(pk) {
      if (this.research_open_history) {
        this.hide_results();
        return;
      }
      this.$store.dispatch(actions.INC_LOADING);
      this.research_history = [];
      directionsPoint.paraclinicResultPatientHistory({ pk }).then(({ data }) => {
        this.research_history = data;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.research_open_history = pk;
      });
    },
    hide_results() {
      this.research_history = [];
      this.research_open_history = null;
    },
    r(research) {
      return this.r_list(research).length === 0;
    },
    r_list(research) {
      const l = [];
      if (research.confirmed) {
        return [];
      }

      for (const g of research.research.groups) {
        if (!vGroup(g, research.research.groups, this.data.patient)) {
          continue;
        }
        let n = 0;
        for (const f of g.fields) {
          n++;
          if (f.required && (f.value === '' || f.value === '- Не выбрано' || !f.value)
              && (vField(g, research.research.groups, f.visibility, this.data.patient))) {
            l.push((g.title !== '' ? `${g.title} ` : '') + (f.title === '' ? `поле ${n}` : f.title));
          }
        }
      }
      return l.slice(0, 2);
    },
    hide_modal_anamnesis_edit() {
      if (this.$refs.modalAnamnesisEdit) {
        this.$refs.modalAnamnesisEdit.$el.style.display = 'none';
      }
      this.anamnesis_edit = false;
    },
    save_anamnesis() {
      this.$store.dispatch(actions.INC_LOADING);
      patientsPoint.saveAnamnesis(this.data.patient, 'card_pk', { text: this.anamnesis_data.text }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.new_anamnesis = this.anamnesis_data.text;
        this.hide_modal_anamnesis_edit();
      });
    },
    edit_anamnesis() {
      this.$store.dispatch(actions.INC_LOADING);
      patientsPoint.loadAnamnesis(this.data.patient, 'card_pk').then((data) => {
        this.anamnesis_data = data;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.anamnesis_edit = true;
      });
    },
    load_history() {
      this.directions_history = [];
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint.paraclinicResultUserHistory(this, 'date').then((data) => {
        this.directions_history = data.directions;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    reload_if_need() {
      if (this.date === moment().format('DD.MM.YYYY')) {
        this.load_history();
      }
    },
    load_pk(pk) {
      this.pk = `${pk}`;
      return this.load();
    },
    async load() {
      if (
        this.has_changed
        // eslint-disable-next-line no-alert,no-restricted-globals
        && !confirm('Возможно имеются несохраненные изменения! Вы действительно хотите закрыть текущий протокол?')
      ) {
        return;
      }
      this.clear(true);
      this.$store.dispatch(actions.INC_LOADING);
      await directionsPoint.getParaclinicForm({ pk: this.pk_c, byIssledovaniye: this.iss_search }).then((data) => {
        if (data.ok) {
          this.tnd = moment().add(1, 'day').format('YYYY-MM-DD');
          this.td_m_year = moment().subtract(1, 'year').format('YYYY-MM-DD');
          this.dreg_rows_loading = false;
          this.benefit_rows_loading = false;
          this.dreg_rows = [];
          this.benefit_rows = [];
          this.pk = '';
          this.data = data;
          this.sidebarIsOpened = false;
          setTimeout(
            () => this.$root.$emit(
              'preselect-args', { card_pk: data.patient.card_pk, base_pk: data.patient.base },
            ),
            300,
          );
          if (data.card_internal && data.status_disp === 'need' && data.has_doc_referral) {
            window.errmessage('Диспансеризация не пройдена');
          }
          this.changed = false;
        } else {
          window.errmessage(data.message);
        }
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    hide_modal_create_directions() {
      if (this.$refs.modalCD) {
        this.$refs.modalCD.$el.style.display = 'none';
      }
      this.create_directions_for = -1;
      this.create_directions_data = [];
      this.create_directions_diagnosis = '';
    },
    create_directions(iss) {
      this.create_directions_diagnosis = iss.diagnos;
      this.create_directions_for = iss.pk;
    },
    visibility_state(iss) {
      const groups = {};
      const fields = {};
      const { groups: igroups } = iss.research;
      for (const group of iss.research.groups) {
        if (!vGroup(group, igroups, this.data.patient)) {
          groups[group.pk] = false;
        } else {
          groups[group.pk] = true;
          for (const field of group.fields) {
            fields[field.pk] = vField(group, igroups, field.visibility, this.data.patient);
          }
        }
      }

      return {
        groups,
        fields,
      };
    },
    save(iss) {
      this.hide_results();
      this.inserted = false;
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint.paraclinicResultSave({
        data: {
          ...iss,
          direction: this.data.direction,
        },
        with_confirm: false,
        visibility_state: this.visibility_state(iss),
      }).then((data) => {
        if (data.ok) {
          window.okmessage('Сохранено');
          // eslint-disable-next-line no-param-reassign
          iss.saved = true;
          this.data.direction.amd = data.amd;
          this.data.direction.amd_number = data.amd_number;
          this.reload_if_need();
          this.changed = false;
        } else {
          window.errmessage(data.message);
        }
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.inserted = true;
        this.load_location();
      });
    },
    save_and_confirm(iss) {
      this.hide_results();
      this.inserted = false;
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint.paraclinicResultSave({
        data: {
          ...iss,
          direction: this.data.direction,
        },
        with_confirm: true,
        visibility_state: this.visibility_state(iss),
      }).then((data) => {
        if (data.ok) {
          window.okmessage('Сохранено');
          window.okmessage('Подтверждено');
          // eslint-disable-next-line no-param-reassign
          iss.saved = true;
          // eslint-disable-next-line no-param-reassign
          iss.allow_reset_confirm = true;
          // eslint-disable-next-line no-param-reassign
          iss.confirmed = true;
          this.data.direction.amd = data.amd;
          this.data.direction.amd_number = data.amd_number;
          this.data.direction.all_confirmed = this.data.researches.every((r) => Boolean(r.confirmed));
          this.reload_if_need();
          this.changed = false;
        } else {
          window.errmessage(data.message);
        }
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.inserted = true;
        this.load_location();
      });
    },
    confirm(iss) {
      this.hide_results();
      this.inserted = false;
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint.paraclinicResultConfirm({ iss_pk: iss.pk }).then((data) => {
        if (data.ok) {
          window.okmessage('Подтверждено');
          // eslint-disable-next-line no-param-reassign
          iss.confirmed = true;
          // eslint-disable-next-line no-param-reassign
          iss.allow_reset_confirm = true;
          this.data.direction.amd = data.amd;
          this.data.direction.amd_number = data.amd_number;
          this.data.direction.all_confirmed = this.data.researches.every((r) => Boolean(r.confirmed));
          this.reload_if_need();
          this.changed = false;
        } else {
          window.errmessage(data.message);
        }
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.inserted = true;
        this.load_location();
      });
    },
    async reset_confirm(iss) {
      this.hide_results();

      try {
        await this.$dialog.confirm(`Подтвердите сброс подтверждения услуги «${iss.research.title}»`);
      } catch (_) {
        return;
      }

      this.inserted = false;
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await directionsPoint.paraclinicResultConfirmReset({ iss_pk: iss.pk });
      if (data.ok) {
        window.okmessage('Подтверждение сброшено');
        // eslint-disable-next-line no-param-reassign
        iss.confirmed = false;
        this.data.direction.amd = 'not_need';
        this.data.direction.all_confirmed = this.data.researches.every((r) => Boolean(r.confirmed));
        this.reload_if_need();
        this.changed = false;
      } else {
        window.errmessage(data.message);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
      this.inserted = true;
      this.load_location();
    },
    clear(ignoreOrig) {
      const ignore = ignoreOrig || false;
      if (
        !ignore
        && this.has_changed
        // eslint-disable-next-line no-alert,no-restricted-globals
        && !confirm('Возможно имеются несохраненные изменения! Вы действительно хотите закрыть текущий протокол?')
      ) {
        return;
      }

      this.inserted = false;
      this.changed = false;
      this.anamnesis_edit = false;
      this.new_anamnesis = null;
      this.data = { ok: false };
      this.research_open_history = null;
      this.dreg_rows_loading = false;
      this.dreg_rows = [];
      this.benefit_rows_loading = false;
      this.benefit_rows = [];
      this.$root.$emit('preselect-card', null);
    },
    print_direction(pk) {
      this.$root.$emit('print:directions', [pk]);
    },
    print_results(pk) {
      this.$root.$emit('print:results', [pk]);
    },
    copy_results(row, pk) {
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint.paraclinicDataByFields({ pk, pk_dest: row.pk }).then(({ data }) => {
        this.hide_results();
        this.replace_fields_values(row, data);
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    load_template(row, pk) {
      this.$store.dispatch(actions.INC_LOADING);
      researchesPoint.getTemplateData({ pk: parseInt(pk, 10) }).then(({ data: { fields: data, title } }) => {
        this.template_fields_values(row, data, title);
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    async open_slot(row) {
      await this.$store.dispatch(actions.INC_LOADING);
      this.slot.id = row.slot;
      this.slot.data = await usersPoint.getReserve({ pk: row.slot, patient: row.uid });
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async close_slot() {
      if (!this.$refs.modalSlot) {
        return;
      }
      this.$refs.modalSlot.$el.style.display = 'none';
      this.slot.id = null;
      this.slot.data = {};
    },
    async fill_slot() {
      let s = '';
      for (const r of this.user_services) {
        if (r.pk === this.slot.data.direction_service) {
          s = r.title;
          break;
        }
      }
      try {
        await this.$dialog.confirm(`Подтвердите назначение услуги ${s}`);
        await this.$store.dispatch(actions.INC_LOADING);
        const cards = await patientsPoint.searchCard({
          type: this.internal_base,
          query: this.slot.data.patient_uid,
          list_all_cards: false,
          inc_rmis: true,
        });
        const card_pk = (cards.results || [{}])[0].pk;
        const { direction } = await usersPoint.fillSlot({ slot: { ...this.slot, card_pk } });
        await this.$store.dispatch(actions.DEC_LOADING);
        this.load_location();
        this.open_fill_slot(direction);
      } catch (_) {
        await this.$store.dispatch(actions.DEC_LOADING);
      }
    },
    open_fill_slot(direction) {
      this.close_slot();
      this.load_pk(direction);
    },
    template_fields_values(row, dataTemplate, title) {
      this.$dialog.alert(title, {
        view: 'replace-append-modal',
      }).then(({ data }) => {
        if (data === 'append') {
          this.append_fields_values(row, dataTemplate);
        } else {
          this.replace_fields_values(row, dataTemplate);
        }
      });
    },
    replace_fields_values(row, data) {
      for (const g of row.research.groups) {
        for (const f of g.fields) {
          if (![1, 3, 16, 17, 20, 13, 14, 11].includes(f.field_type)) {
            f.value = data[f.pk] || '';
          }
        }
      }
    },
    append_fields_values(row, data) {
      for (const g of row.research.groups) {
        for (const f of g.fields) {
          if (![1, 3, 16, 17, 20, 13, 14, 11].includes(f.field_type) && data[f.pk]) {
            this.append_value(f, data[f.pk]);
          }
        }
      }
    },
    clear_vals(row) {
      this.$dialog
        .confirm('Вы действительно хотите очистить результаты?')
        .then(() => {
          window.okmessage('Очищено');
          for (const g of row.research.groups) {
            for (const f of g.fields) {
              if (![1, 3, 16, 17, 20, 13, 14, 11, 23].includes(f.field_type)) {
                this.clear_val(f);
              }
            }
          }
        });
    },
    clear_val(field) {
      // eslint-disable-next-line no-param-reassign
      field.value = '';
    },
    append_value(field, value) {
      let add_val = value;
      if (add_val !== ',' && add_val !== '.') {
        if (
          field.value.length > 0
          && field.value[field.value.length - 1] !== ' '
          && field.value[field.value.length - 1] !== '\n'
        ) {
          if (field.value[field.value.length - 1] === '.') {
            add_val = add_val.replace(/./, add_val.charAt(0).toUpperCase());
          }
          add_val = ` ${add_val}`;
        } else if (
          (
            field.value.length === 0
            || (
              field.value.length >= 2
            && field.value[field.value.length - 2] === '.'
            && field.value[field.value.length - 1] === '\n')
          )
          && field.title === ''
        ) {
          add_val = add_val.replace(/./, add_val.charAt(0).toUpperCase());
        }
      }
      // eslint-disable-next-line no-param-reassign
      field.value += add_val;
    },
    select_research(pk) {
      if (this.slot.data.direction) {
        return;
      }
      this.slot.data.direction_service = pk;
    },
    add_researches(row, pks) {
      this.create_directions(row);
      setTimeout(() => {
        for (const pk of pks) {
          this.$root.$emit('researches-picker:add_researchcd', pk);
        }
      }, 300);
    },
    show_results(pk) {
      this.$root.$emit('print:results', pk);
    },
    async send_amd() {
      await this.$store.dispatch(actions.INC_LOADING);
      const toSend = this.directions_history.filter((d) => ['error', 'need'].includes(d.amd)).map((d) => d.pk);
      if (toSend.length > 0) {
        await directionsPoint.sendAMD({ pks: toSend });
        window.okmessage('Отправка запланирована');
        this.reload_if_need();
      } else {
        window.errmessage('Не найдены подходящие направления');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async reset_amd(pks) {
      try {
        await this.$dialog.confirm('Подтвердите сброс статуса отправки в АМД');
        await this.$store.dispatch(actions.INC_LOADING);
        await directionsPoint.resetAMD({ pks });
        this.load_pk(this.data.direction.pk);
        this.reload_if_need();
        await this.$store.dispatch(actions.DEC_LOADING);
      } catch (e) {
        // pass
      }
    },
    async send_to_amd(pks) {
      await this.$store.dispatch(actions.INC_LOADING);
      await directionsPoint.sendAMD({ pks });
      this.load_pk(this.data.direction.pk);
      this.reload_if_need();
      window.okmessage('Отправка запланирована');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    updateValue(field, prop) {
      return (newValue) => {
        // eslint-disable-next-line no-param-reassign
        field[prop] = newValue;
      };
    },
    enter_field(...args) {
      return enter_field.apply(this, args);
    },
    leave_field(...args) {
      return leave_field.apply(this, args);
    },
  },
  computed: {
    userServicesFiltered() {
      return this.user_services.filter(s => !this.slot.data.direction || s.pk === this.slot.data.direction_service);
    },
    date_to_form() {
      return `"${this.date}"`;
    },
    ca() {
      if (this.new_anamnesis !== null) {
        return this.new_anamnesis;
      }
      return this.data.anamnesis;
    },
    fte() {
      return this.$store.getters.modules.l2_fast_templates;
    },
    stat_btn() {
      return this.$store.getters.modules.l2_stat_btn;
    },
    stat_btn_d() {
      return this.stat_btn && this.directions_history.length;
    },
    rmis_queue() {
      return this.$store.getters.modules.l2_rmis_queue;
    },
    amd() {
      return this.$store.getters.modules.l2_amd;
    },
    l2_microbiology() {
      return this.$store.getters.modules.l2_microbiology;
    },
    pk_c() {
      const lpk = this.pk.trim();
      if (lpk === '') return -1;
      try {
        return parseInt(lpk, 10);
      } catch (e) {
        // pass
      }
      return -1;
    },
    has_changed() {
      return this.changed && this.data && this.data.ok && this.inserted;
    },
    ...mapGetters({
      user_data: 'user_data',
      researches_obj: 'researches',
      bases: 'bases',
    }),
    internal_base() {
      for (const b of this.bases) {
        if (b.internal_type) {
          return b.pk;
        }
      }
      return -1;
    },
    bases_obj() {
      return this.bases.reduce((a, b) => ({
        ...a,
        [b.pk]: b,
      }), {});
    },
    has_loc() {
      if (!this.user_data || !this.rmis_queue) {
        return false;
      }
      return !!this.user_data.rmis_location;
    },
    user_services() {
      if (!this.user_data || !this.user_data.user_services) {
        return [];
      }
      const r = [{ pk: -1, title: 'Не выбрано', full_title: 'Не выбрано' }];
      for (const d of Object.keys(this.researches)) {
        for (const row of (this.$store.getters.researches[d] || [])) {
          if (this.user_data.user_services.includes(row.pk)) {
            r.push(row);
          }
        }
      }
      return r;
    },
    can_confirm() {
      for (const g of (this.$store.getters.user_data.groups || [])) {
        if (g === 'Без подтверждений') {
          return false;
        }
      }
      return true;
    },
    can_reset_amd() {
      for (const g of (this.$store.getters.user_data.groups || [])) {
        if (g === 'Управление отправкой в АМД') {
          return true;
        }
      }
      return false;
    },
    navState() {
      if (!this.data.ok) {
        return null;
      }
      return {
        pk: this.data.direction.pk,
      };
    },
  },
};
</script>

<style scoped lang="scss">
  .results-root {
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;

    & > div {
      align-self: stretch;
    }
  }

  @media (max-width: 1366px) {
    .burger {
      position: absolute;
      top: 0;
      left: 0;
      bottom: 0;
      z-index: 11;
      background-color: #323639;
      width: 36px;
      transition: all .4s cubic-bezier(.25, .8, .25, 1);
      cursor: pointer;

      &:hover {
        background-color: #4a5054;
      }

      &.active {
        background-color: #03614b;
        &:hover {
          background-color: #059271;
        }

        .burger-inner i {
          transform: rotate(90deg);
        }
      }

      .burger-inner {
        writing-mode: vertical-lr;
        text-orientation: mixed;
        color: #fff;
        padding: 20px 0 0 7px;
        font-size: 16px;
        i {
          transition: all .4s cubic-bezier(.25, .8, .25, 1);
        }
      }

      .burger-lines {
        top: 290px;
        bottom: 10px;
        left: 17px;

        &, &::before, &::after {
          position: absolute;
          width: 1px;
          background-color: rgba(#fff, .1);
        }

        &::before, &::after {
          top: 0;
          bottom: 0;
          content: "";
        }

        &::before {
          left: -9px;
        }

        &::after {
          left: 9px;
        }
      }
    }
  }

  @media (max-width: 1366px) {
    .backdrop {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(#000, .6);
      backdrop-filter: blur(3px);
      z-index: 9;
      display: flex;
      align-items: center;
      justify-content: center;
      padding-left: 341px;

      &-inner {
        color: #fff;
        text-shadow: 0 0 4px rgba(#000, .6);
      }
    }
  }

  @media (min-width: 1367px) {
    .burger, .backdrop {
      display: none;
    }
  }

  .results-sidebar {
    width: 304px;
    border-right: 1px solid #b1b1b1;
    display: flex;
    flex-direction: column;

    @media (max-width: 1366px) {
      position: absolute;
      top: 0;
      left: -304px;
      bottom: 0;
      z-index: 10;
      background-color: #fff;
      transition: all .4s cubic-bezier(.25, .8, .25, 1);

      &.opened {
        left: 36px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
      }
    }
  }

  .results-content {
    display: flex;
    flex-direction: column;
    width: calc(100% - 304px);

    @media (max-width: 1366px) {
      padding-left: 36px;
      width: 100%;
    }
  }

  .results-top {
    border-bottom: 1px solid #b1b1b1;
    height: 68px;
    padding: 5px;
  }

  .results-top > div {
    font-family: "Courier New", Courier, monospace !important;
  }

  .research-title {
    position: sticky;
    top: 0;
    background-color: #ddd;
    text-align: center;
    padding: 5px;
    font-weight: bold;
    z-index: 4;
    display: flex;
  }

  .research-left {
    position: relative;
    text-align: left;
    width: calc(100% - 390px);
  }

  .research-right {
    text-align: right;
    width: 390px;
    margin-top: -5px;
    margin-right: -5px;
    margin-bottom: -5px;
    white-space: nowrap;

    .btn {
      border-radius: 0;
      padding: 5px 4px;
    }
  }

  .right-f {
    width: 140px;
    display: inline-block;

    ::v-deep .btn {
      border-radius: 0;
      padding-top: 5px;
      padding-bottom: 5px;
    }
  }

  .results-history {
    margin-top: -95px;
    margin-left: -295px;
    margin-right: -100px;
    padding: 8px;
    background: #fff;
    border-radius: 4px;
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);

    ul {
      padding-left: 20px;
      margin: 0;

      li {
        font-weight: normal;

        a {
          font-weight: bold;
          display: inline-block;
          padding: 2px 4px;
          background: rgba(#000, .03);
          border-radius: 4px;
          margin-left: 3px;

          &:hover {
            background: rgba(#000, .1);
          }
        }
      }
    }
  }

  .results-editor {
    height: calc(100% - 68px);
    overflow-y: auto;
    overflow-x: hidden;
  }

  .sidebar-bottom-top {
    background-color: #eaeaea;
    flex: 0 0 34px;
    display: flex;
    justify-content: flex-start;
    align-items: center;

    ::v-deep .form-control {
      border-radius: 0;
      border-top: none;
      border-left: none;
      border-right: none;
    }

    span {
      display: inline-block;
      white-space: nowrap;
      padding-left: 5px;
      width: 130px;
    }
  }

  .control-row {
    height: 34px;
    background-color: #f3f3f3;
    display: flex;
    flex-direction: row;

    button {
      align-self: stretch;
      border-radius: 0;
    }

    div {
      align-self: stretch
    }
  }

  .res-title {
    padding: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .direction, .sd {
    padding: 5px;
    margin: 5px;
    border-radius: 5px;
    border: 1px solid rgba(0, 0, 0, 0.14);
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);

    hr {
      margin: 3px;
    }
  }

  .research-row {
    margin-top: 3px;
    margin-bottom: 3px;
    padding: 3px;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
  }

  .anamnesis {
    padding: 10px;
  }

  .status-list {
    display: flex;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  @keyframes rotating {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .directions {
    position: relative;
    height: calc(100% - 68px);
    padding-bottom: 34px;

    &.noStat {
      padding-bottom: 0;
    }

    .inner {
      height: 100%;
      overflow-y: auto;
      overflow-x: hidden;
    }

    &.has_loc {
      .inner {
        height: calc(50% + 17px);
      }
    }

    .rmis_loc {
      position: absolute;
      height: 50%;
      bottom: 0;
      left: 0;
      right: 0;
      border-top: 1px solid #b1b1b1;

      .title {
        height: 20px;
        background: #eaeaea;
        text-align: center;
        position: relative;

        .loader {
          position: absolute;
          right: 2px;
          top: 1px;
          animation: rotating 1.5s linear infinite;
        }
      }

      .inner {
        height: calc(100% - 20px);
        overflow-y: auto;
        overflow-x: hidden;

        &.stat_btn {
          height: calc(100% - 54px);
        }

        table {
          margin-bottom: 0;
        }

        th, td {
          font-size: 12px;
          padding: 2px;
        }

        tr {
          cursor: pointer;

          &.current {
            td {
              background-color: #687282;
              color: #fff;
            }
          }
        }
      }
    }

    .side-bottom {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      border-radius: 0;
      display: flex;
      flex-direction: row;

      .btn {
        height: 34px;
        border-radius: 0;
      }

      &_all {
        .btn:first-child {
          width: 163px;
        }

        .btn:last-child {
          width: 140px;
        }
      }

      &_amd, &_stat {
        .btn {
          width: 100%;
        }
      }
    }
  }

  .dreg_nex {
    color: #687282;
  }

  .dreg_ex {
    color: #da3b6c;
    text-shadow: 0 0 4px rgba(#da3b6c, .6);
  }

  .slot {
    &-0 {
      color: #e1f2fe;
    }

    &-1 {
      color: #f7581c;
    }

    &-2 {
      color: #049372;
    }
  }

  .content-picker {
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    align-items: stretch;
    align-content: flex-start;
  }

  .research-select {
    align-self: stretch;
    display: flex;
    align-items: center;
    padding: 1px 2px 1px;
    color: #000;
    background-color: #fff;
    text-decoration: none;
    transition: .15s linear all;
    margin: 0;
    font-size: 12px;
    min-width: 0;
    flex: 0 1 auto;
    width: 25%;
    height: 34px;
    border: 1px solid #6C7A89 !important;
    cursor: pointer;
    text-align: left;
    outline: transparent;

    &.active {
      background: #049372 !important;
      color: #fff;
    }

    &:hover {
      box-shadow: inset 0 0 8px rgba(0, 0, 0, .8) !important;
    }
  }

  .inline-form {
    background: none;
    border: none;
    padding: 0;
    display: inline-block;
    width: 140px;
    margin-right: -50px;

    &:focus {
      outline: none;
    }
  }

  .lastresults {
    table-layout: fixed;
    padding: 0;
    margin: 0;
    color: #000;
    background-color: #ffdb4d;
    border-color: #000;

    ::v-deep th, ::v-deep td {
      border-color: #000;
    }

    ::v-deep a {
      color: #000;
      text-decoration: dotted underline;
    }

    ::v-deep a:hover {
      text-decoration: none;
    }
  }

  .comment {
    margin-left: 3px;
    color: #049372;
    font-weight: 600;
  }

  .disp {
    a:not(.btn):not(.not-black) {
      color: #0d0d0d !important;
      text-decoration: dotted underline;

      &:hover {
        text-decoration: none;
      }
    }

    &_need, &_need:focus, &_need:active, &_need:hover {
      color: #f7581c !important;
      text-shadow: 0 0 4px rgba(#f7581c, .6);
      font-weight: bold;
    }

    &_finished, &_finished:focus, &_finished:active, &_finished:hover {
      color: #049372 !important;
      text-shadow: 0 0 4px rgba(#049372, .6);
    }

    .btn {
      width: 100%;
      padding: 4px;
    }
  }

  .disp_row {
    font-weight: bold;
    display: inline-block;
    width: 76px;

    &_need, &_need a {
      color: #ff0000 !important;
    }

    &_finished, &_finished a {
      color: #049372 !important;
    }

    a {
      text-decoration: dotted underline;

      &:hover {
        text-decoration: none;
      }
    }
  }

  .status, .control-row .amd {
    padding: 5px;
  }

  .status {
    font-weight: bold;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status-none {
    color: #CF3A24
  }

  .amd {
    font-weight: bold;

    &-need, &-error {
      color: #CF3A24
    }

    &-planned {
      color: #d9be00
    }

    &-ok {
      color: #049372
    }
  }

  label.field-title {
    font-weight: normal;
  }

  textarea {
    resize: vertical;
  }
</style>
