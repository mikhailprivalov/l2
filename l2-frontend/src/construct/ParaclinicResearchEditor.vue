<template>
  <div class="root">
    <div
      class="top-editor"
      :class="{ simpleEditor: simple, formEditor: ex_dep === 12, oneLine: ex_dep === 13 || ex_dep === 14 || ex_dep === 15 }"
    >
      <div class="left">
        <div class="input-group">
          <span
            v-if="ex_dep === 12"
            class="input-group-addon"
          > Название шаблона параметров направления ({{ loaded_pk }}) </span>
          <span
            v-else-if="ex_dep === 13"
            class="input-group-addon"
          >
            Название заявления
          </span>
          <span
            v-else-if="ex_dep === 14"
            class="input-group-addon"
          >Название мониторинга</span>
          <span
            v-else-if="ex_dep === 15"
            class="input-group-addon"
          >Название экспертизы</span>
          <span
            v-else
            class="input-group-addon"
          >Полное наименование</span>
          <input
            v-model="title"
            type="text"
            class="form-control"
          >
          <label
            v-if="ex_dep === 12"
            class="input-group-addon"
            style="height: 34px;text-align: left;"
          >
            <input
              v-model="is_global_direction_params"
              type="checkbox"
            > Глобальный
          </label>
          <span
            v-if="(ex_dep === 12 || simple) && fte && ex_dep !== 14"
            class="input-group-btn"
          >
            <button
              class="btn btn-blue-nb"
              type="button"
              style="border-radius: 0;width: 100%;"
              :disabled="has_unsaved || loaded_pk < 0"
              @click="f_templates()"
            >
              Шаблоны быстрого ввода
            </button>
          </span>
        </div>
        <div
          v-if="ex_dep !== 12 && ex_dep !== 13 && ex_dep !== 14 && ex_dep !== 15"
          class="input-group"
        >
          <span class="input-group-addon">Краткое <small>(для создания направлений)</small></span>
          <input
            v-model="short_title"
            type="text"
            class="form-control"
          >
          <span class="input-group-addon">Профиль</span>
          <select
            v-model="speciality"
            class="form-control"
          >
            <option
              v-for="d in specialities"
              :key="d.pk"
              :value="d.pk"
            >
              {{ d.title }}
            </option>
          </select>
        </div>
      </div>
      <div
        v-if="!simple && ex_dep !== 12 && ex_dep !== 13 && ex_dep !== 15"
        class="right"
      >
        <div
          v-if="department < -1 && ex_dep !== 14"
          class="row"
          style="margin-right: 0;"
        >
          <div
            class="col-xs-6"
            style="padding-right: 0"
          >
            <div
              class="input-group"
              style="margin-right: -1px"
            >
              <span class="input-group-addon">Код ОМС</span>
              <input
                v-model="code"
                type="text"
                class="form-control f-code"
              >
              <span class="input-group-addon">Код Вн</span>
              <input
                v-model="internal_code"
                type="text"
                class="form-control f-code"
              >
            </div>
          </div>
          <div
            class="col-xs-6"
            style="padding-left: 0;padding-right: 0;margin-right: 0;"
          >
            <div class="input-group">
              <label
                v-if="ex_dep !== 8 && ex_dep !== 13 && ex_dep !== 15"
                v-tippy
                class="input-group-addon"
                style="height: 34px;text-align: left;"
                title="Показывать ли форму дополнительных услуг в протоколе"
              >
                <input
                  v-model="show_more_services"
                  type="checkbox"
                > Доп. услуги
              </label>
              <span class="input-group-addon">Подраздел</span>
              <select
                v-model="site_type"
                class="form-control"
              >
                <option
                  v-for="r in ex_deps"
                  :key="r.pk"
                  :value="r.pk"
                >
                  {{ r.title }}
                </option>
              </select>
            </div>
          </div>
        </div>
        <div
          v-else-if="ex_dep === 14"
          class="input-group"
        >
          <span class="input-group-addon">Подраздел</span>
          <select
            v-model="site_type"
            class="form-control"
          >
            <option
              v-for="r in ex_deps"
              :key="r.pk"
              :value="r.pk"
            >
              {{ r.title }}
            </option>
          </select>
          <label
            class="input-group-addon"
            style="height: 34px;text-align: left;"
          >
            <input
              v-model="hide"
              type="checkbox"
            > Скрыть
          </label>
        </div>
        <div
          v-else
          class="input-group"
        >
          <label
            v-if="ex_dep !== 8 && ex_dep !== 15 && ex_dep !== 13"
            class="input-group-addon"
            style="height: 34px;text-align: left;"
          >
            <input
              v-model="show_more_services"
              type="checkbox"
            > Доп.услуги
          </label>
          <span class="input-group-addon">Код ОМC</span>
          <input
            v-model="code"
            type="text"
            class="form-control f-code"
          >
          <span class="input-group-addon">Код Вн</span>
          <input
            v-model="internal_code"
            type="text"
            class="form-control f-code"
          >
          <span class="input-group-addon">УЕТ</span>
          <input
            v-model="uet_refferal_doc"
            type="text"
            class="form-control f-code"
          >
          <span class="input-group-addon">УЕТ(м/с)</span>
          <input
            v-model="uet_refferal_co_executor_1"
            type="text"
            class="form-control f-code"
          >
        </div>
        <div
          v-if="ex_dep !== 14"
          class="input-group"
        >
          <span class="input-group-addon"> Ф.направления </span>
          <select
            v-model="direction_current_form"
            class="form-control"
          >
            <option
              v-for="d in direction_forms"
              :key="d[0]"
              :value="d[0]"
            >
              {{ d[1] }}
            </option>
          </select>
          <label
            class="input-group-addon"
            style="height: 34px;text-align: left;"
          >
            <input
              v-model="hide"
              type="checkbox"
            > Скрыть
          </label>
          <span
            v-if="fte"
            class="input-group-btn"
          >
            <button
              class="btn btn-blue-nb"
              type="button"
              style="border-radius: 0;width: 100%;"
              :disabled="has_unsaved || loaded_pk < 0"
              @click="f_templates()"
            >
              Шаблоны быстрого ввода
            </button>
          </span>
        </div>
      </div>
      <div
        v-else-if="ex_dep === 13"
        class="right"
      >
        <div class="input-group">
          <span class="input-group-addon">Печатная форма</span>
          <select
            v-model="direction_current_form"
            class="form-control"
          >
            <option
              v-for="d in direction_forms"
              :key="d[0]"
              :value="d[0]"
            >
              {{ d[1] }}
            </option>
          </select>
          <label
            class="input-group-addon"
            style="height: 34px;text-align: left;"
          >
            <input
              v-model="hide"
              type="checkbox"
            > Скрыть
          </label>
        </div>
      </div>
    </div>
    <div class="content-editor">
      <template v-if="ex_dep !== 12 && ex_dep !== 13 && ex_dep !== 15">
        <div
          v-if="!simple && ex_dep !== 14"
          class="input-group"
        >
          <span class="input-group-addon nbr">Информация на направлении</span>
          <textarea
            v-model="info"
            v-autosize="info"
            class="form-control noresize"
            rows="1"
          />
        </div>
        <div class="row">
          <div
            class="col-xs-12"
            style="padding-right: 0"
          >
            <div class="input-group">
              <span class="input-group-addon nbr">Ресурс ЕЦП</span>
              <input
                v-model="autoRegisterRmisLocation"
                type="text"
                class="form-control f-code"
              >
            </div>
          </div>
        </div>
        <div class="row">
          <div
            :class="expertise ? 'col-xs-5' : 'col-xs-6'"
            style="padding-right: 0"
          >
            <div class="input-group">
              <span
                class="input-group-addon nbr"
                style="width: 232px"
              >Метод</span>
              <Treeselect
                v-model="currentMethod"
                class="treeselect-nbr treeselect-wide"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="collectMethods"
                placeholder="Код не указан"
                :append-to-body="true"
                :clearable="false"
              />
            </div>
          </div>
          <div
            class="col-xs-7"
            style="padding-right: 0;padding-left: 0"
          >
            <div class="input-group">
              <span
                class="input-group-addon nbr"
                style="width: 150px"
              >Код НСИ</span>
              <Treeselect
                v-model="currentNsiResearchCode"
                class="treeselect-nbr treeselect-wide"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="collectNsiResearchCode"
                placeholder="Код не выбран"
                :append-to-body="true"
                :clearable="false"
              />
            </div>
          </div>
        </div>
        <div class="row">
          <div
            :class="expertise ? 'col-xs-5' : 'col-xs-6'"
            style="padding-right: 0"
          >
            <div
              v-if="direction_params_all.length > 1"
              class="input-group"
            >
              <span
                class="input-group-addon nbr"
                style="width: 232px"
              >Параметры направления</span>
              <Treeselect
                v-model="direction_current_params"
                class="treeselect-noborder treeselect-wide"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="direction_params_all"
                placeholder="Параметры не выбраны"
                :append-to-body="true"
                :clearable="false"
              />
            </div>
          </div>
          <div
            v-if="expertise && direction_expertise_all.length > 0"
            class="col-xs-3"
            style="padding-right: 0;padding-left: 0"
          >
            <div class="input-group">
              <span
                class="input-group-addon nbr"
                style="width: 150px"
              >Экспертиза</span>
              <Treeselect
                v-model="direction_current_expertise"
                class="treeselect-noborder treeselect-wide"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="direction_expertise_all"
                placeholder="Экспертиза не выбрана"
                :append-to-body="true"
                :clearable="false"
              />
            </div>
          </div>
          <div
            class="expertise ? 'col-xs-4' : 'col-xs-6'"
            style="padding-left: 0"
          >
            <div
              v-if="ex_dep !== 14"
              class="input-group"
            >
              <span class="input-group-addon nbr"> Ф.результатов </span>
              <select
                v-model="result_current_form"
                class="form-control nbr"
              >
                <option
                  v-for="d in result_forms"
                  :key="d[0]"
                  :value="d[0]"
                >
                  {{ d[1] }}
                </option>
              </select>
              <span
                v-if="is_paraclinic"
                class="input-group-btn"
              >
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  style="border-radius: 0;"
                  :disabled="loaded_pk < 0"
                  @click="open_localization()"
                >
                  Локализация
                </button>
              </span>
            </div>
            <div
              v-else
              class="input-group"
            >
              <span class="input-group-addon nbr"> Период мониторинга </span>
              <Treeselect
                v-model="type_period"
                class="treeselect-noborder treeselect-wide"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="period_types"
                placeholder="Период не выбран"
                :append-to-body="true"
                :clearable="true"
              />
            </div>
          </div>
        </div>
      </template>
      <div
        v-if="ex_dep === 7"
        class="department-select"
      >
        <Treeselect
          v-model="hospital_research_department_pk"
          :multiple="false"
          :disable-branch-nodes="true"
          :options="departments"
          placeholder="Отделение не выбрано"
        />
        <div class="input-group">
          <span class="input-group-addon">Наименование для расписания</span>
          <input
            v-model="schedule_title"
            type="text"
            class="form-control"
          >
        </div>
      </div>
      <template v-if="ex_dep !== 7">
        <div
          v-for="(group, gi) in orderBy(groups, 'order')"
          :key="gi"
          class="ed-group"
        >
          <div
            v-if="ex_dep !== 12 && ex_dep !== 13"
            class="input-group treeselect-input-group-simple"
          >
            <span class="input-group-btn">
              <button
                class="btn btn-blue-nb lob"
                :disabled="is_first_group(group)"
                @click="dec_group_order(group)"
              >
                <i class="glyphicon glyphicon-arrow-up" />
              </button>
            </span>
            <span class="input-group-btn">
              <button
                class="btn btn-blue-nb nob"
                :disabled="is_last_group(group)"
                @click="inc_group_order(group)"
              >
                <i class="glyphicon glyphicon-arrow-down" />
              </button>
            </span>
            <span class="input-group-addon">Название группы ({{ group.pk === -1 ? 'новое' : group.pk }})</span>
            <input
              v-model="group.title"
              type="text"
              class="form-control"
              placeholder="Название"
            >
            <span class="input-group-addon">Условие видимости</span>
            <input
              v-model="group.visibility"
              type="text"
              class="form-control"
              placeholder="Условие"
            >
            <span class="input-group-addon">CDA-отношение</span>
            <span class="input-group-btn">
              <Treeselect
                v-model="group.cdaOption"
                class="treeselect-wide treeselect-noborder-left"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="cda_options"
                placeholder="CDA-отношение"
                :append-to-body="true"
                :clearable="false"
              />
            </span>
          </div>
          <div
            v-if="ex_dep !== 12 && ex_dep !== 13"
            class="row"
          >
            <div class="col-xs-6">
              <label v-if="!group.hide">Отображать название <input
                v-model="group.show_title"
                type="checkbox"
              ></label>
              <label v-if="!group.hide"> Поля в одну строку<input
                v-model="group.fieldsInline"
                type="checkbox"
              ></label>
              <div v-else>
                <strong>Группа скрыта.</strong>
                <label><input
                  v-model="group.display_hidden"
                  type="checkbox"
                > отображать поля</label>
              </div>
            </div>
            <div class="col-xs-2 text-right" />
            <div class="col-xs-4 text-right">
              <a
                href="#"
                class="a-under"
                style="padding-right: 10px"
                @click.prevent="exportGroup(group.pk)"
              >Эскпорт группы</a>
              <label>Скрыть группу <input
                v-model="group.hide"
                type="checkbox"
              ></label>
            </div>
          </div>
          <template v-if="!group.hide || group.display_hidden">
            <div>
              <strong>Поля ввода</strong>
            </div>
            <div
              v-for="(row, ri) in orderBy(group.fields, 'order')"
              :key="ri"
              class="ed-field"
            >
              <div class="ed-field-inner">
                <div>
                  <button
                    class="btn btn-default btn-sm btn-block"
                    :disabled="is_first_field(group, row)"
                    @click="dec_order(group, row)"
                  >
                    <i class="glyphicon glyphicon-arrow-up" />
                  </button>
                  <button
                    class="btn btn-default btn-sm btn-block"
                    :disabled="is_last_field(group, row)"
                    @click="inc_order(group, row)"
                  >
                    <i class="glyphicon glyphicon-arrow-down" />
                  </button>
                </div>
                <div>
                  <div class="input-group">
                    <span class="input-group-addon">Название поля ({{ row.pk === -1 ? 'новое' : row.pk }})</span>
                    <input
                      v-model="row.title"
                      type="text"
                      class="form-control"
                    >
                    <span class="input-group-addon">Синоним</span>
                    <input
                      v-model="row.short_title"
                      type="text"
                      class="form-control"
                    >
                    <span class="input-group-addon">ID-скрепки</span>
                    <input
                      v-model="row.attached"
                      type="text"
                      class="form-control"
                    >
                  </div>
                  <div class="row">
                    <div class="col-xs-6">
                      <strong>Контролируемый параметр:</strong>
                      <Treeselect
                        v-model="row.patientControlParam"
                        class="treeselect treeselect-26px"
                        :multiple="false"
                        :disable-branch-nodes="true"
                        :options="patient_control_param_all"
                        placeholder="Контролируемый параметр"
                        :append-to-body="true"
                        :clearable="false"
                      />
                    </div>
                    <div class="col-xs-6">
                      <strong>CDA-отношение:</strong>
                      <Treeselect
                        v-model="row.cdaOption"
                        class="treeselect treeselect-26px"
                        :multiple="false"
                        :disable-branch-nodes="true"
                        :options="cda_options"
                        placeholder="CDA-отношение"
                        :append-to-body="true"
                        :clearable="false"
                      />
                    </div>
                  </div>
                  <div v-if="row.field_type === 0 || row.field_type === 29">
                    <strong>Значение по умолчанию:</strong>
                    <textarea
                      v-if="row.lines > 1"
                      v-model="row.default"
                      :rows="row.lines"
                      class="form-control"
                    />
                    <input
                      v-else
                      v-model="row.default"
                      class="form-control"
                    >
                  </div>
                  <div v-if="[1, 20].includes(row.field_type)">
                    <strong>Значение по умолчанию:</strong>
                    <input
                      v-model="row.default"
                      class="form-control"
                    >
                  </div>
                  <div v-else-if="row.field_type === 3">
                    <strong>Формула:</strong>
                    <input
                      v-model="row.default"
                      class="form-control"
                    >
                    <label>
                      <input
                        v-model="row.can_edit"
                        type="checkbox"
                      > можно редактировать
                    </label>
                  </div>
                  <div v-else-if="[2, 28, 32, 33, 34, 36].includes(row.field_type)">
                    <strong>Ссылка на поле (%):</strong>
                    <input
                      v-model="row.default"
                      class="form-control"
                    >
                  </div>
                  <div v-else-if="row.field_type === 30">
                    <strong>Тип номера:</strong>
                    <select
                      v-model="row.default"
                      class="form-control"
                    >
                      <option value="">
                        не выбрано
                      </option>
                      <option value="deathFormNumber">
                        Номер свидетельства о смерти
                      </option>
                    </select>
                  </div>
                  <div v-else-if="row.field_type === 37">
                    <strong>Тип номера:</strong>
                    <select
                      v-model="row.default"
                      class="form-control"
                    >
                      <option value="">
                        не выбрано
                      </option>
                      <option value="deathPerinatalNumber">
                        Номер перинатольного МСС
                      </option>
                    </select>
                  </div>
                  <div v-else-if="row.field_type === 11">
                    <strong>ID фракции:</strong>
                    <input
                      v-model="row.default"
                      class="form-control"
                    >
                  </div>
                  <div v-else-if="row.field_type === 13 || row.field_type === 14 || row.field_type === 23">
                    <strong>ID поля:</strong>
                    <input
                      v-model="row.default"
                      class="form-control"
                    >
                  </div>
                  <div v-else-if="row.field_type === 15">
                    <strong>Значение по умолчанию:</strong>
                    <RichTextEditor v-model="row.default" />
                  </div>
                  <div v-else-if="row.field_type === 18">
                    <strong>Значение по умолчанию:</strong>
                    <NumberField v-model="row.default" />
                  </div>
                  <div v-else-if="row.field_type === 19">
                    <strong>Значение по умолчанию:</strong>
                    <NumberRangeField
                      v-model="row.default"
                      :variants="row.values_to_input"
                    />
                  </div>
                  <div v-else-if="row.field_type === 21">
                    <ConfigureAnesthesiaField v-model="row.values_to_input" />
                  </div>
                  <div v-else-if="row.field_type === 24">
                    <strong>Результаты лабораторные:</strong>
                  </div>
                  <div v-else-if="row.field_type === 25">
                    <strong>Результаты диагностические:</strong>
                  </div>
                  <div v-else-if="row.field_type === 26">
                    <strong>Результаты консультационные:</strong>
                  </div>
                  <div v-else-if="row.field_type === 38">
                    <strong>Результаты процедурного листа:</strong>
                  </div>
                  <div v-else-if="row.field_type === 27">
                    <strong>Таблица:</strong>
                  </div>
                  <div v-else-if="row.field_type === 39">
                    <strong>Справочник:</strong>
                    <br>
                    <Treeselect
                      :value="row.values_to_input[0] || null"
                      class="treeselect-wide"
                      :multiple="false"
                      :disable-branch-nodes="true"
                      :options="dynamicDirectories"
                      placeholder="Справочник не выбран"
                      :append-to-body="true"
                      :clearable="true"
                      @input="e => e ? row.values_to_input = [e] : row.values_to_input = []"
                    />
                  </div>
                  <PermanentDirectories
                    v-if="row.field_type === 28"
                    :row="row"
                    :permanent_directories_keys="permanent_directories_keys"
                    :permanent_directories="permanent_directories"
                  />
                  <v-collapse-wrapper v-show="[0, 10, 12, 13, 14, 19, 22, 23, 27].includes(row.field_type)">
                    <div
                      v-collapse-toggle
                      class="header"
                    >
                      <a
                        v-if="row.field_type === 0"
                        href="#"
                        class="a-under"
                        @click.prevent
                      >
                        Шаблоны быстрого ввода (кол-во: {{ row.values_to_input.length }})
                      </a>
                      <a
                        v-else-if="row.field_type === 19"
                        href="#"
                        class="a-under"
                        @click.prevent
                      >
                        Мин, Макс, Шаг, Единицы измерения
                      </a>
                      <a
                        v-else-if="row.field_type === 27"
                        href="#"
                        class="a-under"
                        @click.prevent
                      >
                        Настройка таблицы
                      </a>
                      <a
                        v-else
                        href="#"
                        class="a-under"
                        @click.prevent
                      > Варианты (кол-во: {{ row.values_to_input.length }}) </a>
                    </div>
                    <div
                      v-collapse-content
                      class="my-content"
                    >
                      <TableConstructor
                        v-if="row.field_type === 27"
                        :row="row"
                      />
                      <template v-else>
                        <div
                          class="input-group"
                          style="margin-bottom: 5px"
                        >
                          <input
                            v-model="row.new_value"
                            type="text"
                            class="form-control"
                            placeholder="Новый шаблон быстрого ввода"
                            @keyup.enter="add_template_value(row)"
                          >
                          <span class="input-group-btn">
                            <button
                              class="btn last btn-blue-nb"
                              type="button"
                              :disabled="row.new_value === ''"
                              @click="add_template_value(row)"
                            >
                              Добавить
                            </button>
                          </span>
                        </div>
                        <div>
                          <div
                            v-for="(v, i) in row.values_to_input"
                            :key="i"
                            class="input-group"
                            style="margin-bottom: 1px"
                          >
                            <span class="input-group-btn">
                              <button
                                class="btn btn-blue-nb lob"
                                :disabled="is_first_in_template(i)"
                                @click="up_template(row, i)"
                              >
                                <i class="glyphicon glyphicon-arrow-up" />
                              </button>
                            </span>
                            <span class="input-group-btn">
                              <button
                                class="btn btn-blue-nb nob"
                                :disabled="is_last_in_template(row, i)"
                                @click="down_template(row, i)"
                              >
                                <i class="glyphicon glyphicon-arrow-down" />
                              </button>
                            </span>
                            <input
                              v-model="row.values_to_input[i]"
                              class="form-control"
                              type="text"
                            >
                            <span class="input-group-btn">
                              <button
                                class="btn btn-blue-nb"
                                @click="remove_template(row, i)"
                              >
                                <i class="glyphicon glyphicon-remove" />
                              </button>
                            </span>
                          </div>
                        </div>
                      </template>
                    </div>
                  </v-collapse-wrapper>
                  <FieldHelper
                    :field-type="row.field_type"
                    :value="row.default"
                    :groups="groups"
                  />
                </div>
                <div>
                  <strong>Подсказка:</strong>
                  <textarea
                    v-model="row.helper"
                    class="form-control"
                  />
                </div>
                <div>
                  <strong>Видимость:</strong>
                  <textarea
                    v-model="row.visibility"
                    class="form-control"
                  />
                </div>
                <div>
                  <strong>Контроль:</strong>
                  <textarea
                    v-model="row.controlParam"
                    class="form-control"
                  />
                </div>
                <div>
                  <label> <input
                    v-model="row.hide"
                    type="checkbox"
                  > скрыть поле </label>
                  <label> <input
                    v-model="row.required"
                    type="checkbox"
                  > запрет пустого </label>
                  <label> <input
                    v-model="row.for_talon"
                    type="checkbox"
                  > в талон </label>
                  <label> <input
                    v-model="row.for_extract_card"
                    type="checkbox"
                  > в выписку </label>
                  <label> <input
                    v-model="row.for_med_certificate"
                    type="checkbox"
                  > в справку </label>
                  <label> <input
                    v-model="row.operator_enter_param"
                    type="checkbox"
                  > оператор </label>
                  <label> <input
                    v-model="row.not_edit"
                    type="checkbox"
                  > только чтение </label>
                  <label v-show="row.field_type === 35">
                    <input
                      v-model="row.sign_organization"
                      type="checkbox"
                    > ЭЦП-МО
                  </label>
                  <label
                    v-show="row.field_type === 0 || row.field_type === 13 || row.field_type === 14 || row.field_type === 23"
                    style="line-height: 1"
                  >
                    Число строк:<br>
                    <input
                      v-model.number="row.lines"
                      class="form-control"
                      type="number"
                      min="1"
                    >
                  </label>
                  <label>
                    Тип поля:<br>
                    <select
                      v-model.number="row.field_type"
                      class="form-control"
                    >
                      <option value="0">Строка</option>
                      <option value="1">Дата</option>
                      <option value="2">Диагноз по МКБ (1.2.643.5.1.13.13.11.1005)</option>
                      <option value="32">МКБ-внешние причины заболеваемости и смертности(1.2.643.5.1.13.13.99.2.692)</option>
                      <option value="33">МКБ-Алфавитный (1.2.643.5.1.13.13.11.1489)</option>
                      <option value="34">МКБ-обычный (1.2.643.5.1.13.13.11.1005)</option>
                      <option value="36">МКБ-Комбинация (1489, 692)</option>
                      <option value="3">Расчётное</option>
                      <option value="10">Справочник</option>
                      <option value="11">Фракция</option>
                      <option value="12">Радио</option>
                      <option value="13">Поле описательного результата</option>
                      <option value="14">Поле описательного результата без заголовка</option>
                      <option
                        v-if="rich_text_enabled || row.field_type === 15"
                        value="15"
                      >Текст с форматированием</option>
                      <option value="16">(Стационар) агрегация по лаборатории</option>
                      <option value="17">(Стационар) агрегация по описательным</option>
                      <option value="18">Число</option>
                      <option value="19">Число через range</option>
                      <option value="20">Время ЧЧ:ММ</option>
                      <option value="21">Течение анестезии (таблица)</option>
                      <option value="22">Текст с автозаполнением</option>
                      <option value="23">Ссылка без автозагрузки</option>
                      <option value="24">Результаты лабораторные</option>
                      <option value="25">Результаты диагностические</option>
                      <option value="26">Результаты консультаций</option>
                      <option value="38">Результаты процедурного листа</option>
                      <option value="27">Таблица</option>
                      <option value="40">Реляционная таблица</option>
                      <option value="28">НСИ-справочник</option>
                      <option value="29">Адрес по ФИАС</option>
                      <option
                        v-if="number_generator_field_enabled"
                        value="30"
                      >Генератор номера документа</option>
                      <option
                        v-if="number_generator_field_enabled"
                        value="37"
                      >Генератор номера перинатального МСС св-ва</option>
                      <option
                        v-if="tfoms_attachment_field_enabled"
                        value="31"
                      >
                        Сведения о прикреплении застрахованного лица (ТФОМС)
                      </option>
                      <option value="35">Врач</option>
                      <option value="39">Динамический справочник</option>
                    </select>
                  </label>
                </div>
              </div>
            </div>
            <div>
              <button
                class="btn btn-blue-nb"
                @click="add_field(group)"
              >
                Добавить поле
              </button>
            </div>
          </template>
        </div>
        <div
          v-if="ex_dep !== 12 && ex_dep !== 13"
          class="add-buttons"
        >
          <button
            class="btn btn-blue-nb"
            @click="add_group()"
          >
            Добавить группу
          </button>
          <LoadFile
            is-load-group-for-protocol
            title-button="Загрузить из файла"
            file-filter="application/JSON"
            :research-id="pk"
            tag="div"
            @load-file="onLoadFileGroup"
          />
        </div>
      </template>
      <div v-if="ex_dep === 12 && pk > -1">
        <div><strong>Назначения, где используется этот шаблон параметров:</strong></div>
        <ul>
          <li
            v-for="a in assigned_to_params"
            :key="a"
          >
            {{ a }}
          </li>
          <li v-if="assigned_to_params.length === 0">
            не найдено
          </li>
        </ul>
      </div>
    </div>
    <div class="footer-editor">
      <button
        class="btn btn-blue-nb"
        @click="cancel"
      >
        Отмена
      </button>
      <button
        class="btn btn-blue-nb"
        :disabled="!valid"
        @click="save"
      >
        Сохранить
      </button>
    </div>
    <FastTemplatesEditor
      v-if="f_templates_open"
      :title="title"
      :research_pk="loaded_pk"
      :groups="groups"
    />
    <Localizations
      v-if="show_localization"
      :title="title"
      :research_pk="loaded_pk"
      @hide="hide_localization"
    />
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Vue2Filters from 'vue2-filters';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import constructPoint from '@/api/construct-point';
import * as actions from '@/store/action-types';
import NumberRangeField from '@/fields/NumberRangeField.vue';
import ConfigureAnesthesiaField from '@/fields/ConfigureAnesthesiaField.vue';
import NumberField from '@/fields/NumberField.vue';
import FieldHelper from '@/ui-cards/FieldHelper.vue';
import Localizations from '@/construct/Localizations.vue';
import PermanentDirectories from '@/construct/PermanentDirectories.vue';
import LoadFile from '@/ui-cards/LoadFile.vue';

