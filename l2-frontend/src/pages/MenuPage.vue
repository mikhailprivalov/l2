<template>
  <div v-frag>
    <div :class="chatsEnabled && 'menu-wrapper'">
      <div :class="chatsEnabled && 'menu-left'">
        <div class="panel panel-default panel-flt">
          <ul class="list-group">
            <li class="list-group-item">
              <div class="row">
                <div class="col-xs-12 col-md-6 col-lg-6">
                  Вход выполнен как: {{ user_data.username }}
                  <a
                    v-if="changePassword"
                    href="#"
                    class="a-under"
                    @click="modalPassword = true"
                  >сменить&nbsp;пароль</a>
                  <template v-if="changePassword">
                    <br>
                    Email:
                    <a
                      v-if="email"
                      v-tippy
                      href="#"
                      class="a-under-reversed"
                      title="Редактировать адрес"
                      @click="modalEmail = true"
                    >
                      <span class="a-internal">{{ email }}</span> <i class="fa fa-pencil" />
                    </a>
                    <a
                      v-else
                      href="#"
                      class="a-under"
                      @click="modalEmail = true"
                    >установить email</a>
                  </template>
                  <br>
                  Двухфакторная аутентификация:
                  <a
                    href="#"
                    class="a-under-reversed"
                    @click="modalTwoFactor = true"
                  >{{ hasTOTP ? 'активирована' : 'не активна' }} <i class="fa fa-pencil" /></a>
                  <br>
                  Изменить пароль:
                  <span class="change-password-links">
                    <a
                      href="#"
                      class="a-under"
                      @click="modalL2Password = true"
                    >L2</a>
                    <a
                      v-if="showRmisChangePassword"
                      href="#"
                      class="a-under"
                      @click="modalRmis = true"
                    >РМИС</a>
                  </span>
                </div>
                <div class="col-xs-12 col-md-6 col-lg-6 text-right text-left-xs">
                  {{ fio_dep }}
                  <br>
                  <a
                    href="/logout"
                    class="btn btn-blue-nb"
                  >Выход</a>
                </div>
              </div>
            </li>
            <li class="list-group-item">
              Ваши права доступа и группы:
              <div class="row dash-buttons groups-btns">
                <div
                  v-for="g in user_data.groups"
                  :key="g"
                  class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb5"
                >
                  <div
                    class="label label-default bw100 btn-ell"
                    :title="g"
                  >
                    {{ g }}
                  </div>
                </div>
              </div>
            </li>
            <li
              v-if="user_data.specialities && user_data.specialities.length > 0"
              class="list-group-item"
            >
              Специальности:
              <div
                v-for="s in user_data.specialities"
                :key="s"
                class="row dash-buttons groups-btns"
              >
                <div class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb5">
                  <div
                    class="label label-default bw100 btn-ell"
                    :title="s"
                  >
                    {{ s }}
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </div>
        <div class="row menu dash-buttons text-center">
          <div
            v-for="b in buttons"
            :key="b.title"
            class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb10 dash-btn"
          >
            <router-link
              :to="b.url"
              class="panel-body"
              :target="b.nt && '_blank'"
            >
              <span>{{ b.title }}</span>
            </router-link>
          </div><div
            v-if="forms_url"
            class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb10 dash-btn"
          >
            <router-link
              :to="forms_url"
              class="panel-body"
              target="_blank"
            >
              <span><i class="fas fa-comment" /> Оставить отзыв</span>
            </router-link>
          </div>
        </div>
        <hr>
        <div class="row dash-buttons text-center">
          <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 mb10 dash-btn dash-info">
            <div class="panel-body">
              <span>
                <span>{{ system }}</span>
                <br>
                <span>{{ menu.version }}</span>
              </span>
            </div>
          </div>
          <div
            v-if="menu.region === '38'"
            class="col-xs-12 col-sm-6 col-md-6 col-lg-6 mb10 dash-btn dash-info"
          >
            <a
              href="http://l2-irk.ru"
              target="_blank"
              class="panel-body"
            >
              <span>l2-irk.ru</span>
            </a>
          </div>
          <div
            v-else-if="menu.region === 'DEMO'"
            class="col-xs-12 col-sm-6 col-md-4 col-lg-4 mb10 dash-btn dash-info"
          >
            <div class="panel-body">
              <span>
                <span>DEMO</span>
              </span>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="chatsEnabled"
        class="menu-right"
      >
        <ChatsBody />
      </div>
    </div>
    <MountingPortal
      mount-to="#portal-place-modal"
      name="ChangePassword"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modalPassword"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          :no-close="!!loading"
          @close="modalPassword = false"
        >
          <span slot="header">Смена пароля</span>
          <div
            v-if="email"
            slot="body"
            class="popup-body"
          >
            Ваш email: <strong>{{ email }}</strong>
            <br>
            Новый пароль будет отправлен вам на почту!<br>
            После получения пароля войдите в систему заново.<br>
            Все активные сессии будут прекращены (включая текущую).
            <br><br>
            <button
              class="btn btn-blue-nb"
              :disabled="loading"
              type="button"
              @click="doChangePassword"
            >
              Сменить пароль
            </button>
          </div>
          <div
            v-else
            slot="body"
            class="popup-body"
          >
            <div class="alert-modal">
              В вашем профиле не настроен <strong>email адрес</strong>!
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button
                  class="btn btn-blue-nb"
                  :disabled="loading"
                  type="button"
                  @click="modalPassword = false"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
    <MountingPortal
      mount-to="#portal-place-modal"
      name="TOTP"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modalTwoFactor"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          :no-close="!!loading"
          @close="modalTwoFactor = false"
        >
          <span slot="header">Двухфакторная аутентификация</span>
          <div
            v-if="!hasTOTP"
            slot="body"
            class="popup-body"
          >
            <div class="alert-modal">
              Двухфакторная аутентификация не настроена!
            </div>
            <div class="alert-modal">
              Для настройки двухфакторной аутентификации вам необходимо установить приложение<br>
              <strong>TOTP совместимое приложение</strong> на ваш мобильный телефон<br>
              или воспользоваться специальными сервисами.
            </div>
            <div>
              <img
                :src="secretQRBase64"
                alt="qr-code"
                class="qr-code"
              >
              <input
                :value="secretCode"
                type="text"
                class="form-control mb10"
                readonly
              >
              <input
                v-model="checkCode"
                type="text"
                class="form-control mb10"
                placeholder="Введите код из приложения"
              >
              <button
                class="btn btn-blue-nb"
                :disabled="loading"
                type="button"
                @click="doCheckCode"
              >
                Проверить код
              </button>
            </div>
          </div>
          <div
            v-else
            slot="body"
            class="popup-body"
          >
            <div class="alert-modal">
              Двухфакторная аутентификация настроена!
            </div>
            <div class="alert-modal">
              Для отключения двухфакторной аутентификации вам необходимо ввести код из приложения.
            </div>
            <div>
              <input
                v-model="checkCode"
                type="text"
                class="form-control mb10"
                placeholder="Введите код из приложения"
              >
              <button
                class="btn btn-blue-nb"
                :disabled="loading"
                type="button"
                @click="doCheckCodeDisable"
              >
                Проверить код и отключить двухфакторную аутентификацию
              </button>
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button
                  class="btn btn-blue-nb"
                  :disabled="loading"
                  type="button"
                  @click="modalTwoFactor = false"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
    <MountingPortal
      mount-to="#portal-place-modal"
      name="SetL2Password"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modalL2Password"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          :no-close="!!loading"
          @close="modalL2Password = false"
        >
          <span slot="header">L2</span>
          <div
            slot="body"
            class="popup-body"
          >
            <input
              v-model="oldPassword"
              type="password"
              class="form-control mb10"
              placeholder="Текущий пароль"
              autocomplete="current-password"
            >
            <input
              v-model="newPassword"
              type="password"
              class="form-control mb10"
              placeholder="Новый пароль (минимум 6 символов)"
              autocomplete="new-password"
            >
            <input
              v-model="confirmPassword"
              type="password"
              class="form-control mb10"
              placeholder="Подтверждение пароля"
              autocomplete="new-password"
            >
            <button
              class="btn btn-blue-nb"
              :disabled="loading"
              type="button"
              @click="doSetPassword"
            >
              Сохранить
            </button>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button
                  class="btn btn-blue-nb"
                  :disabled="loading"
                  type="button"
                  @click="modalL2Password = false"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
    <MountingPortal
      mount-to="#portal-place-modal"
      name="SetRmis"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modalRmis"
          show-footer="true"
          white-bg="true"
          max-width="1100px"
          width="100%"
          margin-left-right="auto"
          :no-close="!!loading"
          @close="modalRmis = false"
        >
          <span slot="header">РМИС</span>
          <div
            slot="body"
            class="popup-body"
          >
            <input
              v-model.trim="rmis_login"
              type="text"
              class="form-control mb10"
              placeholder="РМИС логин"
            >
            <div class="rmis-password-row mb10">
              <input
                v-model="rmis_password"
                type="password"
                class="form-control rmis-password-input"
                placeholder="РМИС пароль (для замены введите значение)"
                autocomplete="new-password"
              >
              <span
                v-if="rmisPasswordHint"
                class="rmis-password-hint"
              >{{ rmisPasswordHint }}</span>
            </div>
            <button
              class="btn btn-blue-nb mr10"
              :disabled="loading"
              type="button"
              @click="doCheckRmis"
            >
              Проверить
            </button>
            <button
              class="btn btn-blue-nb"
              :disabled="loading"
              type="button"
              @click="doSetRmis"
            >
              Сохранить
            </button>
            <div
              v-if="ecpPositions.length"
              class="rmis-ecp-wrap"
            >
              <table class="table table-condensed table-bordered rmis-ecp-table">
                <colgroup>
                  <col class="col-type-medical-form">
                  <col class="col-arm-type">
                  <col>
                  <col>
                  <col class="col-med-staff-fact-stavka">
                  <col class="col-lpu-section-name">
                </colgroup>
                <thead>
                  <tr>
                    <th>Тип медпомощи</th>
                    <th class="col-arm-type">
                      arm_type
                    </th>
                    <th>med_staff_fact_id</th>
                    <th>lpu_section_id</th>
                    <th class="col-med-staff-fact-stavka">
                      med_staff_fact_stavka
                    </th>
                    <th class="col-lpu-section-name">
                      lpu_section_name
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in ecpPositions"
                    :key="row.id"
                  >
                    <td>
                      <select
                        v-model="row.type_medical_form"
                        class="form-control rmis-type-select"
                      >
                        <option value="unset">
                          Не установлено
                        </option>
                        <option
                          value="emergency"
                          :disabled="isTypeMedicalFormTaken('emergency', row.id)"
                        >
                          Экстренная служба
                        </option>
                        <option
                          value="stationary"
                          :disabled="isTypeMedicalFormTaken('stationary', row.id)"
                        >
                          Стационар
                        </option>
                      </select>
                    </td>
                    <td class="col-arm-type">
                      {{ row.arm_type || '—' }}
                    </td>
                    <td>{{ row.med_staff_fact_id || '—' }}</td>
                    <td>{{ row.lpu_section_id || '—' }}</td>
                    <td class="col-med-staff-fact-stavka">
                      {{ row.med_staff_fact_stavka || '—' }}
                    </td>
                    <td class="col-lpu-section-name">
                      {{ row.lpu_section_name || '—' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button
                  class="btn btn-blue-nb"
                  :disabled="loading"
                  type="button"
                  @click="modalRmis = false"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
    <MountingPortal
      mount-to="#portal-place-modal"
      name="Email"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modalEmail"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          :no-close="!!loading"
          @close="modalEmail = false"
        >
          <span slot="header">Установка email</span>
          <div
            v-if="!hasNewCodeRequest"
            slot="body"
            class="popup-body"
          >
            Ваш текущий email: <strong>{{ email || 'не установлен' }}</strong>
            <br>
            <div
              v-if="email && !hasCodeRequest"
              class="alert-modal"
            >
              Для установки нового адреса запросите код на предыдущий.<br>
              Если у вас нет доступа к {{ email }}, то обратитесь к администратору.
            </div>
            <button
              v-if="needCodeRequest"
              class="btn btn-blue-nb"
              :disabled="loading"
              type="button"
              @click="requestCode"
            >
              Запросить код
            </button>

            <input
              v-else-if="email"
              v-model.trim="confirmationCode"
              type="text"
              class="form-control"
              style="margin-bottom: 10px;"
              :placeholder="`Код с ${email}`"
              :readonly="loading"
            >

            <template v-if="!needCodeRequest">
              <input
                v-model.trim="newEmail"
                type="email"
                class="form-control"
                placeholder="Новый адрес"
                style="margin-bottom: 5px;"
                :readonly="loading"
              >
              <div v-if="newEmailIsNotValid">
                {{ newEmailIsNotValid }}
              </div>

              <button
                class="btn btn-blue-nb"
                style="margin-top: 5px;"
                :disabled="loading || !!newEmailIsNotValid || (!confirmationCode && !!email)"
                type="button"
                @click="setNewEmail"
              >
                Установить email
              </button>
            </template>
          </div>
          <div
            v-else
            slot="body"
            class="popup-body"
          >
            <a
              class="a-under"
              :style="loading ? 'opacity: 0' : ''"
              href="#"
              @click.prevent="hasNewCodeRequest = loading"
            >
              вернуться назад
            </a>
            <br>
            Подтвердите
            <span v-if="email">
              смену адреса с <strong>{{ email }}</strong> на
            </span>
            <span v-else>установку адреса</span>
            <strong>{{ newEmail }}</strong>
            <br>
            Вам был отправлен код на новый адрес.
            <br>

            <input
              v-model.trim="newConfirmationCode"
              type="text"
              class="form-control"
              style="margin-bottom: 5px;"
              :placeholder="`Код с ${newEmail}`"
              :readonly="loading"
            >

            <button
              class="btn btn-blue-nb"
              :disabled="!newConfirmationCode || loading"
              type="button"
              @click="confirmNewEmail"
            >
              Подтвердить
            </button>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button
                  class="btn btn-blue-nb"
                  :disabled="loading"
                  type="button"
                  @click="modalEmail = false"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { mapGetters } from 'vuex';

import Modal from '@/ui-cards/Modal.vue';
import { Button, Menu } from '@/types/menu';
import { validateEmail } from '@/utils';
import ChatsBody from '@/ui-cards/Chat/ChatsBody.vue';

const TYPE_MEDICAL_FORM_UNSET = 'unset';
const TYPE_MEDICAL_FORM_EMERGENCY = 'emergency';
const TYPE_MEDICAL_FORM_STATIONARY = 'stationary';

function normalizeTypeMedicalForm(value: unknown) {
  if (value === null || value === undefined || value === '' || value === TYPE_MEDICAL_FORM_UNSET) {
    return TYPE_MEDICAL_FORM_UNSET;
  }
  if (value === 0 || value === '0' || value === TYPE_MEDICAL_FORM_EMERGENCY) {
    return TYPE_MEDICAL_FORM_EMERGENCY;
  }
  if (value === 1 || value === '1' || value === TYPE_MEDICAL_FORM_STATIONARY) {
    return TYPE_MEDICAL_FORM_STATIONARY;
  }
  return TYPE_MEDICAL_FORM_UNSET;
}

function serializeTypeMedicalForm(value: string) {
  if (value === TYPE_MEDICAL_FORM_EMERGENCY) {
    return 0;
  }
  if (value === TYPE_MEDICAL_FORM_STATIONARY) {
    return 1;
  }
  return null;
}

function mapEcpPositionRows(rows: Array<Record<string, unknown>>) {
  return (rows || []).map(row => ({
    id: row.id as number,
    type_medical_form: normalizeTypeMedicalForm(row.type_medical_form),
    arm_type: (row.arm_type as string) || '',
    med_staff_fact_id: (row.med_staff_fact_id as string) || '',
    lpu_section_id: (row.lpu_section_id as string) || '',
    med_staff_fact_stavka: (row.med_staff_fact_stavka as string) || '',
    lpu_section_name: (row.lpu_section_name as string) || '',
  }));
}

function validateUniqueTypeMedicalForm(
  rows: Array<{ type_medical_form: string }>,
) {
  const labels: Record<string, string> = {
    [TYPE_MEDICAL_FORM_EMERGENCY]: 'Экстренная служба',
    [TYPE_MEDICAL_FORM_STATIONARY]: 'Стационар',
  };
  const seen = new Set<string>();

  for (const row of rows) {
    const type = row.type_medical_form;
    if (type === TYPE_MEDICAL_FORM_UNSET) {
      continue;
    }
    if (seen.has(type)) {
      return `Тип медпомощи «${labels[type]}» указан более одного раза`;
    }
    seen.add(type);
  }

  return null;
}

@Component({
  components: { ChatsBody, Modal },
  data() {
    return {
      modalPassword: false,
      modalEmail: false,
      loading: false,
      newEmail: '',
      newEmailCode: '',
      hasCodeRequest: false,
      hasNewCodeRequest: false,
      confirmationCode: '',
      newConfirmationCode: '',
      modalTwoFactor: false,
      modalL2Password: false,
      modalRmis: false,
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
      rmis_login: '',
      rmis_password: '',
      rmisPasswordHint: '',
      ecpPositions: [],
      secretQRBase64: null,
      secretCode: null,
      checkCode: '',
    };
  },
  watch: {
    modalL2Password(open) {
      if (!open) {
        this.oldPassword = '';
        this.newPassword = '';
        this.confirmPassword = '';
        this.loading = false;
      }
    },
    modalRmis(open) {
      if (open) {
        this.rmis_login = this.user_data?.rmis_login || '';
        this.rmis_password = '';
        this.loadEcpPositions();
      } else {
        this.rmis_login = '';
        this.rmis_password = '';
        this.rmisPasswordHint = '';
        this.ecpPositions = [];
        this.loading = false;
      }
    },
    modalEmail() {
      this.hasCodeRequest = false;
      this.hasNewCodeRequest = false;
      this.newEmail = '';
      this.confirmationCode = '';
      this.newConfirmationCode = '';
      this.loading = false;
    },
    hasNewCodeRequest() {
      this.newConfirmationCode = '';
    },
    async modalTwoFactor() {
      if (this.modalTwoFactor) {
        if (!this.hasTOTP) {
          this.loading = true;
          const {
            qrCode = null, secretCode = null, ok, message,
          } = await this.$api('users/generate-totp-code');
          if (!ok) {
            this.$root.$emit('msg', 'error', message);
            this.modalTwoFactor = false;
          }
          this.loading = false;
          this.secretQRBase64 = qrCode;
          this.secretCode = secretCode;
        }
      } else {
        this.secretQRBase64 = null;
        this.secretCode = null;
      }
      this.checkCode = '';
    },
  },
  computed: {
    ...mapGetters(['menu', 'user_data']),
    buttons() {
      if (!this.menu?.buttons) {
        return [];
      }

      return this.menu.buttons.filter(b => !b.not_show_home && !b.hr);
    },
    fio_dep() {
      return [this.user_data?.fio, this.user_data?.department.title].filter(Boolean).join(', ');
    },
    email() {
      return this.user_data?.email;
    },
    hasTOTP() {
      return this.user_data?.hasTOTP;
    },
    forms_url() {
      return this.user_data?.modules.forms_url;
    },
    changePassword() {
      return this.$store.getters.modules.change_password;
    },
    showRmisChangePassword() {
      return !!this.$store.getters.modules.show_rmis_change_password;
    },
  },
})
export default class MenuPage extends Vue {
  menu: Menu;

  buttons: Button[];

  fio_dep: string;

  forms_url: string;

  changePassword: boolean;

  showRmisChangePassword: boolean;

  modalPassword: boolean;

  modalEmail: boolean;

  loading: boolean;

  email: string | null;

  newEmail: string;

  newEmailCode: string;

  confirmationCode: string;

  newConfirmationCode: string;

  hasCodeRequest: boolean;

  hasNewCodeRequest: boolean;

  modalTwoFactor: boolean;

  modalL2Password: boolean;

  modalRmis: boolean;

  oldPassword: string;

  newPassword: string;

  confirmPassword: string;

  rmis_login: string;

  rmis_password: string;

  rmisPasswordHint: string;

  ecpPositions: Array<{
    id: number;
    type_medical_form: string;
    arm_type: string;
    med_staff_fact_id: string;
    lpu_section_id: string;
    med_staff_fact_stavka: string;
    lpu_section_name: string;
  }>;

  secretQRBase64: string | null;

  secretCode: string | null;

  checkCode: string;

  get system() {
    return this.$systemTitle();
  }

  get newEmailIsNotValid() {
    if (!this.newEmail) {
      return 'Введите email';
    }

    if (!validateEmail(this.newEmail)) {
      return 'Некорректный email';
    }

    if (this.email === this.newEmail) {
      return 'Email совпадает с текущим';
    }

    return false;
  }

  get needCodeRequest() {
    return !this.hasCodeRequest && !!this.email;
  }

  async doSetPassword() {
    if (!this.oldPassword) {
      this.$root.$emit('msg', 'error', 'Введите текущий пароль');
      return;
    }
    if (this.newPassword.length < 6) {
      this.$root.$emit('msg', 'error', 'Пароль должен содержать минимум 6 символов');
      return;
    }
    if (this.newPassword !== this.confirmPassword) {
      this.$root.$emit('msg', 'error', 'Пароли не совпадают');
      return;
    }

    this.loading = true;

    try {
      const { ok, message } = await this.$api(
        '/users/set-password',
        this,
        ['oldPassword', 'newPassword', 'confirmPassword'],
      );
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Пароль изменён. Войдите в систему заново.', 15000);
        this.$router.push('login');
        return;
      }

      this.$root.$emit('msg', 'error', message || 'Что-то пошло не так');
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
    }
    this.loading = false;
  }

  async loadEcpPositions() {
    try {
      const { ok, rows, rmis_password_hint: rmisPasswordHint } = await this.$api('users/get-ecp-positions');
      if (!ok) {
        this.ecpPositions = [];
        this.rmisPasswordHint = '';
        return;
      }
      this.ecpPositions = mapEcpPositionRows(rows);
      this.rmisPasswordHint = rmisPasswordHint || '';
    } catch (error) {
      this.ecpPositions = [];
      this.rmisPasswordHint = '';
      // eslint-disable-next-line no-console
      console.error(error);
    }
  }

  serializeEcpPositions() {
    return this.ecpPositions.map(row => ({
      id: row.id,
      type_medical_form: serializeTypeMedicalForm(row.type_medical_form),
    }));
  }

  isTypeMedicalFormTaken(type: string, currentRowId: number) {
    if (type === TYPE_MEDICAL_FORM_UNSET) {
      return false;
    }
    return this.ecpPositions.some(
      row => row.id !== currentRowId && row.type_medical_form === type,
    );
  }

  async doCheckRmis() {
    const rmisLogin = (this.rmis_login || '').trim();
    if (!rmisLogin) {
      this.$root.$emit('msg', 'error', 'Укажите логин РМИС');
      return;
    }

    this.loading = true;

    try {
      const { ok, message, rows } = await this.$api('/users/check-rmis', null, null, {
        rmis_login: rmisLogin,
        rmis_password: this.rmis_password,
      });
      if (ok) {
        this.ecpPositions = mapEcpPositionRows(rows);
      } else {
        await this.loadEcpPositions();
      }
      this.$root.$emit('msg', ok ? 'ok' : 'error', message || (ok ? 'Авторизация успешна' : 'Ошибка авторизации'));
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
    }
    this.loading = false;
  }

  async doSetRmis() {
    const typeMedicalFormError = validateUniqueTypeMedicalForm(this.ecpPositions);
    if (typeMedicalFormError) {
      this.$root.$emit('msg', 'error', typeMedicalFormError);
      return;
    }

    this.loading = true;
    const rmisLogin = (this.rmis_login || '').trim();

    try {
      const {
        ok,
        message,
        rmis_login: savedLogin,
        rmis_password_hint: rmisPasswordHint,
      } = await this.$api('/users/set-rmis', null, null, {
        rmis_login: rmisLogin,
        rmis_password: this.rmis_password,
        ecp_positions: this.serializeEcpPositions(),
      });
      if (ok) {
        this.$store.commit('SET_USER_DATA', {
          data: { rmis_login: savedLogin ?? rmisLogin },
        });
        this.rmis_login = savedLogin ?? rmisLogin;
        this.rmis_password = '';
        this.rmisPasswordHint = rmisPasswordHint || '';
        this.$root.$emit('msg', 'ok', 'Данные РМИС сохранены');
        return;
      }

      this.$root.$emit('msg', 'error', message || 'Что-то пошло не так');
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
    } finally {
      this.loading = false;
    }
  }

  async doChangePassword() {
    try {
      await this.$dialog.confirm('Вы действительно хотите сменить пароль и выйти из системы?');
    } catch (_) {
      return;
    }

    this.loading = true;

    try {
      const { ok, message } = await this.$api('/users/change-password');
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Успешно. Проверьте почту и повторите вход в систему!', 15000);
        this.$router.push('login');
        return;
      }

      this.$root.$emit('msg', 'error', message || 'Что-то пошло не так');
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
    }
    this.loading = false;
  }

  async requestCode() {
    this.loading = true;
    const { ok, message } = await this.$api('/users/set-new-email', {
      step: 'request-code',
    });
    if (ok) {
      this.hasCodeRequest = true;
    } else {
      this.$root.$emit('msg', 'error', message);
    }
    this.loading = false;
  }

  async setNewEmail() {
    this.loading = true;
    const { ok, message } = await this.$api('/users/set-new-email', this, ['newEmail', 'confirmationCode'], {
      step: 'set-new-email',
    });
    if (ok) {
      this.hasNewCodeRequest = true;
    } else {
      this.$root.$emit('msg', 'error', message);
    }
    this.loading = false;
  }

  async confirmNewEmail() {
    this.loading = true;
    const { ok, message } = await this.$api(
      '/users/set-new-email',
      this,
      ['newEmail', 'confirmationCode', 'newConfirmationCode'],
      {
        step: 'confirm-new-email',
      },
    );
    if (ok) {
      this.$root.$emit('msg', 'ok', 'Успешно. Страница будет перезагружена', 10000);
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } else {
      this.$root.$emit('msg', 'error', message);
      this.loading = false;
    }
  }

  async doCheckCode() {
    this.loading = true;
    const { ok, message } = await this.$api('/users/set-totp', this, 'secretCode', {
      confirmationCode: this.checkCode,
    });
    if (ok) {
      this.$root.$emit('msg', 'ok', 'Двухфакторная аутентификация активирована');
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } else {
      this.$root.$emit('msg', 'error', message);
      this.loading = false;
    }
  }

  async doCheckCodeDisable() {
    this.loading = true;
    const { ok, message } = await this.$api('/users/disable-totp', {
      confirmationCode: this.checkCode,
    });
    if (ok) {
      this.$root.$emit('msg', 'ok', 'Двухфакторная аутентификация отключена');
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } else {
      this.$root.$emit('msg', 'error', message);
      this.loading = false;
    }
  }

  get chatsEnabled() {
    return this.$store.getters.chatsEnabled;
  }
}
</script>

