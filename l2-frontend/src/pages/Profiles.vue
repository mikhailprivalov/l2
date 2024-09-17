<template>
  <div class="root">
    <div class="left">
      <Treeselect
        v-model="selected_hospital"
        :multiple="false"
        :disable-branch-nodes="true"
        :options="can_edit_any_organization ? hospitals : own_hospital"
        placeholder="Больница не выбрана"
        :append-to-body="true"
        :disabled="open_pk !== -2"
        :clearable="false"
      />
      <input
        v-model="filter"
        class="form-control"
        placeholder="Фильтр"
        style="margin-top: 5px"
      >
      <div class="left-wrapper">
        <ul>
          <li
            v-for="d in departmentFiltered"
            :key="d.pk"
          >
            <strong>{{ d.title }}</strong>
            <ul>
              <li
                v-for="x in d.users"
                :key="x.pk"
                :class="{ selected: x.pk === open_pk }"
              >
                <a
                  class="user-link"
                  href="#"
                  @click.prevent="open(x.pk)"
                >{{ x.username }} – {{ x.fio }}</a>
              </li>
              <li :class="{ selected: open_pk === -1 && user.department === d.pk }">
                <a
                  href="#"
                  @click.prevent="open(-1, d.pk)"
                > <i class="fa fa-plus" /> добавить пользователя</a>
              </li>
            </ul>
          </li>
        </ul>
      </div>
    </div>
    <div
      v-if="open_pk > -2"
      class="right"
    >
      <div class="right-wrapper">
        <div class="main-data">
          <div class="row">
            <div
              class="col-xs-6"
              style="padding-right: 0"
            >
              <div class="input-group">
                <input
                  v-model="user.family"
                  class="form-control wbr"
                  type="text"
                  placeholder="Фамилия"
                >
                <span
                  class="input-group-btn"
                  style="width: 0"
                />
                <input
                  v-model="user.name"
                  class="form-control wbr"
                  type="text"
                  placeholder="Имя"
                >
                <span
                  class="input-group-btn"
                  style="width: 0"
                />
                <input
                  v-model="user.patronymic"
                  class="form-control"
                  style="margin-right: -1px"
                  type="text"
                  placeholder="Отчество"
                >
              </div>
            </div>
            <div
              class="col-xs-6 left-padding"
            >
              <div
                class="input-group"
                style="margin-right: -1px"
              >
                <span class="input-group-addon">Имя пользователя</span>
                <input
                  v-model="user.username"
                  class="form-control"
                  type="text"
                >
                <div class="input-group-btn">
                  <button
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    class="btn btn-blue-nb btn-ell dropdown-toggle nbr"
                    title="Генерация имени пользователя на основе ФИО"
                    type="button"
                    @click="gen_username"
                  >
                    <i class="fa fa-dot-circle-o" />
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="row">
            <div
              class="col-xs-6"
              style="padding-right: 0"
            >
              <div class="input-group">
                <span class="input-group-addon">Пароль</span>
                <input
                  v-if="user.sendPassword && validEmail"
                  key="no-passwd"
                  placeholder="пароль будет отправлен на email"
                  class="form-control"
                  type="text"
                  readonly
                >
                <input
                  v-else
                  key="passwd"
                  v-model="user.password"
                  :placeholder="
                    'Минимальная длина пароля – 6 символов. ' + (open_pk === -1 ? '' : 'Для смены пароля введите новый')
                  "
                  class="form-control"
                  type="text"
                >
                <div
                  v-if="!user.sendPassword || !validEmail"
                  class="input-group-btn"
                >
                  <button
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    class="btn btn-blue-nb btn-ell dropdown-toggle nbr"
                    title="Генерация пароля"
                    type="button"
                    @click="gen_passwd"
                  >
                    <i class="fa fa-dot-circle-o" />
                  </button>
                </div>
                <div
                  v-if="user.doc_pk > -1"
                  class="input-group-btn"
                >
                  <a
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    :href="`/barcodes/login?pk=${user.doc_pk}`"
                    target="_blank"
                    class="btn btn-blue-nb btn-ell dropdown-toggle nbr"
                    title="Штрих-код для входа"
                    type="button"
                    style="border-radius: 0"
                  >
                    <i class="fa fa-barcode" />
                  </a>
                </div>
              </div>
            </div>
            <div
              v-if="modules.change_password"
              class="col-xs-6 left-padding"
            >
              <div class="input-group">
                <span class="input-group-addon">Email</span>
                <input
                  v-model.trim="user.email"
                  placeholder="Email"
                  class="form-control"
                  type="email"
                  :class="!validEmail && 'has-error-field'"
                >
              </div>
            </div>
            <div
              class="col-xs-6"
              :style="modules.change_password ? 'padding-right: 0' : 'padding-left: 0'"
            >
              <div class="input-group">
                <span class="input-group-addon">Подразделение</span>
                <select
                  v-model="user.department"
                  class="form-control"
                >
                  <option
                    v-for="d in departments"
                    :key="d.pk"
                    :value="d.pk"
                  >
                    {{ d.title }}
                  </option>
                </select>
              </div>
            </div>
            <div
              v-if="modules.change_password"
              class="col-xs-6 left-padding"
            >
              <label class="group-input-label">
                <input
                  v-model="user.sendPassword"
                  type="checkbox"
                  :disabled="!validEmail"
                >
                Сгенерировать новый пароль и отправить на email
              </label>
            </div>
          </div>
        </div>
        <div class="more-data">
          <div
            v-if="l2_user_data.rmis_enabled"
            class="row"
          >
            <div
              class="col-xs-4"
              style="padding-right: 0"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">РМИС логин</span>
                <input
                  v-model="user.rmis_login"
                  class="form-control"
                >
              </div>
            </div>
            <div
              class="col-xs-4 left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">РМИС пароль</span>
                <input
                  v-model="user.rmis_password"
                  class="form-control"
                  placeholder="Для замены введите значение"
                >
              </div>
            </div>
            <div
              class="col-xs-4 left-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">ID ресурса РМИС</span>
                <input
                  v-model="user.rmis_resource_id"
                  class="form-control"
                >
              </div>
            </div>
          </div>
          <div
            v-if="modules.l2_rmis_queue || modules.l2_schedule"
            class="row"
          >
            <div
              class="col-xs-4 right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">РМИС location</span>
                <input
                  v-model="user.rmis_location"
                  class="form-control"
                >
              </div>
            </div>
            <div
              class="col-xs-4 left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">External_id</span>
                <input
                  v-model="user.rmis_employee_id"
                  class="form-control"
                >
              </div>
            </div>
            <div
              class="col-xs-4 left-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">РМИС service</span>
                <input
                  v-model="user.rmis_service_id_time_table"
                  class="form-control"
                >
              </div>
            </div>
          </div>
          <div class="row">
            <div
              class="col-xs-3"
              style="padding-right: 0"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Код врача</span>
                <input
                  v-model="user.personal_code"
                  class="form-control"
                >
              </div>
            </div>
            <div
              class="col-xs-3 left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Кабинет</span>
                <input
                  v-model="user.cabinet"
                  class="form-control"
                >
              </div>
            </div>
            <div
              class="col-xs-6 left-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Специальность</span>
                <Treeselect
                  v-model="user.speciality"
                  class="treeselect-nbr treeselect-wide treeselect-34px"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="specialities"
                  placeholder="Специальность не выбрана"
                  :append-to-body="true"
                  :clearable="false"
                />
              </div>
            </div>
          </div>
          <div class="row">
            <div
              class="col-xs-6"
              style="padding-right: 0"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">СНИЛС</span>
                <input
                  v-model.trim="user.snils"
                  class="form-control"
                  :class="!snilsValid && 'has-error-field'"
                  placeholder="СНИЛС в формате 12345678912"
                >
              </div>
            </div>
            <div
              class="col-xs-6 left-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Должность</span>
                <Treeselect
                  v-model="user.position"
                  class="treeselect-nbr treeselect-wide treeselect-34px"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="positions"
                  placeholder="Должность не выбрана"
                  :append-to-body="true"
                  :clearable="false"
                />
              </div>
            </div>
          </div>
          <div
            class="input-group"
            style="width: 100%"
          >
            <span class="input-group-addon">Группы</span>
            <select
              v-model="user.groups"
              class="form-control"
              multiple
              style="height: 136px"
            >
              <option
                v-for="g in user.groups_list"
                :key="g.pk"
                :value="g.pk"
              >
                {{ g.title }}
              </option>
            </select>
          </div>
          <div class="row">
            <div
              class="col-xs-2"
              style="padding-right: 0"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <label
                  class="input-group-addon"
                  style="height: 34px; text-align: left"
                >
                  <input
                    v-model="user.external_access"
                    type="checkbox"
                  > Внешний доступ до
                </label>
              </div>
            </div>
            <div
              class="col-xs-2 left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <input
                  v-if="user.external_access"
                  v-model="user.date_stop_external_access"
                  class="form-control"
                  type="date"
                >
              </div>
            </div>
            <div
              class="col-xs-4 left-padding right-padding"
            >
              <div
                class=" input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Участок</span>
                <select
                  v-model="user.district"
                  class="form-control"
                >
                  <option
                    v-for="d in districts"
                    :key="d.pk"
                    :value="d.pk"
                  >
                    {{ d.title }}
                  </option>
                </select>
              </div>
            </div>
            <div
              class="col-xs-3 left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <label
                  class="input-group-addon"
                  style="height: 34px; text-align: left"
                >
                  <input
                    v-model="user.notControlAnketa"
                    type="checkbox"
                  > Не контролировать АНКЕТУ
                </label>
              </div>
            </div>
            <div
              class="col-xs-1 left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <label
                  class="input-group-addon"
                  style="height: 34px; text-align: left"
                >
                  <input
                    v-model="user.dismissed"
                    type="checkbox"
                  > Уволен
                </label>
              </div>
            </div>
          </div>
          <div class="more-title">
            Запрет на создание направлений с назначениями:
            <button
              class="btn btn-blue-nb sidebar-btn"
              style="font-size: 13px"
            >
              <i
                v-if="setup_forbidden"
                v-tippy="{ placement: 'bottom' }"
                class="glyphicon glyphicon-circle-arrow-up"
                title="Скрыть"
                @click="change_setup_forbidden"
              />
              <i
                v-else
                v-tippy="{ placement: 'bottom' }"
                class="glyphicon glyphicon-circle-arrow-down"
                title="Редактировать"
                @click="change_setup_forbidden"
              />
            </button>
            <button
              class="btn btn-blue-nb sidebar-btn"
              style="font-size: 13px"
              @click="restrictedOfPrice"
            >
              Ограничить услуги по прайсу
            </button>
            <button
              class="btn btn-blue-nb sidebar-btn"
              style="font-size: 13px"
              @click="cancelRestricted"
            >
              Убрать ограничение
            </button>
          </div>
          <div
            v-if="setup_forbidden"
            class="row"
            style="margin-right: 0"
          >
            <div
              class="col-xs-6"
              style="height: 300px; border-right: 1px solid #eaeaea; padding-right: 0"
            >
              <ResearchesPicker
                v-model="user.restricted_to_direct"
                :hidetemplates="true"
                :just_search="true"
              />
            </div>
            <div
              class="col-xs-6 left-padding right-padding"
              style="height: 300px"
            >
              <SelectedResearches
                :researches="user.restricted_to_direct"
                :simple="true"
              />
            </div>
          </div>
          <div
            v-if="(modules.l2_rmis_queue || modules.l2_schedule) && (user.rmis_location !== '')"
            class="more-title"
          >
            Услуги, оказываемые пользователем:
          </div>
          <div
            v-if="(modules.l2_rmis_queue || modules.l2_schedule) && user.rmis_location !== ''"
            class="row"
            style="margin-right: 0"
          >
            <div
              class="col-xs-6"
              style="height: 300px; border-right: 1px solid #eaeaea; padding-right: 0"
            >
              <ResearchesPicker
                v-model="user.users_services"
                :hidetemplates="true"
                :filter_types="[2]"
                :just_search="true"
              />
            </div>
            <div
              class="col-xs-6 left-padding right-padding"
              style="height: 300px"
            >
              <SelectedResearches
                :researches="user.users_services"
                :simple="true"
              />
            </div>
          </div>
          <div class="more-title">
            Расписание-ресурсы:
            <button
              class="btn btn-blue-nb sidebar-btn"
              style="font-size: 13px"
            >
              <i
                v-if="setup_resource"
                v-tippy="{ placement: 'bottom' }"
                class="glyphicon glyphicon-circle-arrow-up"
                title="Скрыть"
                @click="change_setup_resource"
              />
              <i
                v-else
                v-tippy="{ placement: 'bottom' }"
                class="glyphicon glyphicon-circle-arrow-down"
                title="Редактировать"
                @click="change_setup_resource"
              />
            </button>
          </div>
          <div
            v-if="setup_resource"
            class="row"
            style="height: 200px; border-right: 1px solid #eaeaea; padding-right: 0"
          >
            <div
              class="col-xs-6"
              style="height: 100%"
            >
              <ResearchesPicker
                v-model="resource_researches"
                autoselect="none"
                :hidetemplates="true"
              />
            </div>
            <div
              class="col-xs-6"
              style="height: 100%"
            >
              <SelectedResearches
                :researches="resource_researches || []"
                :simple="true"
              />
            </div>
            <div
              :class="current_resource_pk !== -1 ? 'col-xs-9' : 'col-xs-10'"
              style="padding-right: 0"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Наименование ресурса</span>
                <input
                  v-model="current_resource_title"
                  class="form-control"
                >
              </div>
            </div>
            <div
              v-if="current_resource_pk !== -1"
              style="padding-right: 0;text-align: right"
              class="col-xs-1"
            >
              <button
                v-tippy
                class="btn btn-blue-nb"
                title="Отмена"
                @click="current_resource_title = ''; resource_researches = []; current_resource_pk = -1;"
              >
                <i class="fa fa-times" />
              </button>
            </div>
            <div
              style="padding-right: 20px;text-align: right"
              class="col-xs-2"
            >
              <button
                :disabled="!valid || resource_researches.length === 0 || current_resource_title.length === 0"
                class="btn btn-blue-nb"
                @click="save_resource"
              >
                {{ current_resource_pk !== -1 ? 'Обновить ресурс' : 'Сохранить ресурс' }}
              </button>
            </div>
          </div>
          <div
            v-if="setup_resource"
            style="padding-top: 30px"
          >
            <div
              v-for="row in rows"
              :key="row.pk"
              class="research"
              :class="current_resource_pk === row.pk && 'research-active'"
            >
              <strong
                v-if="row.title"
                class="t-r"
              >
                {{ row.title }}
              </strong>
              <span
                v-for="res in row.researches"
                :key="res.pk"
                class="t-r"
              >
                {{ res.title }}
              </span>
              <button
                class="btn btn-blue-nb sidebar-btn"
                style="font-size: 12px"
                @click="current_resource_researches(row)"
              >
                Редактировать
              </button>
              <button
                class="btn btn-blue-nb sidebar-btn"
                style="font-size: 12px"
                @click="open_schedule(row.pk)"
              >
                Расписание
              </button>
            </div>
          </div>
          <div
            v-if="modules.limit_age_patient_registration"
            class="row"
          >
            <div
              class="col-xs-4 right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Возраст на запись (не старше мес.)</span>
                <input
                  v-model="user.max_age_patient_registration"
                  type="number"
                  class="form-control"
                >
              </div>
            </div>
          </div>
          <div
            v-if="modules.limit_age_patient_registration"
            class="row"
          >
            <div
              class="col-xs-12"
              style="padding-right: 0"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Квоты на запись по времени для подразделений</span>
                <textarea
                  v-model="user.available_quotas_time"
                  v-autosize="user.available_quotas_time"
                  :placeholder='`{"id-подразделения1": "10:00-15:00", "id-подразделения2": "15:00-16:00"}` /* eslint-disable-line vue/html-quotes,max-len */'
                  class="form-control noresize"
                />
              </div>
            </div>
          </div>
          <div
            class="row left-padding-10"
          >
            <div class="more-title">
              Анализаторы:
              <button
                class="btn btn-blue-nb sidebar-btn"
                style="font-size: 13px"
              >
                <i
                  v-if="setup_analyzer"
                  v-tippy="{ placement: 'bottom'}"
                  class="glyphicon glyphicon-circle-arrow-up"
                  title="Скрыть"
                  @click="change_setup_analyzer"
                />
                <i
                  v-else
                  v-tippy="{ placement: 'bottom' }"
                  class="glyphicon glyphicon-circle-arrow-down"
                  title="Выбрать"
                  @click="change_setup_analyzer"
                />
              </button>
            </div>
          </div>
          <div
            class="row left-padding-10"
          >
            <div
              v-if="setup_analyzer"
              class="input-group"
              style="width: 100%"
            >
              <span class="input-group-addon">Анализаторы</span>
              <select
                v-model="analyzers"
                class="form-control"
                multiple
                style="height: 136px"
              >
                <option
                  v-for="l in analyzers_list"
                  :key="l.pk"
                  :value="l.pk"
                >
                  {{ l.label }}
                </option>
              </select>
            </div>
          </div>
          <div
            class="row left-padding-10"
          >
            <div
              class="col-xs-6 left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Кабинеты</span>
                <Treeselect
                  v-model="user.rooms"
                  class="treeselect-nbr treeselect-wide treeselect-34px"
                  :multiple="true"
                  :options="user.rooms_list"
                  :flatten-search-results="true"
                  placeholder="Кабинеты не указаны"
                />
              </div>
            </div>
          </div>
          <div class="row left-padding-10">
            <div
              class="col-xs-4 left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Дата выписки из кадров</span>
                <input
                  v-model="user.date_extract_employee"
                  class="form-control"
                  type="date"
                >
              </div>
            </div>
            <div
              class="col-xs-4 left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Срок сертификата</span>
                <input
                  v-model="user.date_stop_certificate"
                  class="form-control"
                  type="date"
                >
              </div>
            </div>
            <div
              class="col-xs-4 left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Исполнитель в протколе</span>
                <Treeselect
                  v-model="user.replace_doctor_cda"
                  class="treeselect-nbr treeselect-wide treeselect-34px"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="user.department_doctors"
                  placeholder="Врач для CDA"
                  :append-to-body="true"
                  :clearable="false"
                />
              </div>
            </div>
          </div>
          <div
            class="row left-padding-10"
          >
            <div
              class="left-padding right-padding"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Доп. инфо</span>
                <textarea
                  v-model="user.additionalInfo"
                  v-tippy
                  title="Дополнительная информация описывать словарем { key: value }"
                  class="form-control border-top-none"
                  rows="3"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="right-bottom">
        <button
          class="btn btn-blue-nb"
          @click="close"
        >
          Закрыть
        </button>
        <button
          :disabled="!valid"
          class="btn btn-blue-nb"
          @click="save"
        >
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { debounce } from 'lodash';
import { mapGetters } from 'vuex';

