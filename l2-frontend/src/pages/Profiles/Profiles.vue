<template>
  <div class="root">
    <div class="left">
      <Treeselect
        v-model="selectedHospital"
        :multiple="false"
        :disable-branch-nodes="true"
        :options="canEditAnyOrganization ? hospitals : ownHospital"
        placeholder="Больница не выбрана"
        :append-to-body="true"
        :disabled="openPk !== -2"
        :clearable="false"
      />
      <input
        v-model="filter"
        class="form-control"
        placeholder="Фильтр"
        style="margin-top: 5px"
      >
      <div class="left-wrapper">
        <department
          v-for="department in departments"
          :key="department.pk"
        />
      </div>
    </div>
    <div
      v-if="openPk > -2"
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
                    @click="genUsername"
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
                    'Минимальная длина пароля – 6 символов. ' + (openPk === -1 ? '' : 'Для смены пароля введите новый')
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
                    @click="genPasswd"
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
            v-if="l2UserData.rmis_enabled"
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
                v-if="setupForbidden"
                v-tippy="{ placement: 'bottom' }"
                class="glyphicon glyphicon-circle-arrow-up"
                title="Скрыть"
                @click="changeSetupForbidden"
              />
              <i
                v-else
                v-tippy="{ placement: 'bottom' }"
                class="glyphicon glyphicon-circle-arrow-down"
                title="Редактировать"
                @click="changeSetupForbidden"
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
            v-if="setupForbidden"
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
                v-if="setupResource"
                v-tippy="{ placement: 'bottom' }"
                class="glyphicon glyphicon-circle-arrow-up"
                title="Скрыть"
                @click="changeSetupResource"
              />
              <i
                v-else
                v-tippy="{ placement: 'bottom' }"
                class="glyphicon glyphicon-circle-arrow-down"
                title="Редактировать"
                @click="changeSetupResource"
              />
            </button>
          </div>
          <div
            v-if="setupResource"
            class="row"
            style="height: 200px; border-right: 1px solid #eaeaea; padding-right: 0"
          >
            <div
              class="col-xs-6"
              style="height: 100%"
            >
              <ResearchesPicker
                v-model="resourceResearches"
                autoselect="none"
                :hidetemplates="true"
              />
            </div>
            <div
              class="col-xs-6"
              style="height: 100%"
            >
              <SelectedResearches
                :researches="resourceResearches || []"
                :simple="true"
              />
            </div>
            <div
              :class="currentResourcePk !== -1 ? 'col-xs-9' : 'col-xs-10'"
              style="padding-right: 0"
            >
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Наименование ресурса</span>
                <input
                  v-model="currentResourceTitle"
                  class="form-control"
                >
              </div>
            </div>
            <div
              v-if="currentResourcePk !== -1"
              style="padding-right: 0;text-align: right"
              class="col-xs-1"
            >
              <button
                v-tippy
                class="btn btn-blue-nb"
                title="Отмена"
                @click="currentResourceTitle = ''; resourceResearches = []; currentResourcePk = -1;"
              >
                <i class="fa fa-times" />
              </button>
            </div>
            <div
              style="padding-right: 20px;text-align: right"
              class="col-xs-2"
            >
              <button
                :disabled="!valid || resourceResearches.length === 0 || currentResourceTitle.length === 0"
                class="btn btn-blue-nb"
                @click="saveResource"
              >
                {{ currentResourcePk !== -1 ? 'Обновить ресурс' : 'Сохранить ресурс' }}
              </button>
            </div>
          </div>
          <div
            v-if="setupResource"
            style="padding-top: 30px"
          >
            <div
              v-for="row in rows"
              :key="row.pk"
              class="research"
              :class="currentResourcePk === row.pk && 'research-active'"
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
                @click="currentResourceResearches(row)"
              >
                Редактировать
              </button>
              <button
                class="btn btn-blue-nb sidebar-btn"
                style="font-size: 12px"
                @click="openSchedule(row.pk)"
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
                  v-if="setupAnalyzer"
                  v-tippy="{ placement: 'bottom'}"
                  class="glyphicon glyphicon-circle-arrow-up"
                  title="Скрыть"
                  @click="changeSetupAnalyzer"
                />
                <i
                  v-else
                  v-tippy="{ placement: 'bottom' }"
                  class="glyphicon glyphicon-circle-arrow-down"
                  title="Выбрать"
                  @click="changeSetupAnalyzer"
                />
              </button>
            </div>
          </div>
          <div
            class="row left-padding-10"
          >
            <div
              v-if="setupAnalyzer"
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
                  v-for="l in analyzersList"
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

