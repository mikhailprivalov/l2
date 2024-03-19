<template>
  <div
    ref="root"
    class="results-root"
    :class="embedded && 'embedded'"
  >
    <div
      v-if="!embedded"
      :class="{ has_loc: has_loc || schedule_in_protocol, opened: sidebarIsOpened || !data.ok }"
      class="results-sidebar"
    >
      <div class="sidebar-top">
        <div class="input-group">
          <span class="input-group-btn">
            <button
              class="btn btn-blue-nb btn-ell dropdown-toggle bt1"
              type="button"
              data-toggle="dropdown"
            >
              <span class="caret" />
              {{ selectedModeTitle }}
            </button>
            <ul
              class="dropdown-menu"
              style="margin-top: 1px"
            >
              <li
                v-for="row in SEARCH_MODES"
                :key="row.id"
              >
                <a
                  href="#"
                  @click.prevent="searchMode = row.id"
                >{{ row.title }}</a>
              </li>
            </ul>
          </span>
          <input
            v-model="pk"
            type="text"
            class="form-control"
            autofocus
            placeholder="номер"
            @keyup.enter="load()"
          >
          <span
            v-if="selectedModeNeedYear"
            class="input-group-btn"
          >
            <button
              class="btn btn-blue-nb btn-ell dropdown-toggle bt1"
              type="button"
              data-toggle="dropdown"
            >
              <span class="caret" />
              {{ selectedYear }}
            </button>
            <ul
              class="dropdown-menu"
              style="margin-top: 1px"
            >
              <li
                v-for="y in years"
                :key="y"
              >
                <a
                  href="#"
                  @click.prevent="selectedYear = y"
                >{{ y }}</a>
              </li>
            </ul>
          </span>
          <span class="input-group-btn">
            <button
              class="btn last btn-blue-nb nbr"
              type="button"
              style="margin-right: -1px"
              @click="load()"
            >Поиск</button>
          </span>
        </div>
      </div>
      <div class="sidebar-bottom-top">
        <span>Результаты за</span>
        <DateFieldNav
          :brn="false"
          :def="date"
          :val.sync="date"
          w="100px"
          light
        />
      </div>
      <div
        class="directions"
        :class="{ noStat: !stat_btn_d, has_loc: has_loc || schedule_in_protocol, stat_btn: stat_btn_d }"
      >
        <div class="inner">
          <div
            v-for="direction in directions_history"
            :key="direction.pk"
            class="direction"
          >
            <div>{{ direction.patient }}, {{ direction.card }}</div>
            <div
              v-for="i in direction.iss"
              :key="`${i.title}_${i.saved}_${i.confirmed}`"
              class="research-row"
            >
              <div class="row">
                <div class="col-xs-8">
                  {{ i.title }}
                </div>
                <div class="col-xs-4 text-right">
                  <IssStatus
                    :i="i"
                    short
                  />
                </div>
              </div>
            </div>
            <hr>
            <template v-if="direction.amd !== 'not_need' && direction.is_need_send_egisz">
              <div
                v-if="direction.amd === 'need'"
                class="amd amd-need"
              >
                ЕГИСЗ: не отправлено
              </div>
              <div
                v-else-if="direction.amd === 'ok'"
                class="amd amd-ok"
              >
                ЕГИСЗ: отправлено ({{ direction.amd_number }})
              </div>
              <div
                v-else-if="direction.amd === 'error'"
                class="amd amd-error"
              >
                ЕГИСЗ: ошибка
              </div>
              <div
                v-else-if="direction.amd === 'planned'"
                class="amd amd-planned"
              >
                ЕГИСЗ: запланировано
              </div>
              <hr>
            </template>
            <div class="row">
              <div class="col-xs-4">
                <a
                  href="#"
                  @click.prevent="load_pk(direction.pk)"
                >Просмотр</a>
              </div>
              <div class="col-xs-4 text-center">
                <a
                  v-if="direction.all_confirmed && stat_btn"
                  :href="`/forms/pdf?type=105.02&napr_id=[${direction.pk}]`"
                  target="_blank"
                >Статталон</a>
              </div>
              <div class="col-xs-4 text-right">
                <a
                  v-if="direction.all_confirmed"
                  href="#"
                  @click.prevent="print_results(direction.pk)"
                >Печать</a>
                <a
                  v-else
                  href="#"
                  @click.prevent="print_example(direction.pk)"
                >Образец</a>
              </div>
            </div>
          </div>
          <div
            v-if="directions_history.length === 0"
            class="text-center"
            style="margin: 5px"
          >
            Нет данных
          </div>
        </div>
        <div
          v-if="has_loc"
          class="rmis_loc"
        >
          <div class="title">
            <div
              v-if="location.loading"
              class="loader"
            >
              <i class="fa fa-spinner" />
            </div>
            Очередь за <input
              v-model="td"
              :readonly="location.loading"
              class="inline-form"
              required
              type="date"
            >
          </div>
          <div
            class="inner"
            :class="{ stat_btn: stat_btn_d }"
          >
            <table class="table table-bordered table-hover">
              <colgroup>
                <col width="38">
                <col>
                <col width="16">
              </colgroup>
              <tbody>
                <tr
                  v-for="rl in location.data"
                  :key="`${rl.slot}_${rl.status && rl.status.direction}`"
                  v-tippy="{ placement: 'top', arrow: true, animation: 'fade' }"
                  :class="{
                    current:
                      rl.slot === slot.id ||
                      (data.ok && rl.status.direction && rl.status.direction === data.direction.pk && !slot.id),
                  }"
                  :title="statusTitles[rl.status.code] || 'Не обработано'"
                  @click="rl.status.code > 0 ? open_fill_slot(rl.status.direction) : open_slot(rl)"
                >
                  <td>{{ rl.timeStart }}</td>
                  <td>{{ rl.patient }}</td>
                  <td>
                    <span
                      class="slot"
                      :class="`slot-${rl.status.code}`"
                    >
                      <i class="fa fa-circle" />
                    </span>
                  </td>
                </tr>
                <tr v-if="!location.init">
                  <td
                    colspan="3"
                    style="text-align: center"
                  >
                    загрузка...
                  </td>
                </tr>
                <td
                  v-else-if="(location.data || []).length === 0"
                  colspan="3"
                  style="text-align: center"
                >
                  нет данных на дату
                </td>
              </tbody>
            </table>
          </div>
        </div>
        <div
          v-else-if="schedule_in_protocol && location.resources.length > 0"
          class="location-internal"
        >
          <div class="title">
            <div
              v-if="location.loading"
              class="loader"
            >
              <i class="fa fa-spinner" />
            </div>
            Очередь за <input
              v-model="td"
              :readonly="location.loading"
              class="inline-form"
              required
              type="date"
            >
          </div>
          <div class="sub-title">
            <Treeselect
              v-model="location.resource"
              :multiple="false"
              class="treeselect-wide treeselect-nbr treeselect-34px"
              :append-to-body="true"
              :disable-branch-nodes="true"
              :clearable="false"
              :z-index="5001"
              placeholder="Ресурс"
              :options="location.resources"
              :cache-options="true"
              open-direction="bottom"
              :open-on-focus="true"
              :default-expand-level="1"
            />
          </div>
          <div
            class="inner"
            :class="{ stat_btn: stat_btn_d }"
          >
            <DaysGridNatural
              v-if="location.resource && location.services?.length && location.data?.length === 1"
              :resource="location.resource"
              :services="location.services"
              :days="location.data"
              :start-time="location.startTime"
              :end-time="location.endTime"
              mode="natural"
              only-emit
            />
          </div>
        </div>
        <div
          v-if="directions_history.length > 0 && (stat_btn || amd)"
          class="side-bottom"
          :class="{
            'side-bottom_all': stat_btn && amd,
            'side-bottom_stat': stat_btn && !amd,
            'side-bottom_amd': !stat_btn && amd,
          }"
        >
          <a
            v-if="stat_btn"
            class="btn btn-blue-nb"
            :href="`/forms/preview?type=105.01&date=${date_to_form}`"
            target="_blank"
          >печать статталонов</a>
          <a
            v-if="amd"
            class="btn btn-blue-nb"
            href="#"
            target="_blank"
            @click.prevent="send_amd"
          >отправить в ЕГИСЗ</a>
        </div>
      </div>
    </div>
    <div
      v-if="!embedded"
      class="burger"
      :class="{ active: sidebarIsOpened && data.ok }"
      @click="sidebarIsOpened = !sidebarIsOpened"
    >
      <span
        v-if="data.ok"
        class="burger-inner"
      >
        <i class="fa fa-bars" />&nbsp;&nbsp;
        {{ sidebarIsOpened ? 'закрыть поиск и результаты' : 'открыть поиск и результаты' }}
      </span>
      <div
        v-if="data.ok"
        class="burger-lines"
      />
    </div>
    <div
      v-if="(sidebarIsOpened || !data.ok) && !embedded"
      class="backdrop"
      @click="sidebarIsOpened = false"
    >
      <div
        v-if="data.ok"
        class="backdrop-inner"
      >
        <div>
          <div style="font-weight: bold">
            Загруженное направление:
          </div>
          <div>№{{ data.direction.pk }} от {{ data.direction.date }}</div>
          <div>{{ data.patient.fio_age }}</div>
          <div
            v-for="row in data.researches"
            :key="row.pk"
          >
            Услуга: {{ row.research.title }}
          </div>
        </div>
      </div>
      <div
        v-else
        class="backdrop-inner"
      >
        <div>направление не загружено</div>
      </div>
    </div>
    <div
      v-if="data.ok"
      class="results-content"
      :class="{ embedded, embeddedFull }"
    >
      <div
        v-if="!embeddedFull"
        class="results-top"
      >
        <div class="row">
          <div :class="data.has_monitoring ? 'col-xs-11' : 'col-xs-6'">
            <div>
              {{ data.has_monitoring ? 'Мониторинг' : 'Направление' }}
              №<a
                href="#"
                class="a-under"
                @click.prevent="print_direction(data.direction.pk)"
              >{{ data.direction.pk }}</a>
              от
              {{ data.direction.date }}
            </div>
            <div v-if="data.has_monitoring">
              {{ data.hospital_title || data.patient.fio }}
            </div>
            <div v-else>
              {{ data.patient.fio_age }}
            </div>
            <div
              v-if="data.direction.diagnos !== '' && !data.has_monitoring"
              class="text-ell"
              :title="data.direction.diagnos"
            >
              Диагноз:
              {{ data.direction.diagnos }}
            </div>
          </div>
          <div
            v-if="!data.has_monitoring"
            class="col-xs-5"
          >
            <div v-if="!data.patient.imported_from_rmis && !data.has_monitoring">
              Источник финансирования: {{ data.direction.fin_source }}
            </div>
            <div v-if="!data.has_monitoring">
              Карта:
              <a
                :href="`/ui/directions?card_pk=${data.patient.card_pk}&base_pk=${data.patient.base}`"
                target="_blank"
                class="a-under"
              >
                {{ data.patient.card }}
              </a>
              &nbsp;&nbsp;
              <a
                v-if="data.card_internal && data.has_doc_referral"
                v-tippy="{ placement: 'bottom', arrow: true, reactive: true, interactive: true, html: '#template-anamnesis' }"
                href="#"
                @show="load_anamnesis"
                @click.prevent="edit_anamnesis"
              ><i
                class="fa fa-book"
              /></a>
              <span class="visible-small">&nbsp;</span>
              <div
                v-if="data.card_internal"
                id="template-anamnesis"
                :class="{ hidden: !data.ok || !data.has_doc_referral || !data.card_internal }"
              >
                <strong>Анамнез жизни</strong><br>
                <span v-if="anamnesis_loading">загрузка...</span>
                <pre
                  v-else
                  style="padding: 5px; text-align: left; white-space: pre-wrap; word-break: keep-all; max-width: 600px"
                >{{ anamnesis_data.text || 'нет данных' }}</pre>
              </div>
              <a
                v-if="data.card_internal && (data.has_doc_referral || data.has_paraclinic)"
                v-tippy="{ placement: 'bottom', arrow: true, reactive: true, interactive: true, html: '#template-dreg' }"
                style="margin-left: 3px"
                href="#"
                :class="{ dreg_nex: !data.patient.has_dreg, dreg_ex: data.patient.has_dreg }"
                @show="load_dreg_rows"
                @click.prevent="dreg = true"
              ><i
                class="fa fa-database"
              /></a>
              <span class="visible-small">&nbsp;</span>
              <div
                v-if="data.card_internal"
                id="template-dreg"
                :class="{ hidden: !data.ok || (!data.has_doc_referral && !data.has_paraclinic) || !data.card_internal }"
              >
                <strong>Диспансерный учёт</strong><br>
                <span v-if="dreg_rows_loading">загрузка...</span>
                <ul
                  v-else
                  style="padding-left: 25px; text-align: left"
                >
                  <li
                    v-for="rd in dreg_rows"
                    :key="rd.pk"
                  >
                    {{ rd.diagnos }} – {{ rd.date_start }} <span v-if="rd.illnes">– {{ rd.illnes }}</span>
                  </li>
                  <li v-if="dreg_rows.length === 0">
                    нет активных записей
                  </li>
                </ul>
              </div>

              <ScreeningButton
                v-if="data.card_internal && (data.has_doc_referral || data.has_paraclinic)"
                :card-pk="data.patient.card_pk"
                @openScreening="dreg = true"
              />

              <a
                v-if="data.card_internal && data.has_doc_referral"
                v-tippy="{ placement: 'bottom', arrow: true, reactive: true, interactive: true, html: '#template-benefit' }"
                style="margin-left: 3px"
                href="#"
                :class="{ dreg_nex: !data.patient.has_benefit, dreg_ex: data.patient.has_benefit }"
                @show="load_benefit_rows"
                @click.prevent="benefit = true"
              ><i
                class="fa fa-cubes"
              /></a>
              <span class="visible-small">&nbsp;</span>
              <div
                v-if="data.card_internal"
                id="template-benefit"
                :class="{ hidden: !data.ok || !data.has_doc_referral || !data.card_internal }"
              >
                <strong>Льготы пациента</strong><br>
                <span v-if="benefit_rows_loading">загрузка...</span>
                <ul
                  v-else
                  style="padding-left: 25px; text-align: left"
                >
                  <li
                    v-for="rb in benefit_rows"
                    :key="rb.pk"
                  >
                    {{ rb.benefit }} – {{ rb.date_start }} – {{ rb.registration_basis }}
                  </li>
                  <li v-if="benefit_rows.length === 0">
                    нет активных записей
                  </li>
                </ul>
              </div>
              <a
                v-if="data.card_internal && data.has_doc_referral"
                v-tippy="{
                  placement: 'bottom',
                  arrow: true,
                  reactive: true,
                  theme: 'light bordered',
                  html: '#template-disp',
                  interactive: true,
                }"
                style="margin-left: 3px"
                href="#"
                :class="{ [`disp_${data.status_disp}`]: true }"
                @click.prevent
              >Д</a>
              <div
                v-if="data.card_internal && data.status_disp !== 'notneed' && data.has_doc_referral"
                id="template-disp"
                class="disp"
              >
                <strong>Диспансеризация</strong><br>
                <ul style="padding-left: 25px; text-align: left">
                  <li
                    v-for="d in data.disp_data"
                    :key="`${d[0]}_${d[5]}`"
                  >
                    <span :class="{ disp_row: true, [!!d[2] ? 'disp_row_finished' : 'disp_row_need']: true }">
                      <span v-if="!d[2]">требуется</span>
                      <a
                        v-else
                        href="#"
                        class="not-black"
                        @click.prevent="show_results([d[2]])"
                      > пройдено </a>
                    </span>

                    <a
                      href="#"
                      @click.prevent="add_researches(data.researches[0], [d[0]])"
                    >
                      {{ d[5] }}
                    </a>
                  </li>
                </ul>
                <div>
                  <a
                    v-if="data.status_disp === 'need'"
                    href="#"
                    class="btn btn-blue-nb"
                    @click.prevent="
                      add_researches(
                        data.researches[0],
                        data.disp_data.filter((d) => !d[2]).map((d) => d[0]),
                      )
                    "
                  >
                    Выбрать требуемые
                  </a>
                  <a
                    v-else
                    href="#"
                    class="btn btn-blue-nb"
                    @click.prevent="show_results(data.disp_data.map((d) => d[2]))"
                  >
                    Печать всех результатов
                  </a>
                </div>
              </div>
              <MedicalCertificates
                :med_certificates="data.medical_certificates"
                :direction="data.direction.pk"
              />
              <RmisLink :is-schedule="false" />
              <ResultsByYear
                :card_pk="data.patient.card_pk"
                is-doc-referral
              />
              <ResultsByYear
                :card_pk="data.patient.card_pk"
                is-paraclinic
              />
              <ResultsByYear
                :card_pk="data.patient.card_pk"
                is-lab
              />
              <ResultControlParams
                :card_pk="data.patient.card_pk"
              />
            </div>
            <div
              v-if="!data.patient.imported_from_rmis && !data.has_monitoring"
              class="text-ell"
              :title="data.patient.doc"
            >
              Лечащий врач:
              {{ data.patient.doc }}
            </div>
            <div v-else-if="data.patient.imported_org">
              Организация: {{ data.patient.imported_org }}
            </div>
          </div>
          <div class="col-xs-1">
            <button
              v-if="!embedded"
              type="button"
              class="close"
              @click="clear()"
            >
              <span>&times;</span>
            </button>
          </div>
        </div>
      </div>
      <div class="results-editor">
        <div
          v-for="row in data.researches"
          :key="row.pk"
        >
          <div
            class="research-title"
            :class="{ withFiles: row.research.enabled_add_file }"
          >
            <div class="research-left">
              {{ row.research.title }}
              <span
                v-if="row.research.comment"
                class="comment"
              > [{{ row.research.comment }}]</span>
              <dropdown
                v-if="!data.has_microbiology && !data.has_monitoring && !embedded"
                :key="`dd-${row.pk}`"
                :visible="research_open_history === row.pk"
                :position="['left', 'bottom', 'left', 'top']"
                @clickout="hide_results"
              >
                <a
                  style="font-weight: normal"
                  href="#"
                  @click.prevent="open_results(row.pk)"
                > (другие результаты) </a>
                <div
                  slot="dropdown"
                  class="results-history"
                  :class="embedded && 'results-history-embedded'"
                >
                  <ul>
                    <li
                      v-for="rh in research_history"
                      :key="rh.pk"
                    >
                      {{ rh.date }}
                      <a
                        href="#"
                        @click.prevent="print_results(rh.direction)"
                      >печать</a>
                      <a
                        v-if="!row.confirmed"
                        href="#"
                        @click.prevent="copy_results(row, rh.pk)"
                      >скопировать</a>
                    </li>
                    <li v-if="research_history.length === 0">
                      результатов не найдено
                    </li>
                  </ul>
                </div>
              </dropdown>
            </div>
            <div class="research-right">
              <FileAdd
                v-if="row.research.enabled_add_files"
                :iss_pk="row.pk"
                :count_files="row.countFiles"
              />
              <template v-if="data.direction.all_confirmed && !data.has_monitoring">
                <a
                  v-if="stat_btn"
                  :href="`/forms/pdf?type=105.02&napr_id=[${data.direction.pk}]`"
                  class="btn btn-blue-nb"
                  target="_blank"
                >Статталон</a>
                <a
                  href="#"
                  class="btn btn-blue-nb"
                  @click.prevent="print_results(data.direction.pk)"
                >Печать</a>
              </template>
              <template v-if="!data.has_microbiology">
                <a
                  v-if="!!row.pacs"
                  v-tippy
                  :href="row.pacs"
                  class="btn btn-blue-nb"
                  target="_blank"
                  title="Снимок"
                >
                  &nbsp;<i class="fa fa-camera" />&nbsp;
                </a>
                <template v-if="!row.confirmed">
                  <button
                    v-if="!row.confirmed"
                    v-tippy
                    class="btn btn-blue-nb"
                    title="Печать образца"
                    @click="print_example(data.direction.pk)"
                  >
                    Образец
                  </button>
                  <button
                    v-if="!row.confirmed"
                    v-tippy
                    class="btn btn-blue-nb"
                    title="Сохранить без подтверждения"
                    @click="save(row)"
                  >
                    &nbsp;<i class="fa fa-save" />&nbsp;
                  </button>
                  <button
                    v-if="!data.has_monitoring && !data.has_expertise"
                    v-tippy
                    class="btn btn-blue-nb"
                    title="Очистить протокол"
                    @click="clear_vals(row)"
                  >
                    &nbsp;<i class="fa fa-times" />&nbsp;
                  </button>
                  <div
                    v-if="fte && !data.has_monitoring && !data.has_expertise"
                    class="right-f"
                  >
                    <SelectPickerM
                      v-model="templates[row.pk]"
                      :search="true"
                      :options="row.templates.map((x) => ({ label: x.title, value: x.pk }))"
                    />
                  </div>
                  <button
                    v-if="fte && !data.has_monitoring && !data.has_expertise"
                    class="btn btn-blue-nb"
                    @click="load_template(row, templates[row.pk])"
                  >
                    Загрузить шаблон
                  </button>
                </template>
              </template>
            </div>
          </div>
          <DescriptiveForm
            :key="`df-${row.pk}`"
            :research="row.research"
            :confirmed="row.confirmed"
            :patient="data.patient"
            :change_mkb="change_mkb(row)"
            :pk="row.pk"
          />
          <div
            v-if="
              !data.has_microbiology && !data.has_gistology &&
                row.research.show_more_services &&
                (!row.confirmed || row.more.length > 0) &&
                !data.has_monitoring &&
                !data.has_expertise
            "
            class="group"
          >
            <div class="group-title">
              Дополнительные услуги
            </div>
            <div class="row">
              <div
                v-show="!row.confirmed"
                class="col-xs-6"
                style="height: 200px; border-right: 1px solid #eaeaea; padding-right: 0"
              >
                <ResearchesPicker
                  v-model="row.more"
                  :hidetemplates="true"
                  :readonly="row.confirmed"
                  :just_search="true"
                  :filter_types="[2, 7]"
                />
              </div>
              <div
                :class="row.confirmed ? 'col-xs-12' : 'col-xs-6'"
                :style="'height: 200px;' + (row.confirmed ? '' : 'padding-left: 0')"
              >
                <SelectedResearches
                  :researches="row.more"
                  :readonly="row.confirmed"
                  :simple="true"
                />
              </div>
            </div>
          </div>
          <template v-if="data.has_microbiology">
            <div
              v-if="row.tube"
              class="group"
            >
              <div class="fields">
                <div class="field">
                  <div
                    class="field-title"
                    style="flex: 1 0 120px"
                  >
                    Номер анализа
                  </div>
                  <div
                    class="field-value"
                    style="padding: 3px"
                  >
                    <span class="tube-pk">{{ row.tube.pk }}</span>
                  </div>
                </div>
                <div class="field">
                  <div
                    class="field-title"
                    style="flex: 1 0 120px"
                  >
                    Ёмкость
                  </div>
                  <div
                    class="field-value"
                    style="padding: 3px"
                  >
                    <span
                      :style="{
                        width: '10px',
                        height: '10px',
                        background: row.tube.color,
                        border: '1px solid #aaa',
                        display: 'inline-block',
                      }"
                    />
                    {{ row.tube.type }}, дата забора {{ row.tube.get }}
                    <a
                      href="#"
                      class="a-under"
                      @click.prevent="print_tube_iss(row.tube.pk)"
                    >печать ш/к</a>
                  </div>
                </div>
              </div>
            </div>
            <BacMicroForm
              v-model="row.microbiology.bacteries"
              :confirmed="row.confirmed"
              :culture-comments-templates="row.microbiology.cultureCommentsTemplates"
            />
            <div class="group">
              <div class="group-title">
                Заключение
              </div>
              <div class="fields">
                <div
                  :class="{ disabled: row.confirmed }"
                  class="field"
                  v-on="{
                    mouseenter: enter_field(row.microbiology.conclusionTemplates.length > 0),
                    mouseleave: leave_field(row.microbiology.conclusionTemplates.length > 0),
                  }"
                >
                  <FastTemplates
                    :update_value="updateValue(row.microbiology, 'conclusion')"
                    :value="row.microbiology.conclusion || ''"
                    :values="row.microbiology.conclusionTemplates"
                    :confirmed="row.confirmed"
                  />
                  <div class="field-value">
                    <textarea
                      v-model="row.microbiology.conclusion"
                      rows="5"
                      class="form-control"
                      :readonly="row.confirmed"
                    />
                  </div>
                </div>
              </div>
            </div>
          </template>
          <div
            v-if="row.research.is_doc_refferal && row.recipe"
            class="group"
          >
            <div class="group-title">
              Рецепты
            </div>
            <div class="row">
              <div class="col-xs-12">
                <div class="sd">
                  <RecipeInput
                    v-model="row.recipe"
                    :pk="row.pk"
                    :confirmed="row.confirmed"
                  />
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="row.research.is_doc_refferal && row.research.is_paraclinic"
            class="group"
          >
            <div class="group-title">
              Направления в рамках приёма
            </div>
            <div class="row">
              <div class="col-xs-12">
                <div class="sd">
                  <DirectionsHistory
                    :iss_pk="row.pk"
                    :kk="kk || 'cd'"
                  />
                </div>
                <div
                  v-if="!row.confirmed"
                  class="sd empty"
                >
                  <button
                    class="btn btn-primary-nb btn-blue-nb"
                    type="button"
                    @click="create_directions(row)"
                  >
                    <i class="fa fa-plus" /> создать направления
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="(row.research.is_doc_refferal || row.research.is_gistology) && stat_btn && !is_operator_protocol"
            class="group"
          >
            <div class="group-title">
              Данные статталона
            </div>
            <div class="fields">
              <div
                v-if="row.research.is_doc_refferal || row.research.is_gistology"
                class="field"
              >
                <div
                  class="field-title"
                >
                  Цель посещения
                </div>
                <div class="field-value">
                  <select
                    v-model="row.purpose"
                    :disabled="row.confirmed"
                  >
                    <option
                      v-for="o in row.purpose_list"
                      :key="o.pk"
                      :value="o.pk"
                    >
                      {{ o.title }}
                    </option>
                  </select>
                </div>
              </div>
              <div
                v-if="row.research.is_doc_refferal"
                class="field"
              >
                <label
                  class="field-title"
                  for="first-time"
                > Впервые </label>
                <div class="field-value">
                  <input
                    id="first-time"
                    v-model="row.first_time"
                    type="checkbox"
                    :disabled="row.confirmed"
                  >
                </div>
              </div>
              <div
                v-if="row.research.is_doc_refferal"
                class="field"
              >
                <div class="field-title">
                  Результат обращения
                </div>
                <div class="field-value">
                  <select
                    v-model="row.result"
                    :disabled="row.confirmed"
                  >
                    <option
                      v-for="o in row.result_list"
                      :key="o.pk"
                      :value="o.pk"
                    >
                      {{ o.title }}
                    </option>
                  </select>
                </div>
              </div>
              <div
                v-if="row.research.is_doc_refferal"
                class="field"
              >
                <div class="field-title">
                  Исход
                </div>
                <div class="field-value">
                  <select
                    v-model="row.outcome"
                    :disabled="row.confirmed"
                  >
                    <option
                      v-for="o in row.outcome_list"
                      :key="o.pk"
                      :value="o.pk"
                    >
                      {{ o.title }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="field">
                <div class="field-title">
                  Заключительный диагноз
                </div>
                <div
                  v-if="!row.confirmed"
                  class="field-value mkb10"
                >
                  <MKBField v-model="row.diagnos" />
                </div>
                <div
                  v-else
                  class="field-value"
                >
                  <input
                    v-model="row.diagnos"
                    class="form-control"
                    :readonly="true"
                  >
                </div>
              </div>
              <div
                v-if="row.research.is_doc_refferal || needShowDateExamination(row.research)"
                class="field"
              >
                <div class="field-title">
                  Дата осмотра
                </div>
                <label class="field-value">
                  <input
                    v-model="row.examination_date"
                    :max="tdm()"
                    :min="td_m_year"
                    :readonly="row.confirmed"
                    class="form-control"
                    required
                    style="width: 160px"
                    type="date"
                  >
                </label>
              </div>
              <div
                v-if="row.research.is_doc_refferal"
                class="field"
              >
                <div class="field-title">
                  Место оказания
                </div>
                <div class="field-value">
                  <select
                    v-model="row.place"
                    :disabled="row.confirmed"
                  >
                    <option
                      v-for="o in row.place_list"
                      :key="o.pk"
                      :value="o.pk"
                    >
                      {{ o.title }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="field">
                <div class="field-title">
                  Источник финансирования
                </div>
                <div class="field-value">
                  <select
                    v-model="row.fin_source"
                    :disabled="row.confirmed"
                  >
                    <option
                      v-for="o in row.fin_source_list"
                      :key="o.pk"
                      :value="o.pk"
                    >
                      {{ o.title }}
                    </option>
                  </select>
                </div>
              </div>
              <div
                v-if="row.research.is_gistology && paidFinSource(row.fin_source, row.fin_source_list)"
                class="field"
              >
                <div class="field-title">
                  Платная категория
                </div>
                <div class="field-value">
                  <select
                    v-model="row.price_category"
                    :disabled="row.confirmed"
                  >
                    <option
                      v-for="o in row.price_category_list"
                      :key="o.pk"
                      :value="o.pk"
                    >
                      {{ o.title }}
                    </option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="!data.has_microbiology && !row.is_form && !data.has_monitoring && !data.has_expertise && !is_operator_protocol"
            class="group"
          >
            <div class="fields">
              <div class="field">
                <label
                  class="field-title"
                  for="onco"
                > Подозрение на онко </label>
                <div class="field-value">
                  <input
                    id="onco"
                    v-model="row.maybe_onco"
                    type="checkbox"
                    :disabled="row.confirmed"
                  >
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="row.parentDirection && !embedded"
            class="group"
          >
            <div class="group-title">
              Главное направление
            </div>
            <div class="fields">
              <div class="field">
                <label
                  class="field-title"
                  for="onco"
                >
                  №<a
                    v-if="!row.parentDirection.is_hospital"
                    href="#"
                    class="a-under"
                    @click.prevent="load_pk(row.parentDirection.pk)"
                  >{{ row.parentDirection.pk }}</a><span v-else>{{ row.parentDirection.pk }}</span>
                </label>
                <div class="field-value simple-value">
                  {{ row.parentDirection.service }}
                  <template v-if="row.parentDirection.is_hospital">
                    &nbsp;<i
                      v-tippy
                      class="fa fa-bed"
                      title="И/б стационара"
                    />
                  </template>
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="!directionFormProps && row.children_directions && row.children_directions.length > 0"
            class="group"
          >
            <div class="group-title">
              Дочерние направления
            </div>
            <div
              v-for="d in row.children_directions"
              :key="d.pk"
              class="fields"
            >
              <div class="field">
                <label class="field-title">
                  №<a
                    href="#"
                    class="a-under"
                    @click.prevent="load_pk(d.pk)"
                  >{{ d.pk }}</a>
                </label>
                <div class="field-value simple-value">
                  <ul>
                    <li
                      v-for="(s, j) in d.services"
                      :key="j"
                    >
                      {{ s }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="!row.confirmed && can_confirm_by_other_user"
            class="group"
          >
            <div class="fields">
              <div class="field">
                <label class="field-title"> Подтверждение от имени </label>
                <div class="field-value">
                  <Treeselect
                    v-model="row.work_by"
                    :multiple="false"
                    :disable-branch-nodes="true"
                    class="treeselect-wide"
                    :options="workFromUsers"
                    :append-to-body="true"
                    :clearable="true"
                    :z-index="5001"
                    placeholder="Не выбрано"
                  />

                  <div
                    v-if="workFromHistoryList.length > 0"
                    style="margin-top: 5px"
                  >
                    <div
                      v-for="p in workFromHistoryList"
                      :key="p.id"
                    >
                      <a
                        v-tippy
                        href="#"
                        class="a-under-reversed"
                        title="Выбрать из истории"
                        @click.prevent="row.work_by = p.id"
                      >
                        <i class="fas fa-history" /> {{ p.label }} — {{ p.podr }}
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="needShowAdditionalParams(row)"
            class="group"
          >
            <div class="fields">
              <div
                v-if="row.whoSaved"
                class="field"
              >
                <label class="field-title"> Сохранено </label>
                <div class="field-value simple-value">
                  {{ row.whoSaved }}
                </div>
              </div>
              <div
                v-if="row.whoConfirmed"
                class="field"
              >
                <label class="field-title"> Подтверждено </label>
                <div class="field-value simple-value">
                  {{ row.whoConfirmed }}
                </div>
              </div>
              <div
                v-if="row.whoExecuted"
                class="field"
              >
                <label class="field-title"> Оператор </label>
                <div class="field-value simple-value">
                  {{ row.whoExecuted }}
                </div>
              </div>
              <div
                v-if="(data.direction.coExecutor || l2_decriptive_coexecutor) && !is_operator_protocol"
                class="field"
              >
                <label class="field-title">Со-исполнитель</label>
                <div class="field-value simple-value">
                  <Treeselect
                    v-model="data.direction.coExecutor"
                    :multiple="false"
                    :disable-branch-nodes="true"
                    class="treeselect-wide"
                    :options="workFromUsers"
                    :append-to-body="true"
                    :clearable="true"
                    :z-index="5001"
                    placeholder="Не выбрано"
                    :disabled="!l2_decriptive_coexecutor || row.whoConfirmed"
                  />
                </div>
              </div>
              <div
                v-if="data.direction.additionalNumber"
                class="field"
              >
                <label class="field-title">Дополнительный номер</label>
                <div class="field-value simple-value">
                  <code>{{ data.direction.additionalNumber }}</code>
                  <small v-if="data.direction.additionalNumberYear">
                    {{ data.direction.additionalNumberYear }} год
                  </small>
                </div>
              </div>
              <div
                v-if="data.direction.timeGistologyReceive"
                class="field"
              >
                <label class="field-title">Материал гистологии принят</label>
                <div class="field-value simple-value">
                  {{ data.direction.timeGistologyReceive }}
                </div>
              </div>
            </div>
          </div>
          <div class="control-row">
            <div class="res-title">
              {{ row.research.title }}:
            </div>
            <IssStatus :i="row" />
            <button
              v-if="!row.confirmed"
              class="btn btn-blue-nb"
              @click="save(row)"
            >
              Сохранить
            </button>
            <button
              v-if="!row.confirmed && can_confirm && !is_operator_protocol || !row.confirmed && can_confirm && row.research.isAux"
              class="btn btn-blue-nb"
              :disabled="!r(row) || needFillWorkBy(row)"
              @click="save_and_confirm(row)"
            >
              Сохранить и подтвердить
            </button>
            <button
              v-if="row.confirmed && row.allow_reset_confirm && can_confirm && !is_operator_protocol"
              class="btn btn-blue-nb"
              @click="reset_confirm(row)"
            >
              Сброс подтверждения
            </button>
            <template v-if="amd && data.researches.length === 1">
              <div
                v-if="data.direction.amd === 'planned'"
                class="amd amd-planned"
              >
                ЕГИСЗ: очередь
              </div>
              <div
                v-if="data.direction.amd === 'error' && row.confirmed"
                class="amd amd-error"
              >
                ЕГИСЗ: ошибка
              </div>
              <div
                v-if="data.direction.amd === 'need' && row.confirmed"
                class="amd amd-need"
              >
                ЕГИСЗ: не отправлено
              </div>
              <div
                v-if="data.direction.amd === 'ok'"
                class="amd amd-ok"
              >
                ЕГИСЗ: отправлено ({{ data.direction.amd_number }})
              </div>
              <button
                v-if="can_reset_amd && data.direction.amd !== 'not_need' && data.direction.amd !== 'need'"
                class="btn btn-blue-nb"
                @click="reset_amd([data.direction.pk])"
              >
                Сброс статуса ЕГИЗ
              </button>
              <button
                v-if="data.direction.amd === 'need' || data.direction.amd === 'error'"
                class="btn btn-blue-nb"
                @click="send_to_amd([data.direction.pk])"
              >
                Отправить в ЕГИСЗ
              </button>
            </template>
            <EDSDirection
              v-if="data.researches.length === 1"
              :key="`${data.direction.pk}_${row.confirmed}`"
              :direction-pk="data.direction.pk"
              :all_confirmed="data.direction.all_confirmed"
            />
            <div
              v-if="(!r(row) || needFillWorkBy(row)) && !row.confirmed"
              class="status-list"
            >
              <div class="status status-none">
                Не верно:
              </div>
              <div
                v-for="rl in r_list(row)"
                :key="rl"
                class="status status-none"
              >
                {{ rl }};
              </div>
              <div
                v-if="needFillWorkBy(row)"
                class="status status-none"
              >
                подтверждение от имени
              </div>
            </div>
          </div>
        </div>
        <div
          v-if="data && data.ok && data.researches.length > 1 && data.direction.all_confirmed"
          class="control-row"
        >
          <div class="res-title">
            Услуг в направлении: {{ data.researches.length }} шт.
          </div>
          <template v-if="amd">
            <div
              v-if="data.direction.amd === 'planned'"
              class="amd amd-planned"
            >
              ЕГИСЗ: запланировано
            </div>
            <div
              v-if="data.direction.amd === 'error' && row.confirmed"
              class="amd amd-error"
            >
              ЕГИСЗ: ошибка
            </div>
            <div
              v-if="data.direction.amd === 'need' && row.confirmed"
              class="amd amd-need"
            >
              ЕГИСЗ: не отправлено
            </div>
            <div
              v-if="data.direction.amd === 'ok'"
              class="amd amd-ok"
            >
              ЕГИСЗ: отправлено ({{ data.direction.amd_number }})
            </div>
            <button
              v-if="can_reset_amd && data.direction.amd !== 'not_need' && data.direction.amd !== 'need'"
              class="btn btn-blue-nb"
              @click="reset_amd([data.direction.pk])"
            >
              Сброс статуса ЕГИСЗ
            </button>
            <button
              v-if="data.direction.amd === 'need' || data.direction.amd === 'error'"
              class="btn btn-blue-nb"
              @click="send_to_amd([data.direction.pk])"
            >
              Отправить в ЕГИСЗ
            </button>
          </template>
          <EDSDirection
            :key="`${data.direction.pk}_${data.direction.all_confirmed}`"
            :direction-pk="data.direction.pk"
            :all_confirmed="data.direction.all_confirmed"
          />
        </div>
        <div
          v-if="show_additional"
          class="group"
        >
          <div class="group-title">
            Дополнительные исследования
          </div>
          <div class="row">
            <div
              class="col-xs-6"
              style="height: 200px; border-right: 1px solid #eaeaea; padding-right: 0"
            >
              <ResearchesPicker
                v-model="moreServices"
                :hidetemplates="true"
                :just_search="true"
                :types-only="[10000]"
                :filter_sub_types="additionalTypes"
                :filter_researches="data.researches.map((r) => r.research.pk)"
              />
            </div>
            <div
              class="col-xs-6"
              style="height: 200px; padding-left: 0"
            >
              <SelectedResearches
                :researches="moreServices"
                :simple="true"
              />
            </div>
          </div>
          <div
            class="sd empty"
            style="margin-top: 5px"
          >
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              :disabled="moreServices.length === 0"
              @click="add_services"
            >
              Добавить услуги в направление
            </button>
          </div>
          <div
            class="text-right"
            style="margin-top: 5px"
          >
            Вы можете назначить дополнительные исследования только, если направление не подтверждено полностью.
          </div>
        </div>
      </div>
    </div>
    <div
      v-else
      class="results-content"
    />
    <Modal
      v-if="anamnesis_edit"
      ref="modalAnamnesisEdit"
      show-footer="true"
      white-bg="true"
      max-width="710px"
      width="100%"
      margin-left-right="auto"
      margin-top
      @close="hide_modal_anamnesis_edit"
    >
      <span slot="header">Редактор анамнеза жизни – карта {{ data.patient.card }}, {{ data.patient.fio_age }}</span>
      <div
        slot="body"
        style="min-height: 140px"
        class="registry-body"
      >
        <textarea
          v-model="anamnesis_data.text"
          rows="14"
          class="form-control"
          placeholder="Анамнез жизни"
        />
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="hide_modal_anamnesis_edit"
            >
              Отмена
            </button>
          </div>
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="save_anamnesis()"
            >
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </Modal>
    <Modal
      v-if="create_directions_for > -1"
      ref="modalCD"
      margin-top
      margin-left-right="auto"
      max-width="1400px"
      show-footer="true"
      white-bg="true"
      width="100%"
      @close="hide_modal_create_directions"
    >
      <span slot="header">Создание направлений – карта {{ data.patient.card }}, {{ data.patient.fio_age }}</span>
      <div
        slot="body"
        class="registry-body"
        style="min-height: 140px"
      >
        <div class="row">
          <div
            class="col-xs-6"
            style="height: 450px; border-right: 1px solid #eaeaea; padding-right: 0"
          >
            <ResearchesPicker
              v-model="create_directions_data"
              :kk="kk || 'cd'"
              style="border-top: 1px solid #eaeaea; border-bottom: 1px solid #eaeaea"
              :filter_types="[7]"
            />
          </div>
          <div
            class="col-xs-6"
            style="height: 450px; padding-left: 0"
          >
            <SelectedResearches
              :kk="kk || 'cd'"
              :base="bases_obj[data.patient.base]"
              :researches="create_directions_data"
              :main_diagnosis="create_directions_diagnosis"
              :valid="true"
              :card_pk="data.patient.card_pk"
              :initial_fin="data.direction.fin_source_id"
              :parent_iss="create_directions_for"
              :clear_after_gen="true"
              style="border-top: 1px solid #eaeaea; border-bottom: 1px solid #eaeaea"
              :parent-case="caseId"
              :case-by-direction="true"
            />
          </div>
        </div>
        <div
          v-if="create_directions_data.length > 0"
          style="margin-top: 5px; text-align: left"
        >
          <table class="table table-bordered lastresults">
            <colgroup>
              <col width="180">
              <col>
              <col width="110">
              <col width="110">
            </colgroup>
            <tbody>
              <LastResult
                v-for="p in create_directions_data"
                :key="p"
                :individual="data.patient.individual_pk"
                :no-scroll="true"
                :research="p"
              />
            </tbody>
          </table>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="hide_modal_create_directions"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
    <Modal
      v-if="!!slot.id"
      ref="modalSlot"
      margin-top="50px"
      show-footer="true"
      white-bg="true"
      max-width="710px"
      width="100%"
      margin-left-right="auto"
      @close="close_slot"
    >
      <span slot="header">Слот {{ slot.id }}</span>
      <div
        slot="body"
        style="min-height: 200px; background-color: #fff"
        class="registry-body"
      >
        <div
          v-if="Object.keys(slot.data).length === 0"
          class="text-center"
        >
          загрузка...
        </div>
        <div
          v-else
          class="text-left"
        >
          <h3 style="margin-top: 0">
            Талон № {{ slot.data.pk }}
          </h3>
          <h5>{{ slot.data.datetime }}</h5>
          ЕЦП ID пациента:
          <a
            :href="`/ui/directions?rmis_uid=${slot.data.patient_uid}`"
            target="_blank"
          >{{ slot.data.patient_uid }}</a><br>
          <div v-if="!slot.data.direction">
            Нет связанного назначения. Выберите ниже:
          </div>
          <div v-else>
            Выбранное назначение для талона:
          </div>
          <div class="content-picker">
            <ResearchPick
              v-for="row in userServicesFiltered"
              :key="row.pk"
              :class="{ active: row.pk === slot.data.direction_service }"
              :research="row"
              class="research-select"
              @click.native="select_research(row.pk)"
            />
            <div v-if="userServicesFiltered.length === 0">
              нет данных
            </div>
          </div>
          <div
            class="text-center"
            style="margin-top: 10px"
          >
            <button
              v-if="!slot.data.direction"
              :disabled="slot.data.direction_service === -1"
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="fill_slot"
            >
              Сохранить назначение и заполнить протокол
            </button>
            <button
              v-else
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="open_fill_slot(slot.data.direction)"
            >
              Перейти к протоколу
            </button>
          </div>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="close_slot"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
    <DReg
      v-if="dreg"
      :card_pk="data.patient.card_pk"
      :card_data="data.patient"
      :fin-id="data.direction.fin_source_id"
      :parent_iss="data.researches[0].pk"
    />
    <Benefit
      v-if="benefit"
      :card_pk="data.patient.card_pk"
      :card_data="data.patient"
      :readonly="true"
    />
    <ResultsViewer
      v-if="show_results_pk > -1"
      :pk="show_results_pk"
    />
  </div>
</template>

<script lang="ts">
import moment from 'moment';
// @ts-ignore
import dropdown from 'vue-my-dropdown';
import { mapGetters } from 'vuex';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { vField, vGroup } from '@/components/visibility-triggers';
import { cleanCaches } from '@/utils';
import { enterField, leaveField } from '@/forms/utils';
import ResultsByYear from '@/ui-cards/PatientResults/ResultsByYear.vue';
import ResultControlParams from '@/ui-cards/PatientResults/ResultControlParams.vue';
import RmisLink from '@/ui-cards/RmisLink.vue';
import EDSDirection from '@/ui-cards/EDSDirection.vue';
import patientsPoint from '@/api/patients-point';
import * as actions from '@/store/action-types';
import directionsPoint from '@/api/directions-point';
import SelectPickerM from '@/fields/SelectPickerM.vue';
import researchesPoint from '@/api/researches-point';
import Modal from '@/ui-cards/Modal.vue';
import MKBField from '@/fields/MKBField.vue';
import DateFieldNav from '@/fields/DateFieldNav.vue';
import DReg from '@/modals/DReg.vue';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import SelectedResearches from '@/ui-cards/SelectedResearches.vue';
import usersPoint from '@/api/user-point';
import ResearchPick from '@/ui-cards/ResearchPick.vue';
import Benefit from '@/modals/Benefit.vue';
import DirectionsHistory from '@/ui-cards/DirectionsHistory/index.vue';
import RecipeInput from '@/ui-cards/RecipeInput.vue';
import ResultsViewer from '@/modals/ResultsViewer.vue';
import ScreeningButton from '@/ui-cards/ScreeningButton.vue';
import LastResult from '@/ui-cards/LastResult.vue';
import IssStatus from '@/ui-cards/IssStatus.vue';
import MedicalCertificates from '@/ui-cards/MedicalCertificates.vue';

import DescriptiveForm from '../forms/DescriptiveForm.vue';
import BacMicroForm from '../forms/BacMicroForm.vue';
import UrlData from '../UrlData';
import FastTemplates from '../forms/FastTemplates.vue';

const SEARCH_MODES = [
  {
    id: 'direction',
    title: 'Направление',
  },
  {
    id: 'mk',
    title: 'Микробиология',
  },
  {
    id: 'additional',
    title: 'Доп. номер',
  },
];

const EMPTY_YEAR = 'без года';

export default {
  name: 'ResultsParaclinic',
  components: {
    EDSDirection,
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
    ResultControlParams,
    RmisLink,
    ScreeningButton,
    Treeselect,
    FileAdd: () => import('@/ui-cards/FileAdd.vue'),
    DaysGridNatural: () => import('@/pages/Schedule/DaysGridNatural.vue'),
  },
  async beforeRouteLeave(to, from, next) {
    const msg = this.unload();

    if (msg) {
      try {
        await this.$dialog.confirm(msg);
      } catch (_) {
        next(false);
        return;
      }
    }

    next();
  },
  props: {
    directionIdToOpen: {
      type: Number,
      required: false,
    },
    caseId: {
      type: Number,
      required: false,
    },
    kk: {
      type: String,
      required: false,
    },
  },
  data() {
    return {
      pk: '',
      searchMode: SEARCH_MODES[0].id,
      SEARCH_MODES,
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
        resource: null,
        services: [],
        resources: [],
        startTime: null,
        endTime: null,
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
      hasEDSigns: false,
      statusTitles: {
        1: 'Направление зарегистрировано',
        2: 'Результат подтверждён',
      },
      embedded: false,
      embeddedFull: false,
      tableFieldsErrors: {},
      workFromUsers: [],
      priceCategory: [],
      workFromHistory: [],
      moreServices: [],
      usersLoading: false,
      selectedYear: moment().format('YYYY'),
      currentDate: moment().format('YYYY-MM-DD'),
      currentDateInterval: null,
    };
  },
  computed: {
    directionFormProps() {
      return !!this.directionIdToOpen;
    },
    currentYear() {
      return moment(this.currentDate).format('YYYY');
    },
    l2_decriptive_coexecutor() {
      return this.$store.getters.modules.l2_decriptive_coexecutor;
    },
    selectedModeTitle() {
      return this.SEARCH_MODES.find(m => m.id === this.searchMode)?.title;
    },
    requiredStattalonFields() {
      return this.$store.getters.requiredStattalonFields;
    },
    researchesPkRequiredStattalonFields() {
      return this.$store.getters.researchesPkRequiredStattalonFields;
    },
    userServicesFiltered() {
      return this.user_services.filter((s) => !this.slot.data.direction || s.pk === this.slot.data.direction_service);
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
    schedule_in_protocol() {
      return this.$store.getters.modules.l2_schedule_in_protocol;
    },
    amd() {
      return this.$store.getters.modules.l2_amd;
    },
    l2_microbiology() {
      return this.$store.getters.modules.l2_microbiology;
    },
    l2_morfology_additional() {
      return this.$store.getters.modules.l2_morfology_additional;
    },
    locationResource() {
      return this.location?.resource;
    },
    show_additional() {
      if (!this.data?.ok) {
        return false;
      }
      return (
        this.l2_morfology_additional
        && this.data.has_microbiology
        && !this.data.direction.all_confirmed
      );
    },
    additionalTypes() {
      if (!this.show_additional) {
        return [];
      }
      if (this.data.has_microbiology) {
        return [10001];
      }
      if (this.data.has_citology) {
        return [10002];
      }
      if (this.data.has_gistology) {
        return [10003];
      }
      return [1000000];
    },
    pk_c() {
      const lpk = this.pk.trim();
      if (this.searchMode === 'additional') {
        return lpk;
      }
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
      return this.bases.reduce(
        (a, b) => ({
          ...a,
          [b.pk]: b,
        }),
        {},
      );
    },
    has_loc() {
      if (!this.user_data || !this.rmis_queue) {
        return false;
      }
      return !!this.user_data.rmis_location;
    },
    user_services() {
      if (!this.user_data?.user_services) {
        return [];
      }
      const r = [{ pk: -1, title: 'Не выбрано', full_title: 'Не выбрано' }];
      for (const d of Object.keys(this.researches_obj)) {
        for (const row of this.$store.getters.researches[d] || []) {
          if (this.user_data.user_services.includes(row.pk)) {
            r.push(row);
          }
        }
      }
      return r;
    },
    is_operator_protocol() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (g === 'Протокол для оператора') {
          return true;
        }
      }
      return false;
    },
    can_confirm() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (g === 'Без подтверждений') {
          return false;
        }
      }
      return true;
    },
    can_reset_amd() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (g === 'Управление отправкой в ЕГИСЗ') {
          return true;
        }
      }
      return false;
    },
    can_confirm_by_other_user() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (g === 'Работа от имени в описательных протоколах') {
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
    workFromHistoryList() {
      return this.workFromHistory
        .map((p) => {
          for (const podr of this.workFromUsers) {
            const profile = podr.children.find((x) => x.id === p);

            if (profile) {
              return profile;
            }
          }

          return null;
        })
        .filter(Boolean);
    },
    selectedModeNeedYear() {
      return this.searchMode === 'additional';
    },
    years() {
      const currentYear = Number(this.currentYear);
      const years = [];

      for (let i = currentYear; i >= 2022; i--) {
        years.push(i);
      }

      years.push(EMPTY_YEAR);

      return years;
    },
    selectedYearValue() {
      if (this.selectedYear === EMPTY_YEAR) {
        return null;
      }

      return Number(this.selectedYear);
    },
  },
  watch: {
    locationResource: {
      immediate: true,
      handler() {
        if (this.locationResource) {
          this.load_location_internal();
        }
      },
    },
    date() {
      this.load_history();
    },
    user_data: {
      async handler({ rmis_location: rmisLocation }) {
        if (!this.location.init && rmisLocation) {
          await this.load_location();
          await this.load_location_internal();
          this.location.init = true;
        }
      },
      immediate: true,
    },
    can_confirm_by_other_user: {
      handler() {
        this.usersLoading = true;
      },
      immediate: true,
    },
    l2_decriptive_coexecutor: {
      handler() {
        this.usersLoading = true;
      },
      immediate: true,
    },
    usersLoading: {
      async handler() {
        if (this.usersLoading && this.can_confirm_by_other_user && this.workFromUsers.length === 0) {
          const { users } = await usersPoint.loadUsersByGroup({
            group: ['Врач параклиники', 'Врач консультаций', 'Заполнение мониторингов', 'Свидетельство о смерти-доступ'],
          });
          this.workFromUsers = users;
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
    schedule_in_protocol: {
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
        this.load_location_internal();
      },
    },
    navState() {
      if (this.directionFormProps) {
        return;
      }

      if (this.inited) {
        UrlData.set(this.navState);
      }

      UrlData.title(this.data.ok ? this.data.direction.pk : null);
    },
  },
  mounted() {
    this.load_history();
    this.$root.$on('hide_dreg', () => {
      this.load_dreg_rows();
      this.dreg = false;
    });
    this.$root.$on('hide_benefit', () => {
      this.load_benefit_rows();
      this.benefit = false;
    });
    this.$root.$on('reload-location', () => {
      this.load_location_internal();
    });

    this.$root.$on('show_results', (pk) => {
      this.show_results_pk = pk;
    });

    this.$root.$on('hide_results', () => {
      this.show_results_pk = -1;
    });

    this.$root.$on('EDS:has-signs', (has) => {
      this.hasEDSigns = has;
    });

    const storedData = UrlData.get();
    if (this.directionFormProps) {
      this.load_pk(this.directionIdToOpen).then(() => {
        this.inited = true;
      });
    } else if (storedData && typeof storedData === 'object' && storedData.pk) {
      this.load_pk(storedData.pk).then(() => {
        this.inited = true;
      });
    } else {
      this.inited = true;
    }

    this.$root.$on('open-direction-form', (pk) => this.load_pk(pk));

    this.$root.$on('preselect-args-ok', () => {
      this.hasPreselectOk = true;
    });

    this.$root.$on('table-field:errors:set', (fieldPk, hasInvalid) => {
      this.tableFieldsErrors = {
        ...this.tableFieldsErrors,
        [fieldPk]: hasInvalid,
      };
    });

    const urlParams = new URLSearchParams(window.location.search);
    this.embedded = !!this.directionIdToOpen || urlParams.get('embedded') === '1';
    this.embeddedFull = !!this.directionIdToOpen || urlParams.get('embeddedFull') === '1';
    window.$(window).on('beforeunload', this.unload);

    try {
      if (localStorage.getItem('results-paraclinic:work-from-history')) {
        const savedWorkedFrom = JSON.parse(localStorage.getItem('results-paraclinic:work-from-history'));

        if (Array.isArray(savedWorkedFrom)) {
          this.workFromHistory = savedWorkedFrom;
        }
      }
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
    }

    this.$store.dispatch(actions.LOAD_REQUIRED_STATTALON_FIELDS);
    this.$store.dispatch(actions.LOAD_RESEARCHES_PK_REQUIRED_STATTALON_FIELDS);

    this.getCurrentTime();

    this.currentDateInterval = setInterval(() => {
      this.getCurrentTime();
    }, 60000);
  },
  beforeDestroy() {
    window.$(window).off('beforeunload', this.unload);
    clearInterval(this.currentDateInterval);
  },
  methods: {
    async getCurrentTime() {
      const { date } = await this.$api('current-time');
      if (date) {
        this.currentDate = date;
      }
    },
    needShowDateExamination(currentResearch) {
      if (typeof this.data.showExaminationDate.is_gistology !== 'undefined') {
        return currentResearch.is_gistology && this.data.showExaminationDate.is_gistology;
      }
      if (typeof this.data.showExaminationDate.is_paraclinic !== 'undefined') {
        return currentResearch.is_paraclinic && this.data.showExaminationDate.is_paraclinic;
      }
      if (typeof this.data.showExaminationDate.is_stom !== 'undefined') {
        return currentResearch.is_stom && this.data.showExaminationDate.is_stom;
      }
      return false;
    },
    paidFinSource(currentRow, currentFinSourceList) {
      for (const s of currentFinSourceList) {
        if (s.pk === currentRow && s.title === 'Платно') {
          return true;
        }
      }
      return false;
    },
    needShowAdditionalParams(row) {
      return row.whoSaved
      || row.whoConfirmed
      || row.whoExecuted
      || this.data.direction.additionalNumber
      || this.data.direction.timeGistologyReceive
      || this.data.direction.coExecutor
      || this.data.direction.paymentCategory;
    },
    async add_services() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { pks, ok, message } = await this.$api('directions/add-additional-issledovaniye', {
        direction_pk: this.data.direction.pk,
        researches: this.moreServices,
      });
      await this.$store.dispatch(actions.DEC_LOADING);
      this.moreServices = [];
      if (ok) {
        this.load_pk(
          this.data.direction.pk,
          this.data.researches.map((r) => r.pk),
        );
        this.$root.$emit('msg', 'ok', `Добавлено услуг: ${pks.length}`);
      } else {
        this.$root.$emit('msg', 'error', message);
      }
    },
    unload() {
      if (!this.has_changed || this.directionFormProps) {
        return undefined;
      }

      return 'Возможно имеются несохраненные изменения! Вы уверены, что хотите покинуть страницу?';
    },
    async load_location() {
      if (!this.has_loc) {
        return;
      }
      if (!this.loc_timer) {
        this.loc_timer = setInterval(() => this.load_location(), 120000);
      }
      this.location.loading = true;
      try {
        this.location.data = (
          await usersPoint.loadLocation({ date: this.td }).catch((e) => {
            // eslint-disable-next-line no-console
            console.error(e);
            return { data: [] };
          })
        ).data;
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.location.data = [];
      }
      this.location.loading = false;
    },
    async load_location_internal() {
      if (!this.schedule_in_protocol) {
        return;
      }
      this.location.loading = true;
      if (this.location.resources.length === 0) {
        const { pk, options } = await this.$api('/schedule/get-first-user-resource?onlyMe=1');

        if (options.length === 0) {
          this.location.loading = false;
          return;
        }

        this.location.resource = pk;
        this.location.resources = options;
      }

      if (!this.loc_timer) {
        this.loc_timer = setInterval(() => this.load_location_internal(), 120000);
      }
      try {
        if (this.location.resource) {
          const {
            days, startTime, endTime, services,
          } = await this.$api('/schedule/days', {
            displayDays: 1,
            date: this.td,
            resource: this.location.resource,
          });
          this.location.data = days;
          this.location.startTime = startTime;
          this.location.endTime = endTime;
          this.location.services = services;
        }
      } catch (e) {
        // eslint-disable-next-line no-console
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
      this.dreg_rows = (await this.$api('patients/individuals/load-dreg', this.data.patient, 'card_pk')).rows.filter(
        (r) => !r.date_end,
      );
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
            this.$root.$emit('msg', 'ok', `Диагноз в данных статталона обновлён\n${ndiagnos}`, 3000);
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
      directionsPoint
        .paraclinicResultPatientHistory({ pk })
        .then(({ data }) => {
          this.research_history = data;
        })
        .finally(() => {
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
          if (
            (((f.required
                  && (f.value === ''
                    || f.value === '- Не выбрано'
                    || !f.value
                    || (f.field_type === 29 && (f.value.includes('"address": ""') || f.value.includes('"address":""')))))
                || this.tableFieldsErrors[f.pk])
              && vField(g, research.research.groups, f.visibility, this.data.patient))
            || (f.controlParam && !vField(g, research.research.groups, f.controlParam, this.data.patient))
            || (f.title === 'Регистрационный номер' && f.value !== this.data.direction.additionalNumber)
          ) {
            l.push((g.title !== '' ? `${g.title} ` : '') + (f.title === '' ? `поле ${n}` : f.title));
          }
        }
      }

      if (research.research.is_doc_refferal) {
        for (const [key, value] of Object.entries(this.requiredStattalonFields)) {
          if (!research[key] || research[key] === -1) {
            l.push(value);
          }
        }
      }

      const keysData = Object.keys(this.researchesPkRequiredStattalonFields).map(key => Number(key));
      if (keysData.includes(research.research.pk)) {
        for (const [key, value] of Object.entries(this.researchesPkRequiredStattalonFields[research.research.pk])) {
          if (!research[key] || research[key] === -1) {
            l.push(value);
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
      patientsPoint
        .loadAnamnesis(this.data.patient, 'card_pk')
        .then((data) => {
          this.anamnesis_data = data;
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.anamnesis_edit = true;
        });
    },
    load_history() {
      if (this.directionFormProps) {
        return;
      }
      this.directions_history = [];
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint
        .paraclinicResultUserHistory(this, 'date')
        .then((data) => {
          this.directions_history = data.directions;
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
    },
    reload_if_need() {
      if (this.date === moment().format('DD.MM.YYYY')) {
        this.load_history();
      }
    },
    load_pk(pk, withoutIssledovaniye = null) {
      this.pk = `${pk}`;
      return this.load(withoutIssledovaniye);
    },
    async load(withoutIssledovaniye = null) {
      if (!withoutIssledovaniye) {
        if (
          this.has_changed
          // eslint-disable-next-line no-alert,no-restricted-globals
          && !confirm('Возможно имеются несохраненные изменения! Вы действительно хотите закрыть текущий протокол?')
        ) {
          return;
        }
        this.clear(true);
      }
      await this.$store.dispatch(actions.INC_LOADING);
      this.getCurrentTime();
      await directionsPoint
        .getParaclinicForm({
          pk: this.pk_c,
          searchMode: this.searchMode,
          withoutIssledovaniye,
          year: this.selectedYearValue,
        }).then((data) => {
          if (withoutIssledovaniye) {
            this.data.researches = [...this.data.researches, ...data.researches];
            return;
          }
          if (data.ok) {
            this.tnd = moment().add(1, 'day').format('YYYY-MM-DD');
            this.td_m_year = moment().subtract(1, 'year').format('YYYY-MM-DD');
            this.dreg_rows_loading = false;
            this.benefit_rows_loading = false;
            this.dreg_rows = [];
            this.benefit_rows = [];
            this.pk = '';
            this.data = data;
            if (!data.patient?.has_snils) {
              this.$root.$emit('msg', 'error', 'У пациента не заполнен СНИЛС!');
            }
            this.sidebarIsOpened = false;
            this.hasEDSigns = false;
            this.hasPreselectOk = false;
            setTimeout(async () => {
              this.$root.$emit('open-pk', data.direction.pk);
              for (let i = 0; i < 10; i++) {
                await new Promise((r) => {
                  setTimeout(() => r(1), 100);
                });
                if (this.hasPreselectOk) {
                  break;
                }
              }
              await new Promise((r) => {
                setTimeout(() => r(1), 300);
              });
              this.$root.$emit('preselect-args', { card_pk: data.patient.card_pk, base_pk: data.patient.base });
              await new Promise((r) => {
                setTimeout(() => r(1), 300);
              });
              this.$root.$emit('preselect-args', { card_pk: data.patient.card_pk, base_pk: data.patient.base });
            }, 100);
            if (data.card_internal && data.status_disp === 'need' && data.has_doc_referral) {
              this.$root.$emit('msg', 'error', 'Диспансеризация не пройдена');
            }
            this.changed = false;
          } else {
            this.$root.$emit('msg', 'error', data.message);
          }
        })
        .finally(() => {
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
      directionsPoint
        .paraclinicResultSave({
          data: {
            ...iss,
            direction: this.data.direction,
            coExecutor: this.data.direction.coExecutor,
          },
          with_confirm: false,
          visibility_state: this.visibility_state(iss),
        })
        .then((data) => {
          if (data.ok) {
            this.$root.$emit('msg', 'ok', 'Сохранено');
            // eslint-disable-next-line no-param-reassign
            iss.saved = true;
            if (data.execData) {
              // eslint-disable-next-line no-param-reassign
              iss.whoSaved = data.execData.whoSaved;
              // eslint-disable-next-line no-param-reassign
              iss.whoConfirmed = data.execData.whoConfirmed;
              // eslint-disable-next-line no-param-reassign
              iss.whoExecuted = data.execData.whoExecuted;
            }
            this.data.direction.amd = data.amd;
            this.data.direction.amd_number = data.amd_number;
            this.reload_if_need();
            this.changed = false;
            this.$root.$emit('result-saved');
            this.$root.$emit('change-document-state');
          } else {
            this.$root.$emit('msg', 'error', data.message);
          }
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.inserted = true;
          this.load_location();
          this.load_location_internal();
        });
    },
    save_and_confirm(iss) {
      this.hide_results();
      this.inserted = false;
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint
        .paraclinicResultSave({
          data: {
            ...iss,
            direction: this.data.direction,
            coExecutor: this.data.direction.coExecutor,
          },
          with_confirm: true,
          visibility_state: this.visibility_state(iss),
        })
        .then((data) => {
          if (data.ok) {
            this.$root.$emit('msg', 'ok', 'Сохранено');
            this.$root.$emit('msg', 'ok', 'Подтверждено');

            if (iss.work_by) {
              this.workFromHistory = [iss.work_by, ...this.workFromHistory.filter((x) => x !== iss.work_by).slice(0, 5)];
            }
            localStorage.setItem('results-paraclinic:work-from-history', JSON.stringify(this.workFromHistory));

            // eslint-disable-next-line no-param-reassign
            iss.saved = true;
            // eslint-disable-next-line no-param-reassign
            iss.allow_reset_confirm = true;
            // eslint-disable-next-line no-param-reassign
            iss.confirmed = true;
            if (data.execData) {
              // eslint-disable-next-line no-param-reassign
              iss.whoSaved = data.execData.whoSaved;
              // eslint-disable-next-line no-param-reassign
              iss.whoConfirmed = data.execData.whoConfirmed;
              // eslint-disable-next-line no-param-reassign
              iss.whoExecuted = data.execData.whoExecuted;
            }
            this.data.direction.amd = data.amd;
            this.data.direction.amd_number = data.amd_number;
            this.data.direction.all_confirmed = this.data.researches.every((r) => Boolean(r.confirmed));
            for (const r of this.data.researches) {
              r.confirmed_at = data.confirmed_at;
            }
            this.reload_if_need();
            this.changed = false;
            this.$root.$emit('change-document-state');
          } else {
            this.$root.$emit('msg', 'error', data.message);
          }
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.inserted = true;
          this.load_location();
          this.load_location_internal();
          this.$root.$emit('open-pk', this.data.direction.pk);
        });
    },
    confirm(iss) {
      this.hide_results();
      this.inserted = false;
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint
        .paraclinicResultConfirm({ iss_pk: iss.pk })
        .then((data) => {
          if (data.ok) {
            this.$root.$emit('msg', 'ok', 'Подтверждено');
            // eslint-disable-next-line no-param-reassign
            iss.confirmed = true;
            // eslint-disable-next-line no-param-reassign
            iss.allow_reset_confirm = true;
            this.data.direction.amd = data.amd;
            this.data.direction.amd_number = data.amd_number;
            this.data.direction.all_confirmed = this.data.researches.every((r) => Boolean(r.confirmed));
            for (const r of this.data.researches) {
              r.confirmed_at = data.confirmed_at;
            }
            this.reload_if_need();
            this.changed = false;
            this.$root.$emit('change-document-state');
          } else {
            this.$root.$emit('msg', 'error', data.message);
          }
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.inserted = true;
          this.load_location();
          this.load_location_internal();
          this.$root.$emit('open-pk', this.data.direction.pk);
        });
    },
    async reset_confirm(iss) {
      this.hide_results();

      try {
        const moreMessage = this.hasEDSigns ? 'ИМЕЮТСЯ ЭЛЕКТРОННЫЕ ПОДПИСИ! ' : '';
        await this.$dialog.confirm(`${moreMessage}Подтвердите сброс подтверждения услуги «${iss.research.title}»`);
      } catch (_) {
        return;
      }

      this.inserted = false;
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await directionsPoint.paraclinicResultConfirmReset({ iss_pk: iss.pk });
      if (data.ok) {
        this.$root.$emit('msg', 'ok', 'Подтверждение сброшено');
        // eslint-disable-next-line no-param-reassign
        iss.confirmed = false;
        // eslint-disable-next-line no-param-reassign
        iss.whoConfirmed = null;
        // eslint-disable-next-line no-param-reassign
        iss.work_by = null;
        // eslint-disable-next-line no-param-reassign
        iss.whoExecuted = null;
        this.data.direction.amd = 'not_need';
        this.data.direction.all_confirmed = this.data.researches.every((r) => Boolean(r.confirmed));
        if (this.hasEDSigns) {
          this.$root.$emit('EDS:archive-document');
        }
        for (const r of this.data.researches) {
          r.confirmed_at = null;
        }
        this.reload_if_need();
        this.changed = false;
        this.$root.$emit('change-document-state');
      } else {
        this.$root.$emit('msg', 'error', data.message);
      }
      this.$root.$emit('open-pk', this.data.direction.pk);
      await this.$store.dispatch(actions.DEC_LOADING);
      this.inserted = true;
      this.load_location();
      this.load_location_internal();
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
      this.tableFieldsErrors = {};
      this.moreServices = [];
      cleanCaches();
      this.$root.$emit('preselect-args', null);
      this.$root.$emit('open-pk', -1);
    },
    print_direction(pk) {
      this.$root.$emit('print:directions', [pk]);
    },
    print_results(pk) {
      this.$root.$emit('print:results', [pk]);
    },
    print_example(pk) {
      this.$root.$emit('print:example', [pk]);
    },
    copy_results(row, pk) {
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint
        .paraclinicDataByFields({ pk, pk_dest: row.pk })
        .then(({ data }) => {
          this.hide_results();
          this.replace_fields_values(row, data);
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
    },
    load_template(row, pk) {
      this.$store.dispatch(actions.INC_LOADING);
      researchesPoint
        .getTemplateData({ pk: parseInt(pk, 10) })
        .then(({ data: { fields: data, title } }) => {
          this.template_fields_values(row, data, title);
        })
        .finally(() => {
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
          query: `ecp:${this.slot.data.patient_uid}`,
          list_all_cards: false,
        });
        const cardPk = (cards.results || [{}])[0].pk;
        const { direction } = await usersPoint.fillSlot({ slot: { ...this.slot, card_pk: cardPk } });
        await this.$store.dispatch(actions.DEC_LOADING);
        this.load_location();
        this.load_location_internal();
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
      this.$dialog
        .alert(title, {
          view: 'replace-append-modal',
        })
        .then(({ data }) => {
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
      this.$root.$emit('checkTables');
    },
    append_fields_values(row, data) {
      for (const g of row.research.groups) {
        for (const f of g.fields) {
          if (![1, 3, 16, 17, 20, 13, 14, 11, 2, 32, 33, 36, 27, 28, 29, 30, 37, 35].includes(f.field_type) && data[f.pk]) {
            this.append_value(f, data[f.pk]);
          }
        }
      }
      this.$root.$emit('checkTables');
    },
    clear_vals(row) {
      this.$dialog.confirm('Вы действительно хотите очистить результаты?').then(() => {
        this.$root.$emit('msg', 'ok', 'Очищено');
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
      let addVal = value;
      if (addVal !== ',' && addVal !== '.') {
        if (
          field.value.length > 0
          && field.value[field.value.length - 1] !== ' '
          && field.value[field.value.length - 1] !== '\n'
        ) {
          if (field.value[field.value.length - 1] === '.') {
            addVal = addVal.replace(/./, addVal.charAt(0).toUpperCase());
          }
          addVal = ` ${addVal}`;
        } else if (
          (field.value.length === 0
            || (field.value.length >= 2
              && field.value[field.value.length - 2] === '.'
              && field.value[field.value.length - 1] === '\n'))
          && field.title === ''
        ) {
          addVal = addVal.replace(/./, addVal.charAt(0).toUpperCase());
        }
      }
      // eslint-disable-next-line no-param-reassign
      field.value += addVal;
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
        this.$root.$emit('msg', 'ok', 'Отправка запланирована');
        this.reload_if_need();
      } else {
        this.$root.$emit('msg', 'error', 'Не найдены подходящие направления');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async reset_amd(pks) {
      try {
        await this.$dialog.confirm('Подтвердите сброс статуса отправки в ЕГИСЗ');
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
      this.$root.$emit('msg', 'ok', 'Отправка запланирована');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    updateValue(field, prop) {
      return (newValue) => {
        // eslint-disable-next-line no-param-reassign
        field[prop] = newValue;
      };
    },
    enter_field(...args) {
      return enterField.apply(this, args);
    },
    leave_field(...args) {
      return leaveField.apply(this, args);
    },
    needFillWorkBy(row) {
      if (!this.can_confirm_by_other_user || row.confirmed) {
        return false;
      }
      return !row.work_by;
    },
  },

};
</script>

<style scoped lang="scss">
.results-root {
  position: absolute;
  top: 36px;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: stretch;
  flex-direction: row;
  flex-wrap: nowrap;
  align-content: stretch;
  overflow-x: hidden;

  &.embedded {
    top: 0;
  }

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
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
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
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
      }
    }

    .burger-lines {
      top: 290px;
      bottom: 10px;
      left: 17px;

      &,
      &::before,
      &::after {
        position: absolute;
        width: 1px;
        background-color: rgba(#fff, 0.1);
      }

      &::before,
      &::after {
        top: 0;
        bottom: 0;
        content: '';
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
    background-color: rgba(#000, 0.6);
    backdrop-filter: blur(3px);
    z-index: 9;
    display: flex;
    align-items: center;
    justify-content: center;
    padding-left: 341px;

    &-inner {
      color: #fff;
      text-shadow: 0 0 4px rgba(#000, 0.6);
    }
  }
}

@media (min-width: 1367px) {
  .burger,
  .backdrop {
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
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);

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

  &.embedded {
    padding-left: 0 !important;
    width: 100% !important;
  }
}

.results-top {
  border-bottom: 1px solid #b1b1b1;
  height: 68px;
  padding: 5px;
}

.results-top > div {
  font-family: 'Courier New', Courier, monospace !important;
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

  &.withFiles {
    .research-left {
      width: calc(100% - 540px);
    }
    .research-right {
      width: 540px;
    }
  }
}

.research-left {
  position: relative;
  text-align: left;
  width: calc(100% - 430px);

  @media (min-width: 1440px) {
    width: calc(100% - 500px);
  }
}

.research-right {
  text-align: right;
  width: 430px;
  margin-top: -5px;
  margin-right: -5px;
  margin-bottom: -5px;
  white-space: nowrap;

  @media (min-width: 1440px) {
    width: 500px;
  }

  .btn,
  ::v-deep .file-btn {
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
  margin-right: -130px;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);

  &-embedded {
    margin-top: -65px;
    margin-left: -130px;
  }

  ul {
    padding-left: 20px;
    margin: 0;

    li {
      font-weight: normal;

      a {
        font-weight: bold;
        display: inline-block;
        padding: 2px 4px;
        background: rgba(#000, 0.03);
        border-radius: 4px;
        margin-left: 3px;

        &:hover {
          background: rgba(#000, 0.1);
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

.embeddedFull {
  .results-editor {
    height: 100%;
  }
}

.sidebar-top {
  .dropdown-toggle {
    border-radius: 0;
    padding: 6px;
    font-size: 12px;
    height: 34px;
  }
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
  margin-bottom: 10px;

  button {
    align-self: stretch;
    border-radius: 0;
  }

  div {
    align-self: stretch;
  }
}

.res-title {
  padding: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.direction,
.sd {
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

  .location-internal {
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

    .sub-title {
      height: 34px;
      position: relative;
      background: #eaeaea;
    }

    .inner {
      position: relative;
      height: calc(100% - 54px);
      overflow-y: auto;
      overflow-x: hidden;

      &.stat_btn {
        height: calc(100% - 88px);
      }
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

      th,
      td {
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

    &_amd,
    &_stat {
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
  text-shadow: 0 0 4px rgba(#da3b6c, 0.6);
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
  transition: 0.15s linear all;
  margin: 0;
  font-size: 12px;
  min-width: 0;
  flex: 0 1 auto;
  width: 25%;
  height: 34px;
  border: 1px solid #6c7a89 !important;
  cursor: pointer;
  text-align: left;
  outline: transparent;

  &.active {
    background: #049372 !important;
    color: #fff;
  }

  &:hover {
    box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.8) !important;
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

  ::v-deep th,
  ::v-deep td {
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

  &_need,
  &_need:focus,
  &_need:active,
  &_need:hover {
    color: #f7581c !important;
    text-shadow: 0 0 4px rgba(#f7581c, 0.6);
    font-weight: bold;
  }

  &_finished,
  &_finished:focus,
  &_finished:active,
  &_finished:hover {
    color: #049372 !important;
    text-shadow: 0 0 4px rgba(#049372, 0.6);
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

  &_need,
  &_need a {
    color: #ff0000 !important;
  }

  &_finished,
  &_finished a {
    color: #049372 !important;
  }

  a {
    text-decoration: dotted underline;

    &:hover {
      text-decoration: none;
    }
  }
}

.status,
.control-row .amd {
  padding: 5px;
}

.status {
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-none {
  color: #cf3a24;
}

.amd {
  font-weight: bold;

  &-need,
  &-error {
    color: #cf3a24;
  }

  &-planned {
    color: #d9be00;
  }

  &-ok {
    color: #049372;
  }
}

label.field-title {
  font-weight: normal;
}

textarea {
  resize: vertical;
}

.simple-value {
  padding: 5px;

  ul {
    margin: 0;
    padding-left: 20px;
  }
}
</style>