import FastTemplatesEditor from './FastTemplatesEditor.vue';

Vue.use(Vue2Filters);

export default {
  name: 'ParaclinicResearchEditor',
  components: {
    LoadFile,
    PermanentDirectories,
    FieldHelper,
    NumberRangeField,
    NumberField,
    RichTextEditor: () => import('@/fields/RichTextEditor.vue'),
    TableConstructor: () => import('@/construct/TableConstructor.vue'),
    FastTemplatesEditor,
    ConfigureAnesthesiaField,
    Treeselect,
    Localizations,
  },
  mixins: [Vue2Filters.mixin],
  props: {
    pk: {
      type: Number,
      required: true,
    },
    department: {
      type: Number,
      required: true,
    },
    simple: {
      type: Boolean,
      required: false,
      default: false,
    },
    main_service_pk: {
      type: Number,
      required: false,
      default: -1,
    },
    hs_pk: {
      type: Number,
      required: false,
      default: -1,
    },
    hide_main: {
      type: Boolean,
      required: false,
      default: false,
    },
    direction_forms: {
      type: Array,
      required: false,
      default: () => [],
    },
    result_forms: {
      type: Array,
      required: false,
      default: () => [],
    },
    specialities: {
      type: Array,
      required: false,
      default: () => [],
    },
    permanent_directories: {
      type: Object,
      required: false,
      default: () => ({}),
    },
    period_types: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  data() {
    return {
      title: '',
      schedule_title: '',
      short_title: '',
      is_global_direction_params: false,
      code: '',
      internal_code: '',
      uet_refferal_doc: '',
      uet_refferal_co_executor_1: '',
      direction_current_form: 0,
      result_current_form: 0,
      info: '',
      hide: false,
      cancel_do: false,
      loaded_pk: -2,
      site_type: null,
      groups: [],
      template_add_types: [
        { sep: ' ', title: 'Пробел' },
        { sep: ', ', title: 'Запятая и пробел' },
        { sep: '; ', title: 'Точка с запятой (;) и пробел' },
        { sep: '. ', title: 'Точка и пробел' },
        { sep: '\n', title: 'Перенос строки' },
      ],
      has_unsaved: false,
      f_templates_open: false,
      show_more_services: true,
      is_paraclinic: false,
      show_localization: false,
      templates: [],
      opened_template_data: {},
      speciality: -1,
      departments: [],
      hospital_research_department_pk: -1,
      direction_params_all: [],
      patient_control_param_all: [],
      direction_current_params: -1,
      direction_expertise_all: [],
      direction_current_expertise: -1,
      currentNsiResearchCode: -1,
      collectNsiResearchCode: [],
      collectMethods: [],
      currentMethod: -1,
      assigned_to_params: [],
      type_period: null,
      cda_options: [],
      dynamicDirectories: [],
      autoRegisterRmisLocation: '',
    };
  },
  computed: {
    permanent_directories_keys() {
      return [
        { id: -1, label: 'не выбран' },
        ...Object.keys(this.permanent_directories).map(oid => ({ id: oid, label: this.permanent_directories[oid].title })),
      ];
    },
    fte() {
      return this.$store.getters.modules.l2_fast_templates;
    },
    valid() {
      return this.norm_title.length > 0 && !this.cancel_do && (!this.simple || this.main_service_pk !== -1);
    },
    norm_title() {
      return this.title.trim();
    },
    min_max_order_groups() {
      let min = 0;
      let max = 0;
      for (const row of this.groups) {
        if (min === 0) {
          min = row.order;
        } else {
          min = Math.min(min, row.order);
        }
        max = Math.max(max, row.order);
      }
      return { min, max };
    },
    ex_dep() {
      return (
        {
          '-2': 4,
          '-3': 5,
          '-4': 6,
          '-5': 7,
          '-6': 8,
          '-9': 11,
          '-10': 12,
          '-11': 13,
          '-12': 14,
          '-13': 15,
          '-14': 16,
        }[this.department] || this.department
      );
    },
    ex_deps() {
      return this.$store.getters.ex_dep[this.ex_dep] || [];
    },
    rich_text_enabled() {
      return this.$store.getters.modules.descriptive_rich_text;
    },
    number_generator_field_enabled() {
      return this.$store.getters.modules.number_generator_field;
    },
    tfoms_attachment_field_enabled() {
      return this.$store.getters.modules.tfoms_attachment_field;
    },
    expertise() {
      return this.$store.getters.modules.l2_expertise;
    },
  },
  watch: {
    pk() {
      this.load();
    },
    loaded_pk() {
      this.has_unsaved = false;
    },
    groups: {
      handler(n, o) {
        if (o && o.length > 0) {
          this.has_unsaved = true;
        }
      },
      deep: true,
    },
    currentMethod: {
      handler() {
        this.loadcollectNsiCode();
      },
      deep: true,
    },
  },
  created() {
    this.load();
    this.load_deparments();
    this.loadDynamicDirectories();
  },
  mounted() {
    window.$(window).on('beforeunload', () => {
      if (this.has_unsaved && this.loaded_pk > -2 && !this.cancel_do) {
        return 'Изменения, возможно, не сохранены. Вы уверены, что хотите покинуть страницу?';
      }
      return undefined;
    });
    this.$root.$on('hide_fte', () => this.f_templates_hide());
    setTimeout(() => {
      this.has_unsaved = false;
    }, 300);
    setTimeout(() => {
      this.has_unsaved = false;
    }, 1000);
    setTimeout(() => {
      this.has_unsaved = false;
    }, 2000);
  },
  methods: {
    onLoadFileGroup(importData) {
      try {
        const { groups: [group] } = JSON.parse(importData);

        if (!group.fields) {
          throw Error('В файле не найдены поля ввода');
        }

        this.add_group(group);
        this.$ok(`Группа "${group.title}" успешно загружена`);
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.$error('Некорректный файл');
      }
    },
    exportGroup(groupId) {
      window.open(`/api/researches/group-as-json?groupId=${groupId}`, 'group-export');
    },
    open_localization() {
      this.show_localization = true;
    },
    hide_localization() {
      this.show_localization = false;
    },
    f_templates() {
      this.f_templates_open = true;
    },
    f_templates_hide() {
      this.f_templates_open = false;
    },
    is_first_in_template(i) {
      return i === 0;
    },
    is_last_in_template(row, i) {
      return i === row.values_to_input.length - 1;
    },
    up_template(row, i) {
      if (this.is_first_in_template(i)) return;
      const values = JSON.parse(JSON.stringify(row.values_to_input));
      [values[i - 1], values[i]] = [values[i], values[i - 1]];
      // eslint-disable-next-line no-param-reassign
      row.values_to_input = values;
    },
    down_template(row, i) {
      if (this.is_last_in_template(row, i)) return;
      const values = JSON.parse(JSON.stringify(row.values_to_input));
      [values[i + 1], values[i]] = [values[i], values[i + 1]];
      // eslint-disable-next-line no-param-reassign
      row.values_to_input = values;
    },
    remove_template(row, i) {
      if (row.values_to_input.length - 1 < i) return;
      row.values_to_input.splice(i, 1);
    },
    add_template_value(row) {
      if (row.new_value === '') return;
      row.values_to_input.push(row.new_value);
      // eslint-disable-next-line no-param-reassign
      row.new_value = '';
    },
    drag() {
      // console.log(row, ev)
    },
    min_max_order(group) {
      let min = 0;
      let max = 0;
      for (const row of group.fields) {
        if (min === 0) {
          min = row.order;
        } else {
          min = Math.min(min, row.order);
        }
        max = Math.max(max, row.order);
      }
      return { min, max };
    },
    inc_group_order(row) {
      if (row.order === this.min_max_order_groups.max) return;
      const nextRow = this.find_group_by_order(row.order + 1);
      if (nextRow) {
        nextRow.order--;
      }
      // eslint-disable-next-line no-param-reassign
      row.order++;
    },
    dec_group_order(row) {
      if (row.order === this.min_max_order_groups.min) return;
      const prevRow = this.find_group_by_order(row.order - 1);
      if (prevRow) {
        prevRow.order++;
      }
      // eslint-disable-next-line no-param-reassign
      row.order--;
    },
    inc_order(group, row) {
      if (row.order === this.min_max_order(group).max) return;
      const nextRow = this.find_by_order(group, row.order + 1);
      if (nextRow) {
        nextRow.order--;
      }
      // eslint-disable-next-line no-param-reassign
      row.order++;
    },
    dec_order(group, row) {
      if (row.order === this.min_max_order(group).min) return;
      const prevRow = this.find_by_order(group, row.order - 1);
      if (prevRow) {
        prevRow.order++;
      }
      // eslint-disable-next-line no-param-reassign
      row.order--;
    },
    find_by_order(group, order) {
      for (const row of group.fields) {
        if (row.order === order) {
          return row;
        }
      }
      return false;
    },
    find_group_by_order(order) {
      for (const row of this.groups) {
        if (row.order === order) {
          return row;
        }
      }
      return false;
    },
    is_first_group(group) {
      return group.order === this.min_max_order_groups.min;
    },
    is_last_group(group) {
      return group.order === this.min_max_order_groups.max;
    },
    is_first_field(group, row) {
      return row.order === this.min_max_order(group).min;
    },
    is_last_field(group, row) {
      return row.order === this.min_max_order(group).max;
    },
    add_field(group, field: any = {}, ignoreOrder = false) {
      let order = ignoreOrder ? field.order ?? null : 0;

      if (!ignoreOrder || order === null) {
        order = 0;

        for (const row of group.fields) {
          order = Math.max(order, row.order);
        }
      }

      let parsedValuesToInput = [];

      if (field.input_templates && typeof field.input_templates === 'string') {
        try {
          parsedValuesToInput = JSON.parse(field.input_templates);

          if (!Array.isArray(parsedValuesToInput)) {
            parsedValuesToInput = [];
          }
        } catch (error) {
        // eslint-disable-next-line no-console
          console.error(error);
        }
      }

      group.fields.push({
        pk: -1,
        order: ignoreOrder ? order : order + 1,
        title: field.title ?? '',
        short_title: field.short_title ?? '',
        default: field.default_value ?? '',
        helper: field.helper ?? '',
        values_to_input: parsedValuesToInput,
        new_value: '',
        hide: field.hide ?? false,
        lines: field.lines ?? 3,
        field_type: field.field_type ?? 0,
        can_edit: field.can_edit ?? false,
        for_extract_card: field.for_extract_card ?? false,
        for_talon: field.for_talon ?? false,
        for_med_certificate: field.for_med_certificate ?? false,
        operator_enter_param: field.operator_enter_param ?? false,
        not_edit: field.not_edit ?? false,
        required: field.required ?? false,
        visibility: field.visibility ?? '',
        sign_organization: field.sign_organization ?? false,
        controlParam: field.controlParam ?? '',
        attached: field.attached ?? '',
        patientControlParam: field.patientControlParam ?? -1,
        cdaOption: field.cdaOption ?? -1,
      });
    },
    add_group(groupSettings: any = {}) {
      let order = 0;
      for (const row of this.groups) {
        order = Math.max(order, row.order);
      }
      const g = {
        pk: -1,
        order: order + 1,
        title: groupSettings.title ?? '',
        fields: [],
        show_title: groupSettings.show_title ?? true,
        hide: groupSettings.hide ?? false,
        fieldsInline: groupSettings.fieldsInline ?? false,
        cdaOption: groupSettings.cdaOption ?? -1,
        display_hidden: groupSettings.display_hidden ?? false,
        visibility: groupSettings.visibility ?? '',
      };
      if (groupSettings.fields) {
        for (const currentField of groupSettings.fields) {
          this.add_field(g, currentField, true);
        }
      } else {
        this.add_field(g);
      }
      this.groups.push(g);
    },
    load() {
      this.title = '';
      this.short_title = '';
      this.autoRegisterRmisLocation = '';
      this.schedule_title = '';
      this.is_global_direction_params = false;
      this.code = '';
      this.info = '';
      this.hide = false;
      this.site_type = null;
      this.groups = [];
      this.direction_current_form = '';
      this.result_current_form = '';
      this.speciality = -1;
      this.currentMethod = -1;
      this.collectMethods = [];
      this.hospital_research_department_pk = -1;
      this.type_period = null;
      if (this.pk >= 0) {
        this.$store.dispatch(actions.INC_LOADING);
        constructPoint
          .researchDetails(this, 'pk')
          .then(data => {
            this.title = data.title;
            this.short_title = data.short_title;
            this.autoRegisterRmisLocation = data.autoRegisterRmisLocation;
            this.schedule_title = data.schedule_title;
            this.is_global_direction_params = data.is_global_direction_params;
            this.code = data.code;
            this.internal_code = data.internal_code;
            this.uet_refferal_doc = data.uet_refferal_doc;
            this.uet_refferal_co_executor_1 = data.uet_refferal_co_executor_1;
            this.direction_current_form = data.direction_current_form;
            this.result_current_form = data.result_current_form;
            this.currentNsiResearchCode = data.currentNsiResearchCode;
            this.collectNsiResearchCode = data.collectNsiResearchCode;
            this.collectMethods = data.collectMethods;
            this.speciality = data.speciality;
            this.hospital_research_department_pk = data.department;
            this.info = data.info.replace(/<br\/>/g, '\n').replace(/<br>/g, '\n');
            this.hide = data.hide;
            this.site_type = data.site_type;
            this.loaded_pk = this.pk;
            this.groups = data.groups;
            this.direction_params_all = data.direction_params_all;
            this.patient_control_param_all = data.patient_control_param_all;
            this.cda_options = data.cda_options;
            this.direction_current_params = data.direction_current_params;
            this.direction_expertise_all = data.direction_expertise_all;
            this.direction_current_expertise = data.direction_current_expertise;
            this.assigned_to_params = data.assigned_to_params;
            this.show_more_services = data.show_more_services;
            this.is_paraclinic = data.is_paraclinic;
            this.type_period = data.type_period;
            if (this.groups.length === 0) {
              this.add_group();
            }
          })
          .finally(() => {
            this.$store.dispatch(actions.DEC_LOADING);
          });
      } else {
        this.add_group();
      }
      if (this.ex_deps.length > 0 && this.site_type === null) {
        this.site_type = this.ex_deps[0].pk;
      }
    },
    cancel() {
      // eslint-disable-next-line no-restricted-globals,no-alert
      if (this.has_unsaved && !confirm('Изменения, возможно, не сохранены. Вы уверены, что хотите отменить редактирование?')) {
        return;
      }
      this.cancel_do = true;
      this.$root.$emit('research-editor:cancel');
    },
    save() {
      this.$store.dispatch(actions.INC_LOADING);
      const props = [
        'pk',
        'department',
        'title',
        'short_title',
        'autoRegisterRmisLocation',
        'schedule_title',
        'is_global_direction_params',
        'code',
        'hide',
        'groups',
        'site_type',
        'internal_code',
        'uet_refferal_doc',
        'uet_refferal_co_executor_1',
        'direction_current_form',
        'result_current_form',
        'speciality',
        'hospital_research_department_pk',
        'direction_current_params',
        'direction_current_expertise',
        'show_more_services',
        'type_period',
        'not_edit',
        'operator_enter_param',
        'currentNsiResearchCode',
      ];
      const moreData = {
        info: this.info.replace(/\n/g, '<br/>').replace(/<br>/g, '<br/>'),
        simple: this.simple,
      };
      if (this.simple) {
        props.push('main_service_pk', 'hide_main', 'hs_pk');
      }
      constructPoint
        .updateResearch(this, props, moreData)
        .then(() => {
          this.has_unsaved = false;
          this.$root.$emit('msg', 'ok', 'Сохранено');
          this.cancel();
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
    },
    async load_deparments() {
      const { data } = await this.$api('procedural-list/suitable-departments');
      this.departments = [{ id: -1, label: 'Отделение не выбрано' }, ...data];
    },
    async loadDynamicDirectories() {
      const { rows } = await this.$api('dynamic-directory/list-treeselect');
      this.dynamicDirectories = rows;
    },
    async loadcollectNsiCode() {
      const { rows } = await this.$api('external-system/fsidi-by-method', { method: this.currentMethod });
      this.collectNsiResearchCode = rows;
    },
  },
};
</script>

<style scoped lang="scss">
.modal-mask {
  align-items: stretch !important;
  justify-content: stretch !important;
}

::v-deep .panel-flt:not(.ignore-body) {
  margin: 41px;
  align-self: stretch !important;
  width: 100%;
  display: flex;
  flex-direction: column;
}

::v-deep .panel-body:not(.ignore-body) {
  flex: 1;
  padding: 0;
  height: calc(100% - 91px);
  min-height: 200px;
}

.top-editor {
  display: flex;
  flex: 0 0 68px;

  &.oneLine {
    flex: 0 0 34px;
  }

  .left {
    flex: 0 0 45%;
  }

  .right {
    flex: 0 0 55%;
  }

  &.simpleEditor,
  &.formEditor {
    flex: 0 0 34px;

    .left {
      flex: 0 0 100%;
    }

    .right {
      display: none;
    }
  }

  .left {
    border-right: 1px solid #96a0ad;
  }

  .input-group-addon {
    border-top: none;
    border-left: none;
    border-right: none;
    border-radius: 0;
  }

  .form-control {
    border-top: none;
    border-radius: 0;
  }

  .input-group > .form-control:last-child {
    border-right: none;
  }

  .f-code {
    padding: 6px;
  }
}

.content-editor {
  height: 100%;
}

.footer-editor {
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-end;
  background-color: #f4f4f4;

  .btn {
    border-radius: 0;
  }
}

.top-editor,
.content-editor,
.footer-editor {
  align-self: stretch;
}

.root {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  align-content: stretch;
}

.content-editor {
  padding: 5px;
  overflow-y: auto;
  overflow-x: hidden;
}

.ed-group {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  background: #f0f0f0;
}

.groupHidden:not(:hover) {
  opacity: 0.6;
}

.ed-field {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  background: #fff;
  color: #000;
}

.ed-field-inner {
  display: flex;
  flex-direction: row;
  align-items: stretch;
}

.ed-field-inner > div {
  align-self: stretch;

  textarea {
    resize: none;
  }

  &:nth-child(1) {
    flex: 0 0 35px;
    padding-right: 5px;
  }

  &:nth-child(2) {
    width: calc(100% - 530px);
  }

  &:nth-child(3),
  &:nth-child(4),
  &:nth-child(5),
  &:nth-child(6) {
    width: 140px;
    padding-left: 5px;
    padding-right: 5px;
    white-space: nowrap;

    label {
      display: block;
      margin-bottom: 2px;
      width: 100%;

      input[type='number'] {
        width: 100%;
      }
    }
  }

  &:nth-child(3),
  &:nth-child(4) {
    width: 180px;
  }
}

.lob {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.nob {
  border-radius: 0;
}

::v-deep .v-collapse-content-end {
  max-height: 10000px !important;
}

.vc-collapse ::v-deep .v-collapse-content {
  display: none;

  &.v-collapse-content-end {
    display: block;
  }
}

.department-select {
  margin-top: 5px;
}

.add-buttons {
  display: flex;
  flex-direction: row;
  gap: 10px;
}
</style>