<script setup lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { debounce } from 'lodash';
import {
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';

import { validateEmail, validateSnils } from '@/utils';
import usersPoint from '@/api/user-point';
import * as actions from '@/store/action-types';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import SelectedResearches from '@/ui-cards/SelectedResearches.vue';
import UrlData from '@/UrlData';
import { useStore } from '@/store';
import api from '@/api';
import Department from "@/pages/Profiles/Department.vue";

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const toTranslit = (text) => text.replace(/([а-яё])|([\s_-])|([^a-z\d])/gi, (all, ch, space, words) => {
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

const strRand = (l = 8, v = 1) => {
  let result = '';
  const words = v === 1 ? '0123456789-qwertyuiopasdfghjklzxcvbnm01234567890123456789' : '000000000000123456789';
  const maxPosition = words.length - 1;
  for (let i = 0; i < l; ++i) {
    const position = Math.floor(Math.random() * maxPosition);
    result += words.substring(position, position + 1);
  }
  return result;
};

const filter = ref('');
const departments = ref([]);
const analyzers = ref([]);
const analyzersList = ref([]);
const specialities = ref([]);
const positions = ref([]);
const districts = ref([]);
const doctorProfiles = ref([]);
const resourceResearches = ref([]);
const setupAnalyzer = ref(false);
const setupForbidden = ref(false);
const setupResource = ref(false);
const resourceTemplatesList = ref([]);
const currentResourcePk = ref(-1);
const currentResourceTitle = ref('');
const user = ref({
  username: '',
  password: '',
  family: '',
  name: '',
  patronymic: '',
  department: '',
  email: '',
  snils: '',
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
  rooms: '',
  rooms_list: [],
  available_quotas_time: '',
  max_age_patient_registration: null,
  users_services: [],
  restricted_to_direct: [],
  district: null,
  groups: [],
  groups_list: [],
  position: null,
  speciality: null,
});
const selectedHospital = ref(-1);
const openPk = ref(-2);

const rows = computed(() => resourceTemplatesList.value.map((r) => ({
  ...r, researches: r.researches.map((rpk) => store.getters.researches_obj[rpk]).filter(Boolean),
})));

const snilsValid = computed(() => (
  !user.value.snils || (!user.value.snils.includes('-') && !user.value.snils.includes(' ') && validateSnils(user.value.snils))
));

const validEmail = computed(() => validateEmail(user.value?.email));

const departmentFiltered = computed(() => {
  const r = [];
  for (const x of departments.value) {
    r.push({
      ...x,
      users: x.users.filter(
        (y) => y.fio.toLowerCase().startsWith(filter.value.toLowerCase())
              || y.username.toLowerCase().startsWith(filter.value.toLowerCase()),
      ),
    });
  }
  return r.filter((d) => filter.value === '' || d.users.length || d.title.toLowerCase().startsWith(filter.value.toLowerCase()));
});

const valid = computed(() => {
  const p = (openPk.value > -1
      && (user.value.password.length === 0 || user.value.password.length >= 3 || (user.value.sendPassword && validEmail.value)))
        || (openPk.value === -1 && (user.value.password.length >= 3 || (user.value.sendPassword && validEmail.value)));
  return p && user.value.username !== '' && user.value.family !== '' && user.value.name !== '' && snilsValid.value;
});

const modules = computed(() => store.getters.modules);
const l2UserData = computed(() => store.getters.user_data);
const hospitals = computed(() => store.getters.hospitals);

const canEditAnyOrganization = computed(() => l2UserData.value.su || l2UserData.value.all_hospitals_users_control);

const userHospital = computed(() => l2UserData.value.hospital || -1);

const ownHospital = computed(() => [hospitals.value.find(({ id }) => id === l2UserData.value.hospital) || {}]);

// method block
const openSchedule = (pk) => {
  window.open(`/ui/schedule#${UrlData.objectToData({ resourceSelected: pk })}`, '_blank');
};

const currentResourceResearches = (row) => {
  for (const res of resourceTemplatesList.value) {
    if (row.pk === res.pk) {
      resourceResearches.value = res.researches;
      currentResourcePk.value = row.pk;
      currentResourceTitle.value = res.title;
      break;
    }
  }
};

const getAllAnalyzers = async () => {
  const list = await api('analyzers/all-analyzers');
  analyzersList.value = list.data;
};

const changeSetupForbidden = () => {
  setupForbidden.value = !setupForbidden.value;
};

const restrictedOfPrice = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok } = await api('users/update-restricted-directions', {
    userPk: user.value.doc_pk,
    hospitalPk: selectedHospital.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'успешно');
  } else {
    root.$emit('msg', 'error', 'ошибка');
  }
};

const cancelRestricted = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok } = await api('users/cancel-restricted-directions', {
    userPk: user.value.doc_pk,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'успешно');
  } else {
    root.$emit('msg', 'error', 'ошибка');
  }
};

const changeSetupAnalyzer = () => {
  setupAnalyzer.value = !setupAnalyzer.value;
};

const changeSetupResource = () => {
  setupResource.value = !setupResource.value;
};

const genUsername = () => {
  let v = `${user.value.family} ${user.value.name} ${user.value.patronymic}`;
  let ls = v.split(' ');
  if (ls.length > 3) {
    ls = [ls[0], ls.slice(1, ls.length - 2).join(' '), ls[ls.length - 1] || ''];
  }
  while (ls.length <= 2) {
    ls.push(' ');
  }
  v = ls[0] + (ls[1][0] || '') + (ls[2][0] || '');
  v = toTranslit(v.replace(/\s/g, '')) + strRand(3, 2);
  user.value.username = v;
  root.$emit('msg', 'ok', 'Имя пользователя сгенерировано');
};

