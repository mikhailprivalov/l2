<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="680px"
    width="100%"
    margin-left-right="auto"
    margin-top
    @close="hide_modal"
  >
    <span slot="header">Регистратура {{ system }}</span>
    <div
      slot="body"
      style="min-height: 200px"
      class="registry-body"
    >
      <form
        autocomplete="off"
        class="row"
        onsubmit.prevent
      >
        <input
          type="hidden"
          autocomplete="off"
        >
        <div class="col-xs-6 col-form left">
          <div class="form-row">
            <div class="row-t">
              Фамилия
            </div>
            <TypeAhead
              ref="f"
              v-model="card.family"
              :delay-time="100"
              :get-response="getResponse"
              :highlighting="highlighting"
              :limit="10"
              name="f"
              :min-chars="1"
              :on-hit="onHit('family')"
              :select-first="true"
              maxlength="36"
              src="/api/autocomplete?value=:keyword&type=family"
            />
          </div>
          <div class="form-row">
            <div class="row-t">
              Имя
            </div>
            <TypeAhead
              ref="n"
              v-model="card.name"
              :delay-time="100"
              :get-response="getResponse"
              :highlighting="highlighting"
              :limit="10"
              name="n"
              :min-chars="1"
              :on-hit="onHit('name')"
              :select-first="true"
              maxlength="36"
              src="/api/autocomplete?value=:keyword&type=name"
            />
          </div>
          <div class="form-row">
            <div class="row-t">
              Отчество
            </div>
            <TypeAhead
              ref="pn"
              v-model="card.patronymic"
              :delay-time="100"
              :get-response="getResponse"
              :highlighting="highlighting"
              :limit="10"
              name="pn"
              :min-chars="1"
              :on-hit="onHit('patronymic')"
              :select-first="true"
              maxlength="36"
              src="/api/autocomplete?value=:keyword&type=patronymic"
            />
          </div>
        </div>
        <div class="col-xs-6 col-form">
          <div class="form-row">
            <div class="row-t">
              Карта
            </div>
            <div
              class="row-v"
              style="font-weight: bold"
            >
              {{ card_pk >= 0 ? (card.id ? card.number : 'загрузка') : 'НОВАЯ' }}
            </div>
          </div>
          <div class="form-row">
            <div class="row-t">
              Дата рождения
            </div>
            <input
              v-model="card.birthday"
              class="form-control"
              type="date"
              autocomplete="off"
            >
          </div>
          <div class="form-row">
            <div class="row-t">
              Пол
            </div>
            <RadioField
              v-model="card.sex"
              :variants="GENDERS"
              full-width
              uppercase
            />
          </div>
        </div>
      </form>
      <div
        v-if="card_pk < 0"
        class="row"
      >
        <div class="col-xs-6">
          <label
            class="info-row"
            style="cursor: pointer"
          >
            <input
              :checked="card.new_individual || individuals.length === 0"
              type="checkbox"
              @click="toggleNewIndividual"
            > –
            новое физлицо
          </label>
        </div>
        <div class="col-xs-6">
          <div
            v-if="loading"
            class="info-row"
          >
            Поиск пациентов в {{ system }}
            <template v-if="l2_tfoms">
              и в ТФОМС
            </template>
            ...
          </div>
          <div
            v-else
            class="info-row"
          >
            Найдено физлиц в {{ system }}
            <template v-if="l2_tfoms">
              и ТФОМС
            </template>
            : {{ individuals.length }}
          </div>
        </div>
        <div
          v-if="!card.new_individual && individuals.map((i) => i.l2_cards.length).reduce((a, b) => a + b, 0) > 0"
          class="col-xs-12"
        >
          <div
            class="alert-warning"
            style="padding: 10px"
          >
            <strong>Внимание:</strong> найдены существующие карты или созданы автоматически.<br>
            Выберите подходящую, нажав на номер карты или продолжайте создание новой при необходимости или не совпадении физ. лиц
          </div>
        </div>
        <div
          v-if="!card.new_individual && individuals.length > 0"
          class="col-xs-12"
        >
          <div
            v-for="i in individuals"
            :key="i.pk"
            class="info-row individual"
            @click="select_individual(i.pk)"
          >
            <input
              :checked="i.pk === card.individual"
              type="checkbox"
            > {{ i.fio }}<br>
            <table class="table table-bordered table-condensed">
              <thead>
                <tr>
                  <th>Тип</th>
                  <th>Серия</th>
                  <th>Номер</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="d in i.docs"
                  :key="`${d.type_title}_${d.serial}_${d.number}`"
                >
                  <td>{{ d.type_title }}</td>
                  <td>{{ d.serial }}</td>
                  <td>{{ d.number }}</td>
                </tr>
                <tr v-if="i.l2_cards.length > 0">
                  <th>Активные карты {{ system }}</th>
                  <td colspan="2">
                    <div
                      v-for="c in i.l2_cards"
                      :key="c.pk"
                    >
                      <a
                        v-tippy
                        :href="`/ui/directions?card_pk=${c.pk}&base_pk=${base_pk}&open_edit=true`"
                        class="a-under c-pointer"
                        title="Открыть существующую карту"
                      >
                        <strong>{{ c.number }}</strong>
                      </a>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div
        v-else
        class="row"
      >
        <div
          v-if="l2_tfoms"
          class="col-xs-6"
        >
          <div class="info-row">
            <template v-if="card.tfoms_idp || card.tfoms_enp">
              Есть связь с ТФОМС
            </template>
            <template v-else>
              Не связано с ТФОМС
            </template>
            <template v-if="time_tfoms_last_sync">
              ({{ time_tfoms_last_sync }})
            </template>
            <a
              href="#"
              class="a-under"
              tabindex="-1"
              @click.prevent="sync_tfoms"
            >сверка</a>
          </div>
        </div>
        <div
          class="text-right"
          :class="{ 'col-xs-6': l2_tfoms, 'col-xs-12': !l2_tfoms }"
        >
          <div class="info-row">
            Связь с РМИС – {{ card.has_rmis_card ? 'ЕСТЬ' : 'НЕТ' }}
            <strong v-if="card.has_rmis_card">{{ card.rmis_uid }}</strong>
            <a
              href="#"
              class="a-under"
              tabindex="-1"
              @click.prevent="sync_rmis"
            >синхронизировать</a>
          </div>
        </div>
      </div>
      <div
        class="row"
      >
        <div
          class="col-xs-6"
        >
          <div class="info-row">
            <template v-if="card.ecp_id">
              ЕЦП ИД {{ card.ecp_id }}
            </template>
          </div>
        </div>
      </div>
      <div
        v-if="card_pk < 0"
        class="row"
      >
        <div class="col-xs-12 text-center">
          Для настройки документов и других параметров сохраните карту
        </div>
      </div>
      <div v-else>
        <div
          class="row"
          style="margin-bottom: 10px"
        >
          <div class="col-xs-12 col-form mid">
            <div class="form-row-address">
              <div class="row-address-header">
                Адрес регистрации
              </div>
              <AddressFiasField
                ref="ar"
                v-model="card.main_address_full"
                name="ar"
                :form="true"
                edit-title="Адрес регистрации"
              />
            </div>
            <div class="form-row-address">
              <div class="row-address-header">
                Адрес проживания
              </div>
              <AddressFiasField
                ref="af"
                v-model="card.fact_address_full"
                name="af"
                :form="true"
                :receive-copy="true"
                edit-title="Адрес проживания"
              >
                <template #input-group-append>
                  <button
                    v-if="card.main_address_full"
                    v-tippy
                    title="Скопировать из адреса регистрации"
                    class="btn btn-blue-nb nbr btn-address"
                    type="button"
                    tabindex="-1"
                    @click="$root.$emit('address-copy-fast', card.main_address_full)"
                  >
                    <i class="fa fa-paste" />
                  </button>
                </template>
                <template #extended-edit>
                  <AddressFiasField
                    v-if="card.main_address_full"
                    v-model="card.main_address_full"
                    :disabled="true"
                    :area-full="true"
                    :hide-if-empty="true"
                  >
                    <template #input-group-disabled-prepend>
                      <span class="input-group-addon">
                        <span class="input-group-addon-inner"> Адрес регистрации </span>
                      </span>
                    </template>
                    <template #input-group-disabled-append>
                      <span class="input-group-btn">
                        <button
                          v-tippy
                          title="Скопировать адрес регистрации в адрес проживания"
                          class="btn btn-blue-nb"
                          type="button"
                          tabindex="-1"
                          @click="$root.$emit('address-copy', card.main_address_full)"
                        >
                          скопировать
                        </button>
                      </span>
                    </template>
                  </AddressFiasField>
                </template>
              </AddressFiasField>
            </div>
            <div class="form-row sm-f">
              <div class="row-t">
                Участок
              </div>
              <select
                v-model="card.district"
                class="form-control"
              >
                <option
                  v-for="c in card.districts"
                  :key="c.id"
                  :value="c.id"
                >
                  {{ c.title }}
                </option>
              </select>
            </div>
            <div
              v-if="card.sex === 'ж'"
              class="form-row sm-f"
            >
              <div class="row-t">
                Гинекологический участок
              </div>
              <select
                v-model="card.ginekolog_district"
                class="form-control"
              >
                <option
                  v-for="c in card.gin_districts"
                  :key="c.id"
                  :value="c.id"
                >
                  {{ c.title }}
                </option>
              </select>
            </div>
            <div class="form-row sm-f">
              <div
                class="row-t"
              >
                <input
                  v-model="card.custom_workplace"
                  v-tippy="{ placement: 'bottom', arrow: true }"
                  type="checkbox"
                  title="Ручной ввод названия"
                  style="height: auto; flex: 0 23px"
                >
                Место работы (учёбы)
              </div>
              <TypeAhead
                v-if="card.custom_workplace"
                ref="wp"
                v-model="card.work_place"
                :delay-time="100"
                :get-response="getResponse"
                :highlighting="highlighting"
                :limit="10"
                :min-chars="1"
                :on-hit="onHit('work_place')"
                :select-first="true"
                maxlength="128"
                src="/api/autocomplete?value=:keyword&type=work_place"
              />
              <div
                v-else
                v-tippy="{ placement: 'bottom', arrow: true }"
                style="width: 65%"
                type="checkbox"
                :title="card.work_place_db_title"
              >
                <Treeselect
                  v-model="card.work_place_db"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  class="treeselect-wide treeselect-26px treeselect-nbr"
                  :async="true"
                  :append-to-body="true"
                  :clearable="true"
                  :z-index="5001"
                  placeholder="Укажите организацию"
                  :load-options="loadCompanies"
                  loading-text="Загрузка"
                  no-results-text="Не найдено"
                  search-prompt-text="Начните писать для поиска"
                  :cache-options="false"
                  open-direction="top"
                  :open-on-focus="true"
                  @input="changeCompany(card.work_place_db)"
                >
                  <div
                    slot="value-label"
                    slot-scope="{ node }"
                  >
                    {{ node.raw.label || card.work_place_db_title }}
                  </div>
                </Treeselect>
              </div>
            </div>
            <div class="form-row sm-f">
              <div class="row-t">
                Должность
              </div>
              <TypeAhead
                ref="wpos"
                v-model="card.work_position"
                :delay-time="100"
                :get-response="getResponse"
                :highlighting="highlighting"
                :limit="10"
                :min-chars="1"
                :on-hit="onHit('work_position')"
                :select-first="true"
                maxlength="128"
                src="/api/autocomplete?value=:keyword&type=work_position"
              />
            </div>
            <div class="form-row sm-f">
              <div class="row-t">
                Отдел
              </div>
              <Treeselect
                v-model="card.work_department_db"
                :multiple="false"
                class="treeselect-wide treeselect-26px treeselect-nbr"
                :z-index="5001"
                placeholder="Укажите отдел"
                :options="companyDepartments"
              />
            </div>
            <div class="form-row sm-f">
              <div class="row-t">
                Основной диагноз
              </div>
              <TypeAhead
                ref="md"
                v-model="card.main_diagnosis"
                :delay-time="100"
                :get-response="getResponse"
                :highlighting="highlighting"
                :limit="10"
                :min-chars="1"
                :on-hit="onHit('main_diagnosis')"
                :select-first="true"
                maxlength="36"
                src="/api/autocomplete?value=:keyword&type=main_diagnosis"
              />
            </div>
          </div>
        </div>
        <table class="table table-bordered table-condensed table-sm-pd">
          <colgroup>
            <col width="70">
            <col>
            <col>
            <col>
            <col>
            <col>
          </colgroup>
          <thead>
            <tr>
              <th>ПРИОР.</th>
              <th>Тип документа</th>
              <th>Серия</th>
              <th>Номер</th>
              <th>Действие</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="d in card.docs"
              :key="d.id"
              :title="d.who_give"
              :class="{ nonPrior: card.main_docs[d.document_type] !== d.id, prior: card.main_docs[d.document_type] === d.id }"
            >
              <td>
                <input
                  type="radio"
                  :name="`card-doc${d.document_type}`"
                  :checked="card.main_docs[d.document_type] === d.id"
                  @click="update_cdu(d.id)"
                >
              </td>
              <td>
                {{ d.type_title }}
              </td>
              <td>
                {{ d.serial }}
              </td>
              <td>
                {{ d.number }}
              </td>
              <td>
                {{ d.is_active ? 'действ.' : 'не действителен' }}
              </td>
              <td>
                <a
                  v-if="!d.from_rmis"
                  href="#"
                  @click.prevent="edit_document(d.id)"
                ><i class="fa fa-pencil" /></a>
                <span v-else>импорт</span>
              </td>
            </tr>
            <tr>
              <td
                class="text-center"
                colspan="6"
              >
                <a
                  href="#"
                  @click.prevent="edit_document(-1)"
                >добавить документ</a>
              </td>
            </tr>
          </tbody>
        </table>
        <table class="table table-bordered table-condensed table-sm-pd">
          <colgroup>
            <col width="70">
            <col width="120">
            <col>
            <col width="150">
            <col width="40">
          </colgroup>
          <thead>
            <tr>
              <th>ВЫБОР</th>
              <th>Статус</th>
              <th>ФИО</th>
              <th>Докум.-основание</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="t in agent_types_excluded"
              :key="t.key"
              :class="{ nonPrior: card.who_is_agent !== t.key, prior: card.who_is_agent === t.key }"
            >
              <td>
                <input
                  v-if="!card.excluded_types.includes(t.key)"
                  type="radio"
                  name="agent"
                  :checked="card.who_is_agent === t.key"
                  @click="update_wia(t.key)"
                >
              </td>
              <td>
                {{ t.title }}
              </td>
              <td :colspan="agent_need_doc(t.key) ? 1 : 2">
                {{ card[t.key] }}
              </td>
              <td v-if="agent_need_doc(t.key)">
                {{ card[`${t.key}_doc_auth`] }}
              </td>
              <td>
                <a
                  href="#"
                  @click.prevent="edit_agent(t.key)"
                ><i class="fa fa-pencil" /></a>
              </td>
            </tr>
            <tr :class="{ nonPrior: card.who_is_agent !== '', prior: card.who_is_agent === '' }">
              <td>
                <input
                  type="radio"
                  name="agent"
                  :checked="card.who_is_agent === ''"
                  @click="update_wia('')"
                >
              </td>
              <td colspan="4">
                НЕ ВЫБРАНО
              </td>
            </tr>
            <tr
              v-for="t in card.agent_types"
              v-if="/*eslint-disable-line vue/no-use-v-if-with-v-for*/ card.excluded_types.includes(t.key)"
              :key="t.key"
              class="prior"
            >
              <td />
              <td>
                {{ t.title }}
              </td>
              <td :colspan="agent_need_doc(t.key) ? 1 : 2">
                {{ card[t.key] }}
              </td>
              <td v-if="agent_need_doc(t.key)">
                {{ card[`${t.key}_doc_auth`] }}
              </td>
              <td>
                <a
                  href="#"
                  @click.prevent="edit_agent(t.key)"
                ><i class="fa fa-pencil" /></a>
              </td>
            </tr>
          </tbody>
        </table>
        <div
          class="row"
          style="margin-bottom: 10px"
        >
          <div class="col-xs-12 col-form mid">
            <div class="form-row sm-f">
              <div class="row-t">
                Телефон
              </div>
              <input
                v-model="card.phone"
                v-mask="'8 999 9999999'"
                class="form-control"
              >
            </div>
          </div>
        </div>
        <div
          v-if="l2_send_patients_email_results"
          class="row"
          style="margin-bottom: 10px"
        >
          <div class="col-xs-12 col-form mid">
            <div class="form-row sm-f">
              <div class="row-t">
                <input
                  v-model="card.send_to_email"
                  v-tippy="{ placement: 'bottom', arrow: true }"
                  type="checkbox"
                  title="Отправлять результаты на почту"
                  style="height: auto; flex: 0 23px"
                >
                Email
              </div>
              <input
                v-model.trim="card.email"
                type="email"
                class="form-control"
                :disabled="!card.send_to_email"
                :placeholder="card.send_to_email ? 'введите адрес' : ''"
              >
            </div>
          </div>
        </div>
        <div
          class="row"
          style="margin-bottom: 10px"
        >
          <div class="col-xs-12 col-form mid">
            <div class="form-row sm-f">
              <div class="row-t">
                Кому доверяю
              </div>
              <input
                v-model="card.contactTrustHealth"
                class="form-control"
                maxlength="20"
              >
            </div>
          </div>
        </div>
        <div
          class="row"
          style="margin-bottom: 10px"
        >
          <div class="col-xs-12 col-form mid">
            <div class="form-row sm-f">
              <div class="row-t">
                Номер карты ТФОМС
              </div>
              <input
                v-model="card.number_poli"
                class="form-control"
                maxlength="20"
              >
            </div>
          </div>
        </div>
        <div
          class="row"
          style="margin-bottom: 10px"
        >
          <div class="col-xs-12 col-form mid">
            <div class="form-row sm-f">
              <div class="row-t">
                Место хранения карты
              </div>
              <Treeselect
                v-model="card.room_location_db"
                :multiple="false"
                class="treeselect-wide treeselect-26px treeselect-nbr"
                :z-index="5002"
                placeholder="Место хранения"
                :options="roomLocations"
              />
            </div>
          </div>
        </div>
        <div
          class="row"
          style="margin-bottom: 10px"
        >
          <div class="col-xs-12 col-form mid">
            <div class="form-row sm-f">
              <div class="row-t">
                Фактор вредности
              </div>
              <TypeAhead
                ref="n"
                v-model="card.harmful"
                :delay-time="100"
                :get-response="getResponse"
                :highlighting="highlighting"
                :limit="10"
                :min-chars="1"
                :on-hit="onHit('harmful')"
                :select-first="true"
                maxlength="255"
                src="/api/autocomplete?value=:keyword&type=harmful"
              />
            </div>
          </div>
        </div>
        <div
          v-if="l2_profcenter"
          class="row"
          style="margin-bottom: 10px"
        >
          <div
            class="col-xs-6"
            style="padding-right: 0"
          >
            <div
              class="form-row sm-f"
              style="border-right: 1px solid #434a54"
            >
              <div
                class="row-t"
                style="width: 50%; flex: 0 50%"
              >
                Номер мед.книжки
              </div>
              <select
                v-model="card.medbookType"
                class="form-control"
                style="width: 50%; flex: 0 50%"
              >
                <option
                  v-for="t in MEDBOOK_TYPES"
                  :key="t.type"
                  :value="t.type"
                >
                  {{ t.title }}
                </option>
              </select>
            </div>
          </div>
          <div
            class="col-xs-6"
            style="padding-left: 0"
          >
            <div
              class="form-row sm-f"
              style="height: 28px"
            >
              <div
                v-if="card.medbookType === 'custom'"
                class="input-group input-group-custom"
              >
                <input
                  v-model.trim="card.medbookPrefix"
                  type="text"
                  class="form-control"
                  maxlength="1"
                  placeholder="Префикс"
                >
                <input
                  v-model="card.medbookNumberCustom"
                  type="number"
                  class="form-control"
                  maxlength="16"
                  :max="medbook_auto_start - 1"
                  min="1"
                  :placeholder="`Номер книжки до ${medbook_auto_start}`"
                >
                <span
                  v-if="card.medbookNumberCustomOriginal && card.medbookNumberCustomOriginal !== card.medbookNumberCustom"
                  class="input-group-btn"
                >
                  <button
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    class="btn row-t-btn"
                    title="Вернуть предыдущий номер"
                    @click="card.medbookNumberCustom = card.medbookNumberCustomOriginal"
                  >
                    <i class="fas fa-undo" />
                  </button>
                </span>
              </div>
              <div
                v-else-if="card.medbookType !== 'custom'"
                style="line-height: 26px; padding-left: 10px"
              >
                <template v-if="card.medbookType === 'auto'">
                  {{ (card.medbookTypePrev === 'auto' && card.medbookNumber) || 'Номер будет сгенерирован после сохранения' }}
                </template>
                <template v-else-if="card.medbookType === 'none' && card.medbookTypePrev !== 'none'">
                  Номер будет очищен после сохранения
                </template>
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="can_change_owner_directions"
          class="input-group form-row-simple"
          style="margin-bottom: 10px"
        >
          <div class="input-group-btn">
            <button
              type="button"
              class="btn btn-blue-nb nbr"
              @click="change_directions_owner()"
            >
              Перенести все услуги в другую карту
              <i class="glyphicon glyphicon-arrow-right" />
            </button>
          </div>
          <input
            v-model.trim="new_card_num"
            type="text"
            class="form-control"
            placeholder="Введите номер карты"
          >
        </div>

        <div
          v-if="can_change_owner_directions"
          class="form-row force-bt"
          style="margin-bottom: 10px"
        >
          <div
            v-if="card.isArchive"
            class="row-t row-t-error bold"
          >
            Карта в архиве <i class="fas fa-exclamation-circle" />
          </div>
          <div
            v-else
            class="row-t"
          >
            Карта не архивирована
          </div>
          <button
            v-if="card.isArchive"
            type="button"
            class="btn btn-blue-nb nbr button-f"
            @click="do_unarchive()"
          >
            Отменить архивацию карты
          </button>
          <button
            v-else
            type="button"
            class="btn btn-blue-nb nbr button-f"
            @click="do_archive()"
          >
            Архивировать карту
          </button>
        </div>
      </div>
      <Modal
        v-if="document_to_edit > -2"
        ref="modalDocEdit"
        show-footer="true"
        white-bg="true"
        max-width="710px"
        width="100%"
        margin-left-right="auto"
        margin-top
        @close="hide_modal_doc_edit"
      >
        <span slot="header">
          Редактор документов (карта {{ card.number }} пациента {{ card.family }} {{ card.name }} {{ card.patronymic }})
        </span>
        <div
          slot="body"
          style="min-height: 200px; padding: 10px"
          class="registry-body"
        >
          <div class="form-group">
            <label>Тип документа:</label>
            <select
              v-if="document_to_edit === -1"
              v-model="document.document_type"
            >
              <option
                v-for="dt in card.doc_types"
                :key="dt.pk"
                :value="dt.pk"
              >
                {{ dt.title }}
              </option>
            </select>
            <span v-else>{{ document.type_title }}</span>
          </div>
          <div
            v-show="doc_edit_fields.serial"
            class="form-group"
          >
            <label for="de-f2">Серия (при наличии):</label>
            <input
              id="de-f2"
              v-model="document.serial"
              class="form-control"
            >
          </div>
          <div
            v-show="is_snils"
            class="form-group"
          >
            <label for="de-f3">Номер СНИЛС:</label>
            <input
              v-if="is_snils"
              id="de-f3"
              v-model="document.number"
              v-mask="doc_edit_fields.masks.number"
              class="form-control"
            >
          </div>
          <div
            v-show="!is_snils"
            class="form-group"
          >
            <label for="de-f3-2">Номер:</label>
            <input
              id="de-f3-2"
              v-model="document.number"
              class="form-control"
            >
          </div>
          <div
            v-show="doc_edit_fields.dates"
            class="form-group"
          >
            <label for="de-f4">Дата выдачи:</label>
            <input
              id="de-f4"
              v-model="document.date_start"
              class="form-control"
              type="date"
            >
          </div>
          <div
            v-show="doc_edit_fields.dates"
            class="form-group"
          >
            <label for="de-f5">Дата окончания:</label>
            <input
              id="de-f5"
              v-model="document.date_end"
              class="form-control"
              type="date"
            >
          </div>
          <div
            v-show="doc_edit_fields.who_give"
            class="form-group str"
          >
            <label>Выдал:</label>
            <TypeAhead
              ref="dwg"
              v-model="document.who_give"
              :delay-time="100"
              :get-response="getResponse"
              :highlighting="highlighting"
              :limit="10"
              :min-chars="1"
              :on-hit="onHitDocWhoGive"
              :select-first="true"
              maxlength="128"
              :src="`/api/autocomplete?value=:keyword&type=who_give:` + document.document_type"
            />
          </div>
          <div
            class="checkbox"
            style="padding-left: 15px"
          >
            <label> <input
              v-model="document.is_active"
              type="checkbox"
            > действителен </label>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="hide_modal_doc_edit"
              >
                Отмена
              </button>
            </div>
            <div class="col-xs-4">
              <button
                :disabled="!valid_doc"
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="save_doc()"
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </Modal>
      <Modal
        v-if="agent_to_edit"
        ref="modalAgentEdit"
        show-footer="true"
        white-bg="true"
        max-width="710px"
        width="100%"
        margin-left-right="auto"
        margin-top
        @close="hide_modal_agent_edit"
      >
        <span slot="header">
          Редактор – {{ agent_type_by_key(agent_to_edit) }}&nbsp; (карта {{ card.number }} пациента {{ card.family }}
          {{ card.name }} {{ card.patronymic }})
        </span>
        <div
          slot="body"
          style="min-height: 140px"
          class="registry-body"
        >
          <div v-show="!agent_clear">
            <div style="height: 110px">
              <PatientSmallPicker
                v-model="agent_card_selected"
                :base_pk="base_pk"
              />
            </div>
            <div
              v-if="agent_need_doc(agent_to_edit)"
              class="form-group"
              style="padding: 10px"
            >
              <label for="ae-f2">Документ-основание:</label>
              <input
                id="ae-f2"
                v-model="agent_doc"
                class="form-control"
              >
            </div>
          </div>
          <div
            v-if="!!card[agent_to_edit]"
            class="checkbox"
            style="padding-left: 35px; padding-top: 10px"
          >
            <label>
              <input
                v-model="agent_clear"
                type="checkbox"
              > очистить представителя ({{ agent_type_by_key(agent_to_edit) }})
            </label>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="hide_modal_agent_edit"
              >
                Отмена
              </button>
            </div>
            <div class="col-xs-4">
              <button
                :disabled="!valid_agent"
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="save_agent()"
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-3">
          <div
            v-if="card_pk >= 0"
            class="dropup"
          >
            <button
              class="btn btn-blue-nb btn-ell dropdown-toggle"
              type="button"
              data-toggle="dropdown"
              style="width: 100%"
            >
              Печатн. формы <span class="caret" />
            </button>
            <ul class="dropdown-menu multi-level">
              <li
                v-for="f in forms"
                :key="`${f.url || '#'}_${f.title}`"
                :class="f.isGroup && 'dropdown-submenu'"
              >
                <a
                  :href="f.url || '#'"
                  :target="!f.isGroup && '_blank'"
                  class="ddm"
                >{{ f.title }}</a>
                <ul
                  v-if="f.isGroup"
                  class="dropdown-menu"
                >
                  <li
                    v-for="ff in f.forms"
                    :key="ff.url"
                  >
                    <a
                      :href="ff.url"
                      target="_blank"
                      class="ddm"
                    >{{ ff.title }}</a>
                  </li>
                </ul>
              </li>
            </ul>
          </div>
        </div>
        <div class="col-xs-2">
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="hide_modal"
          >
            Закрыть
          </button>
        </div>
        <div class="col-xs-3">
          <button
            :disabled="!valid"
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="save()"
          >
            Сохранить
          </button>
        </div>
        <div class="col-xs-4">
          <button
            :disabled="!valid"
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="save_hide_modal"
          >
            Сохранить и закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