import { validateEmail, validateSnils } from '@/utils';
import usersPoint from '@/api/user-point';
import * as actions from '@/store/action-types';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import SelectedResearches from '@/ui-cards/SelectedResearches.vue';
import UrlData from '@/UrlData';

const toTranslit = function (text) {
  return text.replace(/([а-яё])|([\s_-])|([^a-z\d])/gi, (all, ch, space, words) => {
    if (space || words) {
      return space ? '-' : '';
    }
    const code = ch.charCodeAt(0);
    let index;
    if (code === 1025 || code === 1105) {
      index = 0;
    } else {
      index = code > 1071 ? code - 1071 : code - 1039;
    }
    const t = [
      'yo',
      'a',
      'b',
      'v',
      'g',
      'd',
      'e',
      'zh',
      'z',
      'i',
      'y',
      'k',
      'l',
      'm',
      'n',
      'o',
      'p',
      'r',
      's',
      't',
      'u',
      'f',
      'h',
      'c',
      'ch',
      'sh',
      'shch',
      '',
      'y',
      '',
      'e',
      'yu',
      'ya',
    ];
    return t[index];
  });
};

function strRand(l = 8, v = 1) {
  let result = '';
  const words = v === 1 ? '0123456789-qwertyuiopasdfghjklzxcvbnm01234567890123456789' : '000000000000123456789';
  const maxPosition = words.length - 1;
  for (let i = 0; i < l; ++i) {
    const position = Math.floor(Math.random() * maxPosition);
    result += words.substring(position, position + 1);
  }
  return result;
}