const debGu = debounce(() => {
  genUsername();
}, 500);

const genPasswd = () => {
  user.value.password = strRand();
};

const loadUsers = async (prevClr = false) => {
  await store.dispatch(actions.INC_LOADING);
  if (!prevClr) {
    departments.value = [];
  }
  const data = await usersPoint.loadUsers({ selected_hospital: selectedHospital.value });
  departments.value = data.departments;
  specialities.value = data.specialities;
  positions.value = data.positions;
  districts.value = data.districts;
  doctorProfiles.value = data.doctorProfiles;
  await store.dispatch(actions.DEC_LOADING);
};

const reloadResources = async () => {
  if (!openPk.value) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const { userTmp } = await usersPoint.loadUser({ pk: this.openPk });
  user.value.resource_schedule = userTmp.resource_schedule;
  resourceTemplatesList.value = user.value.resource_schedule;
  await store.dispatch(actions.DEC_LOADING);
};

const saveResource = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('schedule/save-resource', {
    pk: user.value.doc_pk,
    resource_researches: resourceResearches.value,
    res_pk: currentResourcePk.value,
    res_title: currentResourceTitle.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', message);
    if (currentResourcePk.value === -1) {
      currentResourceTitle.value = '';
      resourceResearches.value = [];
    }
    await reloadResources();
  }
};

const save = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, npk, message } = await usersPoint.saveUser({
    pk: openPk.value,
    user_data: user.value,
    groupsAnalyzer: analyzers.value,
    hospital_pk: selectedHospital.value,
  });
  if (ok) {
    root.$emit(
      'msg',
      'ok',
      `Пользователь сохранён\n${user.value.family} ${user.value.name} ${user.value.patronymic} – ${user.value.username}`,
    );
    openPk.value = npk;
    await loadUsers(true);
    if (user.value.sendPassword && validEmail.value) {
      user.value.password = '';
    }
    user.value.sendPassword = false;
  } else {
    root.$emit('msg', 'error', `Ошибка\n${message}`);
  }
  await store.dispatch(actions.DEC_LOADING);
};

const close = async () => {
  openPk.value = -2;
  analyzers.value = [];
  user.value = {
    username: '',
    password: '',
    family: '',
    name: '',
    patronymic: '',
    department: '',
    email: '',
    snils: '',
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
    rooms: '',
    rooms_list: [],
    available_quotas_time: '',
    max_age_patient_registration: null,
    users_services: [],
    restricted_to_direct: [],
    district: null,
    groups: [],
    groups_list: [],
    position: null,
    speciality: null,
  };
  currentResourcePk.value = -1;
  currentResourceTitle.value = '';
  resourceResearches.value = [];
};

const open = async (pk, dep = null) => {
  if ((pk === openPk.value && pk !== -1) || (openPk.value === -1 && pk === -1 && dep === user.value.department)) {
    return;
  }
  await close();
  await store.dispatch(actions.INC_LOADING);
  const data = await usersPoint.loadUser({ pk });
  user.value = data.user;
  if (pk === -1) {
    user.value.department = dep;
    genPasswd();
  }
  currentResourcePk.value = -1;
  currentResourceTitle.value = '';
  resourceResearches.value = [];
  resourceTemplatesList.value = user.value.resource_schedule;
  await store.dispatch(actions.DEC_LOADING);
  openPk.value = pk;
};

// created block setup в created все делает
loadUsers();
currentResourcePk.value = -1;
resourceResearches.value = [];
currentResourceTitle.value = '';

watch(() => user.value.family, () => {
  user.value.family = user.value.family
    .replace(/\s\s+/g, ' ')
    .split(' ')
    .map((s) => s
      .split('-')
      .map((x) => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase())
      .join('-'))
    .join(' ');
  if (openPk.value === -1) {
    debGu();
  }
});

watch(() => user.value.name, () => {
  user.value.name = user.value.name
    .replace(/\s\s+/g, ' ')
    .split(' ')
    .map((s) => s
      .split('-')
      .map((x) => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase())
      .join('-'))
    .join(' ');
  if (openPk.value === -1) {
    debGu();
  }
});

watch(() => user.value.patronymic, () => {
  user.value.patronymic = user.value.patronymic
    .replace(/\s\s+/g, ' ')
    .split(' ')
    .map((s) => s
      .split('-')
      .map((x) => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase())
      .join('-'))
    .join(' ');
  if (openPk.value === -1) {
    debGu();
  }
});

watch(() => user.value.external_access, () => {
  if (!user.value.external_access) {
    user.value.date_stop_external_access = '';
  }
});

watch(() => userHospital.value, () => {
  if (selectedHospital.value !== -1 || userHospital.value === -1) {
    return;
  }
  selectedHospital.value = userHospital.value;
}, { immediate: true });

watch(() => selectedHospital.value, () => {
  if (selectedHospital.value === -1) {
    return;
  }
  loadUsers();
});

watch(() => resourceResearches.value, () => {
  if (resourceResearches.value.length === 0) {
    currentResourcePk.value = -1;
  }
});

onMounted(() => {
  getAllAnalyzers();
});
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