// @ts-ignore
import TypeAhead from 'vue2-typeahead';
import moment from 'moment';
import Treeselect, { ASYNC_SEARCH } from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import _ from 'lodash';

import {
  normalizeNamePart, swapLayouts, validateSnils, valuesToString,
} from '@/utils';
import { GENDERS } from '@/constants';
import patientsPoint from '@/api/patients-point';
import Modal from '@/ui-cards/Modal.vue';
import forms from '@/forms';
import RadioField from '@/fields/RadioField.vue';
import AddressFiasField from '@/fields/AddressFiasField.vue';
import * as actions from '@/store/action-types';
import PatientSmallPicker from '@/ui-cards/PatientSmallPicker.vue';

const MEDBOOK_TYPES = [
  { type: 'none', title: 'нет' },
  { type: 'auto', title: 'авто' },
  { type: 'custom', title: 'вручную' },
];

export default {
  name: 'L2CardCreate',
  components: {
    Modal,
    TypeAhead,
    PatientSmallPicker,
    RadioField,
    Treeselect,
    AddressFiasField,
  },
  props: {
    card_pk: {
      type: Number,
      required: true,
    },
    base_pk: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      GENDERS,
      MEDBOOK_TYPES,
      card: {
        number: '',
        number_poli: '',
        main_address_full: JSON.stringify({ address: '', fias: null, details: null }),
        fact_address_full: JSON.stringify({ address: '', fias: null, details: null }),
        work_place: '',
        work_position: '',
        work_department: '',
        family: '',
        patronymic: '',
        name: '',
        main_diagnosis: '',
        sex: GENDERS[0],
        has_rmis_card: false,
        birthday: moment().format('YYYY-MM-DD'),
        individual: -1,
        new_individual: false,
        custom_workplace: false,
        docs: [],
        docs_to_delete: [],
        rmis_uid: null,
        ecp_id: null,
        work_place_db: null,
        work_department_db: null,
        room_location_db: null,
        work_place_db_title: '',
        doc_types: [],
        main_docs: {},
        districts: [],
        district: -1,
        gin_districts: [],
        ginekolog_district: -1,
        agent_types: [],
        agent_need_doc: [],
        excluded_types: [],
        who_is_agent: '',
        mother: null,
        mother_pk: null,
        father: null,
        father_pk: null,
        curator: null,
        curator_doc: null,
        curator_pk: null,
        agent: null,
        agent_doc: null,
        agent_pk: null,
        phone: '',
        email: '',
        send_to_email: false,
        harmful: '',
        tfoms_idp: null,
        tfoms_enp: null,
        time_tfoms_last_sync: null,
        medbookPrefix: '',
        medbookNumber: '',
        medbookNumberCustom: '',
        medbookNumberCustomOriginal: '',
        medbookType: MEDBOOK_TYPES[0].type,
        medbookTypePrev: MEDBOOK_TYPES[0].type,
        isArchive: false,
        contactTrustHealth: '',
      },
      disabled_forms: [],
      individuals: [],
      document_to_edit: -2,
      document: {
        number: '',
      },
      agent_to_edit: null,
      agent_card_selected: null,
      agent_doc: '',
      agent_clear: false,
      loading: false,
      loaded: false,
      new_card_num: '',
      companyDepartments: [],
      roomLocations: [],
    };
  },
  computed: {
    system() {
      return this.$systemTitle();
    },
    l2_tfoms() {
      return this.$store.getters.modules.l2_tfoms;
    },
    l2_profcenter() {
      return this.$store.getters.modules.l2_profcenter;
    },
    l2_send_patients_email_results() {
      return this.$store.getters.modules.l2_send_patients_email_results;
    },
    medbook_auto_start() {
      const value = Number(this.$store.getters.modules.medbook_auto_start);
      return Number.isSafeInteger(value) ? value : 100000;
    },
    doc_edit_type_title() {
      const t = this.document.document_type;
      if (!t) return '';
      return this.card.doc_types.find((x) => x.pk === t)?.title || '';
    },
    is_snils() {
      const tt = this.doc_edit_type_title;
      return tt === 'СНИЛС';
    },
    doc_edit_fields() {
      const tt = this.doc_edit_type_title;
      return {
        serial: tt !== 'СНИЛС',
        dates: tt !== 'СНИЛС',
        who_give: tt !== 'СНИЛС',
        masks: {
          number: tt === 'СНИЛС' ? '999-999-999 99' : undefined,
        },
      };
    },
    family() {
      return this.card.family;
    },
    name() {
      return this.card.name;
    },
    patronymic() {
      return this.card.patronymic;
    },
    sex() {
      return this.card.sex;
    },
    new_individual() {
      return this.card.new_individual;
    },
    time_tfoms_last_sync() {
      return this.card.time_tfoms_last_sync && moment(this.card.time_tfoms_last_sync).format('HH:mm DD.MM.YY');
    },
    valid() {
      if (!this.card.family || !this.card.name || !this.card.birthday) {
        return false;
      }
      return !!(this.card.family.length > 0 && this.card.name.length > 0 && this.card.birthday.match(/\d{4}-\d{2}-\d{2}/gm));
    },
    birthday() {
      return this.card.birthday;
    },
    valid_doc() {
      if (this.doc_edit_type_title === 'СНИЛС') {
        return /^\d\d\d-\d\d\d-\d\d\d \d\d$/gm.test(this.document.number) && validateSnils(this.document.number);
      }
      return this.document.number.length > 0;
    },
    valid_agent() {
      if (this.agent_clear) return true;
      return this.agent_card_selected && this.agent_card_selected !== this.card_pk;
    },
    forms() {
      return this.makeForms(forms);
    },
    can_change_owner_directions() {
      return (this.$store.getters.user_data.groups || []).includes('Управление иерархией истории');
    },
    agent_types_excluded() {
      return this.card.agent_types.filter((t) => !this.card.excluded_types.includes(t.key));
    },
  },
  watch: {
    sex() {
      let s = swapLayouts((this.card.sex || '').toLowerCase());
      if (s.length > 1) {
        // eslint-disable-next-line prefer-destructuring
        s = s[0];
      }
      if (s !== 'м' && s !== 'ж') {
        s = 'м';
      }
      this.card.sex = s;
      this.individuals_search();
    },
    family() {
      this.card.family = normalizeNamePart(this.card.family);
      this.individuals_search();
      this.individual_sex('family', this.card.family);
    },
    name() {
      this.card.name = normalizeNamePart(this.card.name);
      this.individuals_search();
      this.individual_sex('name', this.card.name);
    },
    patronymic() {
      this.card.patronymic = normalizeNamePart(this.card.patronymic);
      this.individuals_search();
      this.individual_sex('patronymic', this.card.patronymic);
    },
    birthday() {
      this.individuals_search();
    },
    new_individual() {
      this.individuals_search();
    },
    individuals: {
      deep: true,
      handler(nv) {
        if (nv.length === 0) {
          this.card.new_individual = true;
        }
      },
    },
  },
  created() {
    this.load_data();
    this.loadRoomLocations();
    this.get_disabled_forms();
    this.$root.$on('reload_editor', () => {
      this.load_data();
    });
  },
  updated() {
    // Костыль, что бы не вылезал автокомплит полей от браузера
    const {
      f, n, pn, ar, af,
    } = this.$refs;
    setTimeout(() => {
      for (const r of [f, n, pn, ar, af]) {
        if (r) {
          const inp = window.$('input', r.$el);
          inp.attr('autocomplete', 'new-password');
        }
      }
    }, 100);
  },
  methods: {
    async changeCompany(currentCompany) {
      const { data } = await this.$api('company-departments-find', {
        company_db: currentCompany,
      });
      this.companyDepartments = data;
    },

    async loadRoomLocations() {
      const { data } = await this.$api('load-room-locations');
      this.roomLocations = data;
    },

    async loadCompanies({ action, searchQuery, callback }) {
      if (action === ASYNC_SEARCH) {
        const { data } = await this.$api(`/companies-find?query=${searchQuery}`);
        callback(
          null,
          data.map(d => ({ id: `${d.id}`, label: `${d.title}` })),
        );
      }
    },
    async get_disabled_forms() {
      const resultData = await this.$api('disabled-forms');
      this.disabled_forms = resultData.rows;
    },
    makeForms(formsBase) {
      return formsBase
        .map((f) => {
          if (f.isGroup) {
            return {
              ...f,
              forms: this.makeForms(f.forms),
            };
          }
          return {
            ...f,
            url: valuesToString(f.url, {
              card: this.card_pk,
              individual: this.card.individual,
            }),
          };
        })
        .filter((f) => !f.not_internal && !this.disabled_forms.includes(f.type));
    },
    companiesTreeselect(companies) {
      return companies.map((c) => ({ id: c.id, label: c.short_title || c.title }));
    },
    agent_type_by_key(key) {
      for (const t of this.card.agent_types) {
        if (t.key === key) {
          return t.title;
        }
      }
      return 'НЕ ВЫБРАНО';
    },
    agent_need_doc(key) {
      return this.card.agent_need_doc.includes(key);
    },
    select_individual(invpk) {
      this.card.individual = invpk;
    },
    toggleNewIndividual() {
      this.card.new_individual = !this.card.new_individual;
    },
    hide_modal() {
      this.$root.$emit('hide_l2_card_create');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    save_hide_modal() {
      this.save(true);
    },
    async save(hideAfter = false) {
      if (this.card.send_to_email && this.card.email) {
        await this.$store.dispatch(actions.INC_LOADING);
        const r = await this.$api('patients/validate-email', { email: this.card.email });
        await this.$store.dispatch(actions.DEC_LOADING);

        if (!r.ok) {
          this.$root.$emit('msg', 'error', 'Введён некорректный email');
          return;
        }
      }
      if (!this.valid) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await patientsPoint.sendCard(
        this.card,
        [
          'family',
          'name',
          'patronymic',
          'birthday',
          'sex',
          'new_individual',
          'base_pk',
          'main_address_full',
          'fact_address_full',
          'work_place',
          'main_diagnosis',
          'work_position',
          'work_department',
          'work_place_db',
          'work_department_db',
          'room_location_db',
          'custom_workplace',
          'district',
          'phone',
          'email',
          'send_to_email',
          'number_poli',
          'harmful',
          'medbookPrefix',
          'medbookNumber',
          'medbookType',
          'medbookNumberCustom',
          'contactTrustHealth',
        ],
        {
          card_pk: this.card_pk,
          individual_pk: this.card.individual,
          gin_district: this.card.ginekolog_district,
          base_pk: this.base_pk,
        },
      );
      if (data.result !== 'ok') {
        let message = 'Сохранение прошло не удачно';
        if (Array.isArray(data.messages)) {
          for (const msg of data.messages) {
            message = `${message} ${msg}`;
          }
        }
        this.$root.$emit('msg', 'error', message);
        await this.$store.dispatch(actions.DEC_LOADING);
        return;
      }
      if (Array.isArray(data.messages)) {
        for (const msg of data.messages) {
          this.$root.$emit('msg', 'warning', msg);
        }
      }
      this.$root.$emit('msg', 'ok', 'Данные сохранены');
      this.$root.$emit('update_card_data');
      if (hideAfter) {
        this.hide_modal();
      }
      this.update_card(hideAfter, data);
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    update_card(hideAfter = false, data = null) {
      this.$root.$emit('select_card', {
        card_pk: data ? data.card_pk : this.card_pk,
        base_pk: this.base_pk,
        hide: hideAfter,
        inc_archive: true,
      });
    },
    async update_cdu(doc) {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.updateCdu({ card_pk: this.card_pk, doc });
      await this.load_data();
      this.$root.$emit('msg', 'ok', 'Изменения сохранены');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async update_wia(key) {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.updateWIA({ card_pk: this.card_pk, key });
      await this.load_data();
      this.$root.$emit('msg', 'ok', 'Изменения сохранены');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    edit_agent(key) {
      this.agent_card_selected = this.card[`${key}_pk`];
      this.agent_doc = this.card[`${key}_doc_auth`] || '';
      this.agent_clear = false;
      this.agent_to_edit = key;
    },
    async sync_rmis() {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.syncRmis(this, 'card_pk');
      await this.load_data();
      this.update_card();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async sync_tfoms() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { updated } = await patientsPoint.syncTfoms(this, 'card_pk');
      await this.load_data();
      this.update_card();
      this.$root.$emit('msg', 'ok', 'Сверка проведена');
      if (updated && updated.length > 0) {
        this.$root.$emit('msg', 'ok', `Обновлены данные: ${updated.join(', ')}`);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    getResponse(resp) {
      return [...resp.data.data];
    },
    onHitDocWhoGive(item) {
      if (!item) {
        return;
      }
      this.document.who_give = item;
    },
    onHit(name, noNext) {
      return (item, t) => {
        if (t.$el) {
          if (noNext) {
            window.$('input', t.$el).focus();
          } else {
            const index = window.$('input', this.$el).index(window.$('input', t.$el)) + 1;
            window.$('input', this.$el).eq(index).focus();
          }
        }
        if (!item) {
          return;
        }
        this.card[name] = item;
      };
    },
    highlighting: (item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`),
    load_data() {
      this.loaded = false;
      if (this.card_pk === -1) {
        return Promise.resolve({});
      }
      this.$store.dispatch(actions.INC_LOADING);
      return patientsPoint
        .getCard(this, 'card_pk')
        .then((data) => {
          this.card = data;
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.loaded = true;
        });
    },
    individuals_search: _.debounce(function () {
      this.individuals_search_main();
    }, 500),
    async individuals_search_main() {
      if (!this.valid || this.card_pk !== -1 || this.card.family === '' || this.card.name === '' || this.card.new_individual) {
        return;
      }

      this.loading = true;

      const { result, forced_gender: forcedGender } = await patientsPoint.individualsSearch(this.card, [
        'family',
        'name',
        'patronymic',
        'birthday',
      ]);

      this.individuals = result;
      this.card.individual = result.length === 0 ? -1 : result[0].pk;
      this.card.new_individual = result.length === 0;
      if (forcedGender) {
        this.card.sex = forcedGender;
      }

      this.loading = false;
    },
    individual_sex(t, v) {
      if (this.card_pk >= 0) {
        return;
      }
      patientsPoint.individualSex({ t, v }).then(({ sex }) => {
        this.card.sex = sex;
      });
    },
    edit_document(pk) {
      this.document = {
        document_type: this.card.doc_types[0].pk,
        is_active: true,
        number: '',
        serial: '',
        type_title: null,
        date_start: null,
        date_end: null,
        who_give: null,
        ...(this.card.docs.find((x) => x.id === pk) || {}),
      };
      this.document_to_edit = pk;
    },
    hide_modal_doc_edit() {
      if (this.$refs.modalDocEdit) {
        this.$refs.modalDocEdit.$el.style.display = 'none';
      }
      this.document_to_edit = -2;
    },
    hide_modal_agent_edit() {
      if (this.$refs.modalAgentEdit) {
        this.$refs.modalAgentEdit.$el.style.display = 'none';
      }
      this.agent_to_edit = null;
    },
    async save_doc() {
      if (!this.valid_doc) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.editDoc(this.document, ['serial', 'number', 'is_active', 'date_start', 'date_end', 'who_give'], {
        card_pk: this.card_pk,
        pk: this.document_to_edit,
        type: this.document.document_type,
        individual_pk: this.card.individual,
      });
      await this.load_data();
      this.document = {
        number: '',
      };
      this.hide_modal_doc_edit();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async save_agent() {
      if (!this.valid_agent) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.editAgent({
        key: this.agent_to_edit,
        parent_card_pk: this.card_pk,
        card_pk: this.agent_card_selected,
        doc: this.agent_doc,
        clear: this.agent_clear,
      });
      await this.load_data();
      this.hide_modal_agent_edit();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async change_directions_owner() {
      const { ok, individual_fio: individualFio } = await this.$api('patients/is-card', {
        number: this.new_card_num,
      });
      if (!ok) {
        this.$root.$emit('msg', 'error', 'Карта не найдена');
        return;
      }
      try {
        await this.$dialog.confirm(
          // eslint-disable-next-line max-len
          `Перенести все услуги из карты №${this.card.number} — ${this.card.family} ${this.card.name} ${this.card.patronymic} в карту №${this.new_card_num} — ${individualFio} ?`,
        );
      } catch (e) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await this.$api('directions/change-owner-direction', {
        old_card_number: this.card.number,
        new_card_number: this.new_card_num,
      });
      this.$root.$emit('msg', 'ok', 'Направления успешно перенесены');
      this.$root.$emit('msg', 'ok', `Номера: ${data.directions}`);
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('update_card_data');
    },
    async do_archive() {
      try {
        await this.$dialog.confirm(
          // eslint-disable-next-line max-len
          `Вы действительно хотите архивировать карту №${this.card.number} — ${this.card.family} ${this.card.name} ${this.card.patronymic}?`,
        );
      } catch (e) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      await this.$api('patients/card/archive', {
        pk: this.card.id,
      });
      await this.load_data();
      this.$root.$emit('msg', 'ok', 'Карта архивирована');
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('update_card_data');
      this.update_card();
    },
    async do_unarchive() {
      try {
        await this.$dialog.confirm(
          // eslint-disable-next-line max-len
          `Вы действительно хотите вернуть карту №${this.card.number} — ${this.card.family} ${this.card.name} ${this.card.patronymic}?`,
        );
      } catch (e) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('patients/card/unarchive', {
        pk: this.card.id,
      });
      await this.load_data();
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Карта возвращена');
        this.$root.$emit('update_card_data');
        this.update_card();
      } else {
        this.$root.$emit('msg', 'error', message);
      }
    },
  },
};
</script>

<style scoped lang="scss">
.nonPrior {
  opacity: 0.7;

  &:hover {
    opacity: 1;
  }
}

.prior {
  background-color: rgba(#000, 0.05);
}

.modal-mask {
  align-items: stretch !important;
  justify-content: stretch !important;
}

::v-deep .panel-flt {
  margin: 41px;
  align-self: stretch !important;
  width: 100%;
  display: flex;
  flex-direction: column;
}

::v-deep .panel-body {
  flex: 1;
  padding: 0;
  height: calc(100% - 91px);
  min-height: 200px;
}

.info-row {
  padding: 7px;
}

.individual {
  cursor: pointer;

  &:hover {
    background-color: rgba(0, 0, 0, 0.15);
  }
}

.str ::v-deep .input-group {
  width: 100%;
}

.lst {
  margin: 0;
  line-height: 1;
}

.c-pointer {
  &,
  & strong,
  &:hover {
    cursor: pointer !important;
  }
}

.loading-body {
  padding: 20px;
  text-align: center;
}

.row-t-btn {
  height: 26px;
  border-radius: 0;
  font-size: 10px;
}

.button-f {
  flex: 1;
}

.input-group-custom {
  flex: 1 100%;
  display: flex;
  flex-direction: row;

  .form-control:first-child {
    flex: 1 80px;
    padding: 6px 8px;
    border-right: 1px solid #434a54;
  }

  .form-control:last-child {
    flex: 1 calc(100% - 80px);
  }
}
</style>