<style lang="scss" scoped>
.qr-code {
  width: 100%;
  max-width: 200px;
  margin: 10px auto;
}

.groups-btns {
  padding: 0;
  margin-right: 0;
  margin-left: 0;
}

.mb5 {
  margin-bottom: 5px;
}

.mb10 {
  margin-bottom: 5px;
}

.menu.dash-buttons > div.mb10 {
  margin-right: 0;
}

.menu.row.dash-buttons {
  margin-right: -2px;
  margin-left: -2px;
}

.change-password-links {
  a + a {
    margin-left: 8px;
  }
}

.mr10 {
  margin-right: 10px;
}

.rmis-password-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rmis-password-input {
  flex: 1;
  min-width: 0;
}

.rmis-password-hint {
  flex: 0 0 auto;
  font-family: monospace;
  color: #666;
  white-space: nowrap;
}

.rmis-ecp-wrap {
  margin-top: 15px;
  overflow-x: auto;
}

.rmis-ecp-table {
  margin-bottom: 0;
  font-size: 12px;
  table-layout: fixed;
  width: 100%;

  th,
  td {
    vertical-align: middle;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .col-type-medical-form {
    width: 190px;
  }

  .col-arm-type {
    width: 72px;
  }

  .col-med-staff-fact-stavka {
    width: 72px;
  }

  .col-lpu-section-name {
    width: auto;
    min-width: 220px;
    white-space: normal;
  }
}

.rmis-type-select {
  height: 34px;
  padding: 4px 6px;
  font-size: 12px;
}

.alert-modal {
  margin: 0 0 15px 0;
  padding: 10px;
  background-color: rgba(0, 0, 0, 8%);
  border-radius: 4px;
}

.a-under:not(:hover),
.a-under-reversed:not(:hover) {
  .a-internal {
    color: #000;
  }
}

.menu-wrapper {
  display: flex;
  flex-direction: row;
  position: relative;
}

.menu-left {
  flex: 1;
}

.menu-right {
  position: sticky;
  top: 20px;
  flex: 0 0 300px;
  margin-left: 20px;
  min-height: 500px;
  height: calc(100vh - 66px);
  border: 1px solid #A6B5AA;
  background: #E6E9ED;
  border-radius: 4px;
  overflow: hidden;
}

@media screen and (max-width: 768px) {
  .menu-wrapper {
    flex-direction: column;
  }

  .menu-left {
    flex: 0 0 100%;
  }

  .menu-right {
    position: relative;
    flex: 0 0 100%;
    margin-left: 0;
    margin-top: 20px;
    height: 500px;
  }
}
</style>