export default {
  name: 'Profiles',
  components: { ResearchesPicker, SelectedResearches, Treeselect },
  data() {
    return {
      filter: '',
      departments: [],
      analyzers: [],
      analyzers_list: [],
      specialities: [],
      positions: [],
      districts: [],
      doctor_profiles: [],
      resource_researches: [],
      setup_analyzer: false,
      setup_forbidden: false,
      setup_resource: false,
      resource_templates_list: [],
      current_resource_pk: -1,
      current_resource_title: '',
      user: {
        username: '',
        password: '',
        email: '',
        rmis_location: '',
        rmis_login: '',
        rmis_password: '',
        doc_pk: -1,
        personal_code: -1,
        cabinet: '',
        rmis_resource_id: '',
        rmis_employee_id: '',
        rmis_service_id_time_table: '',
        sendPassword: false,
        external_access: false,
        date_stop_external_access: '',
        resource_schedule: [],
        notControlAnketa: false,
        date_extract_employee: '',
        date_stop_certificate: '',
        replace_doctor_cda: -1,
        department_doctors: [],
        additionalInfo: '{}',
        dismissed: false,
      },
      selected_hospital: -1,
      open_pk: -2,
    };
  },
  computed: {
    rows() {
      return this.resource_templates_list.map((r) => ({
        ...r,
        researches: r.researches.map((rpk) => this.$store.getters.researches_obj[rpk]).filter(Boolean),
      }));
    },
    snilsValid() {
      return (
        !this.user.snils || (!this.user.snils.includes('-') && !this.user.snils.includes(' ') && validateSnils(this.user.snils))
      );
    },
    validEmail() {
      return validateEmail(this.user?.email);
    },
    departmentFiltered() {
      const r = [];
      for (const x of this.departments) {
        r.push({
          ...x,
          users: x.users.filter(
            (y) => y.fio.toLowerCase().startsWith(this.filter.toLowerCase())
              || y.username.toLowerCase().startsWith(this.filter.toLowerCase()),
          ),
        });
      }
      return r.filter((d) => this.filter === '' || d.users.length || d.title.toLowerCase().startsWith(this.filter.toLowerCase()));
    },
    valid() {
      const p = (this.open_pk > -1
          && (this.user.password.length === 0 || this.user.password.length >= 3 || (this.user.sendPassword && this.validEmail)))
        || (this.open_pk === -1 && (this.user.password.length >= 3 || (this.user.sendPassword && this.validEmail)));
      return p && this.user.username !== '' && this.user.family !== '' && this.user.name !== '' && this.snilsValid;
    },
    ...mapGetters({
      modules: 'modules',
      l2_user_data: 'user_data',
      hospitals: 'hospitals',
    }),
    can_edit_any_organization() {
      return this.l2_user_data.su || this.l2_user_data.all_hospitals_users_control;
    },
    user_hospital() {
      return this.l2_user_data.hospital || -1;
    },
    own_hospital() {
      return [this.hospitals.find(({ id }) => id === this.l2_user_data.hospital) || {}];
    },
  },
  watch: {
    'user.family': function () {
      this.user.family = this.user.family
        .replace(/\s\s+/g, ' ')
        .split(' ')
        .map((s) => s
          .split('-')
          .map((x) => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase())
          .join('-'))
        .join(' ');
      if (this.open_pk === -1) {
        this.deb_gu();
      }
    },
    'user.name': function () {
      this.user.name = this.user.name
        .replace(/\s\s+/g, ' ')
        .split(' ')
        .map((s) => s
          .split('-')
          .map((x) => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase())
          .join('-'))
        .join(' ');
      if (this.open_pk === -1) {
        this.deb_gu();
      }
    },
    'user.patronymic': function () {
      this.user.patronymic = this.user.patronymic
        .replace(/\s\s+/g, ' ')
        .split(' ')
        .map((s) => s
          .split('-')
          .map((x) => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase())
          .join('-'))
        .join(' ');
      if (this.open_pk === -1) {
        this.deb_gu();
      }
    },
    'user.external_access': function () {
      if (!this.user.external_access) {
        this.user.date_stop_external_access = '';
      }
    },
    user_hospital: {
      handler() {
        if (this.selected_hospital !== -1 || this.user_hospital === -1) {
          return;
        }
        this.selected_hospital = this.user_hospital;
      },
      immediate: true,
    },
    selected_hospital() {
      if (this.selected_hospital === -1) {
        return;
      }

      this.load_users();
    },
    resource_researches() {
      if (this.resource_researches.length === 0) {
        this.current_resource_pk = -1;
      }
    },
  },
  created() {
    this.load_users();
    this.current_resource_pk = -1;
    this.resource_researches = [];
    this.current_resource_title = '';
  },
  mounted() {
    this.getAllAnalyzers();
  },
  methods: {
    open_schedule(pk) {
      window.open(`/ui/schedule#${UrlData.objectToData({ resourceSelected: pk })}`, '_blank');
    },
    current_resource_researches(row) {
      for (const res of this.resource_templates_list) {
        if (row.pk === res.pk) {
          this.resource_researches = res.researches;
          this.current_resource_pk = row.pk;
          this.current_resource_title = res.title;
          break;
        }
      }
    },
    async getAllAnalyzers() {
      const list = await this.$api('analyzers/all-analyzers');
      this.analyzers_list = list.data;
    },
    async save_resource() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('schedule/save-resource', {
        pk: this.user.doc_pk,
        resource_researches: this.resource_researches,
        res_pk: this.current_resource_pk,
        res_title: this.current_resource_title,
      });
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', message);
        if (this.current_resource_pk === -1) {
          this.current_resource_title = '';
          this.resource_researches = [];
        }
        await this.reloadResources();
      }
    },
    change_setup_forbidden() {
      this.setup_forbidden = !this.setup_forbidden;
    },
    async restrictedOfPrice() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok } = await this.$api('users/update-restricted-directions', {
        userPk: this.user.doc_pk,
        hospitalPk: this.selected_hospital,
      });
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', 'успешно');
      } else {
        this.$root.$emit('msg', 'error', 'ошибка');
      }
    },
    async cancelRestricted() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok } = await this.$api('users/cancel-restricted-directions', {
        userPk: this.user.doc_pk,
      });
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', 'успешно');
      } else {
        this.$root.$emit('msg', 'error', 'ошибка');
      }
    },
    change_setup_analyzer() {
      this.setup_analyzer = !this.setup_analyzer;
    },
    change_setup_resource() {
      this.setup_resource = !this.setup_resource;
    },
    deb_gu: debounce(function () {
      this.gen_username();
    }, 500),
    gen_username() {
      let v = `${this.user.family} ${this.user.name} ${this.user.patronymic}`;
      let ls = v.split(' ');
      if (ls.length > 3) {
        ls = [ls[0], ls.slice(1, ls.length - 2).join(' '), ls[ls.length - 1] || ''];
      }
      while (ls.length <= 2) {
        ls.push(' ');
      }
      v = ls[0] + (ls[1][0] || '') + (ls[2][0] || '');
      v = toTranslit(v.replace(/\s/g, '')) + strRand(3, 2);
      this.user.username = v;
      this.$root.$emit('msg', 'ok', 'Имя пользователя сгенерировано');
    },
    gen_passwd() {
      this.user.password = strRand();
    },
    async load_users(prevClr = false) {
      await this.$store.dispatch(actions.INC_LOADING);
      if (!prevClr) {
        this.departments = [];
      }
      const {
        departments, specialities, positions, districts, doctorProfiles,
      } = await usersPoint.loadUsers(this, 'selected_hospital');
      this.departments = departments;
      this.specialities = specialities;
      this.positions = positions;
      this.districts = districts;
      this.doctor_profiles = doctorProfiles;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async open(pk, dep = null) {
      if ((pk === this.open_pk && pk !== -1) || (this.open_pk === -1 && pk === -1 && dep === this.user.department)) {
        return;
      }
      this.close();
      await this.$store.dispatch(actions.INC_LOADING);
      const { user } = await usersPoint.loadUser({ pk });
      this.user = user;
      if (pk === -1) {
        this.user.department = dep;
        this.gen_passwd();
      }
      this.current_resource_pk = -1;
      this.current_resource_title = '';
      this.resource_researches = [];
      this.resource_templates_list = this.user.resource_schedule;
      await this.$store.dispatch(actions.DEC_LOADING);
      this.open_pk = pk;
    },
    async reloadResources() {
      if (!this.open_pk) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { user } = await usersPoint.loadUser({ pk: this.open_pk });
      this.user.resource_schedule = user.resource_schedule;
      this.resource_templates_list = this.user.resource_schedule;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, npk, message } = await usersPoint.saveUser({
        pk: this.open_pk,
        user_data: this.user,
        groupsAnalyzer: this.analyzers,
        hospital_pk: this.selected_hospital,
      });
      if (ok) {
        this.$root.$emit(
          'msg',
          'ok',
          `Пользователь сохранён\n${this.user.family} ${this.user.name} ${this.user.patronymic} – ${this.user.username}`,
        );
        this.open_pk = npk;
        this.load_users(true);
        if (this.user.sendPassword && this.validEmail) {
          this.user.password = '';
        }
        this.user.sendPassword = false;
      } else {
        this.$root.$emit('msg', 'error', `Ошибка\n${message}`);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async close() {
      this.open_pk = -2;
      this.analyzers = [];
      this.user = {
        family: '',
        name: '',
        patronymic: '',
        groups: [],
        groups_list: [],
        restricted_to_direct: [],
        resource_schedule: [],
        users_services: [],
        username: '',
        password: '',
        department: null,
        rmis_resource_id: '',
      };
      this.current_resource_pk = -1;
      this.current_resource_title = '';
      this.resource_researches = [];
    },
  },
};
</script>

<style lang="scss" scoped>
.root {
  position: absolute;
  top: 36px;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
}

.left,
.right {
  height: 100%;
}

.left {
  background: #fff;
  border-right: 1px solid #646d78;
  padding-top: 5px;
  padding-left: 2px;
  padding-right: 5px;
  width: 320px;

  input {
    border-radius: 0;
    width: 100%;
  }
}

.left-wrapper {
  height: calc(100% - 75px);
  padding-top: 5px;
  overflow-y: auto;
}

.right {
  width: calc(100% - 321px);
  overflow: hidden;
  position: relative;

  .input-group-addon,
  input,
  select {
    border-radius: 0;
    border-top: none;
    border-right: none;
    border-left: none;
  }

  .input-group-addon {
    width: 155px;
    text-align: left;
  }
}

.right-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 34px;
}

.right-bottom {
  position: absolute;
  background-color: #eaeaea;
  left: 0;
  right: 0;
  bottom: 0;
  height: 34px;
  display: flex;

  button {
    border-radius: 0;
  }
}

.user-link {
  color: #000;
  text-decoration: none;

  &:hover {
    text-decoration: underline;
  }
}

.main-data {
  .input-group {
    width: 100%;
  }

  button {
    border-radius: 0;
    width: 50px;
    margin-right: -1px;
  }
}

ul {
  padding-left: 20px;
}

li > ul > li {
  list-style: none;

  &::before {
    color: #000;
    content: '\2022';
    font-size: 18px;
    line-height: 12px;
    padding-right: 8px;
    position: relative;
    top: 0;
  }

  &.selected::before {
    color: #26816a;
    text-shadow: 0 0 4px rgba(#26816a, 0.9);
  }
}

li.selected {
  a {
    font-weight: bold;

    &.user-link {
      text-shadow: 0 0 4px rgba(#26816a, 0.5);
    }

    &::before {
      content: '[';
      color: #26816a;
    }

    &::after {
      content: ']';
      color: #26816a;
    }
  }
}

.more {
  &-data {
    height: calc(100% - 68px);
    overflow-y: auto;
    overflow-x: hidden;
    padding-bottom: 68px;
  }

  &-title {
    background: #eaeaea;
    padding: 5px;
    width: 100%;
  }
}

.rinp {
  width: 30%;
}

.form-control.wbr {
  border-right: 1px solid #646d78;
}

.group-input-label {
  font-weight: 500;
  height: 34px;
  line-height: 34px;
  padding-left: 10px;
  width: 100%;
  background: #fff;
  border-left: 1px solid #a9b2bd;
  border-bottom: 1px solid #a9b2bd;
  margin-bottom: 0;
}

.sidebar-btn {
  border-radius: 5px;

  &:not(.text-center) {
    text-align: left;
  }

  border-top: none !important;
  border-right: none !important;
  border-left: none !important;
  border-bottom: none !important;
  padding: 4px;
  height: 23px;

  &:not(:hover),
  &.active-btn:hover {
    cursor: default;
    background-color: rgba(#737373, 0.01) !important;
    color: #37bc9b;
  }
}
.sidebar-content {
  height: 100%;
  overflow-y: auto;
  background-color: hsla(30, 3%, 97%, 1);
}

.sidebar-content:not(.fcenter) {
  padding-bottom: 10px;
}

.t-r {
  font-size: 80%;
  padding-left: 5px;
}

.research {
  background-color: #fff;
  padding: 5px 5px 5px 0;
  margin: 10px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
  border-left: 5px solid #fff;

  &.rhide {
    background-image: linear-gradient(#6c7a89, #56616c);
    color: #fff;
  }

  &-active {
    border-left: 5px solid #37bc9b;
  }
}

.research:not(:first-child) {
  margin-top: 0;
}

.research:last-child {
  margin-bottom: 0;
}

.left-padding {
  padding-left: 0
}
.right-padding {
  padding-right: 0
}
.left-padding-10 {
  padding-left: 10px
}
.border-top-none {
  border-top: 0;
}
</style>
