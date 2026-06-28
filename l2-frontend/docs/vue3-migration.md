# Миграция l2-frontend: Vue 2 → Composition API → Vue 3

> Автоматически сгенерировано: 2026-06-28. Всего компонентов: **357**.
> Путь относительно `l2-frontend/src/`.

## Сводка

| Фаза | Кол-во | Описание |
|------|-------:|----------|
| ✅ Готово | 88 | Уже на `<script setup lang="ts">`. Перед Vue 3 — проверить/обновить зависимости библиотек. |
| 🟢 Фаза 1 — простой перенос | 147 | Механический перенос Options API → `<script setup lang="ts">`. Без class components, filters, jQuery, mixins. < 400 строк. |
| 🟡 Фаза 1b — крупные файлы | 24 | Тот же механический перенос, но файл > 400 строк — больше объём работы. |
| 🟠 Фаза 2 — с рефакторингом | 43 | Перенос на Composition API + замена jQuery / vue2-typeahead / v-calendar / mixins / `new Vue()`. |
| 🔵 Фаза 3 — class components | 46 | Полная переписка с `vue-class-component` / `vue-property-decorator` на `<script setup lang="ts">`. |
| 🔴 Фаза 4 — блокеры Vue 3 | 9 | Сначала заменить Vue 2-only паттерн или библиотеку, затем Composition API. |

## Стратегия

1. **Фаза 1–1b** — механический перенос Options API на `<script setup lang="ts">` (171 компонент).
2. **Фаза 2** — перенос + рефакторинг jQuery/typeahead/mixins (43 компонента).
3. **Фаза 3** — переписать class components (46 компонентов).
4. **Фаза 4** — заменить Vue 2-only библиотеки, затем перенести (9 компонентов).
5. **Инфраструктура** — `main.ts`, `mainWithRouter.ts`, `registerVue.ts`, Vuex 3 → Pinia/Vuex 4, vue-router 3 → 4.

### Как переводить (Фаза 1 — простой перенос)

```vue
<!-- Было -->
<script lang="ts">
export default {
  props: { value: String },
  data() { return { local: '' }; },
  computed: { upper() { return this.local.toUpperCase(); } },
  methods: { save() { this.$emit('input', this.local); } },
};
</script>

<!-- Стало -->
<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{ value?: string }>();
const emit = defineEmits<{ (e: 'input', v: string): void }>();

const local = ref('');
const upper = computed(() => local.value.toUpperCase());
function save() { emit('input', local.value); }
</script>
```

**Замены при переносе:**

| Options API | Composition API |
|-------------|-----------------|
| `this.$store` | `useStore()` из `@/store` или composable |
| `this.$router` / `this.$route` | `useRouter()` / `useRoute()` |
| `this.$emit('x', v)` | `emit('x', v)` через `defineEmits` |
| `this.$refs.x` | `ref()` + template ref |
| `this.$api(...)` | `import api from '@/api'` |
| `mapState` / `mapGetters` | `computed(() => store.state.x)` |
| `mapActions` / `mapMutations` | `store.dispatch` / `store.commit` |
| Глобальные filters (`| formatDate`) | composable или `moment()` inline |
| `this.$dialog` | composable или `ui-cards/Modal.vue` |

---

## Инфраструктура (не компоненты)

| Файл | Проблема | Действие |
|------|----------|----------|
| `src/main.ts` | `new Vue({ el })` | `createApp()` |
| `src/mainWithRouter.ts` | `new Vue()` + vue-router 3 + vue-meta 2 | Vue 3 bootstrap + router 4 |
| `src/registerVue.ts` | `Vue.filter()`, `Vue.use()`, `Vue.prototype.$*`, portal-vue, vue-frag | plugins/composables/directives |
| `src/store/index.ts` | Vuex 3 | Pinia или Vuex 4 |
| `src/App.vue` | class component | `<script setup>` + router-view |

### npm-зависимости без Vue 3 аналога

| Пакет | Замена |
|-------|--------|
| `@braid/vue-formulate` | FormKit или свой UI |
| `portal-vue` | `<Teleport>` |
| `vue-frag` | не нужен в Vue 3 |
| `vue-meta` v2 | `@unhead/vue` |
| `vue2-filters` | composables |
| `vue2-collapse` | свой collapse |
| `vue2-timepicker` | vue3-timepicker |
| `vue2-typeahead` | свой autocomplete / `@vueuse/core` |
| `tiptap` v1 | `@tiptap/vue-3` |
| `vue-codeditor` | `@guolao/vue-monaco-editor` |
| `v-calendar` v2 | v-calendar v3 |
| `@riophae/vue-treeselect` | `@zanmato/vue3-treeselect` |
| `vue-tippy` v4 | `vue-tippy` v6 |
| `vue-toastification` v1 | v2 |
| `vuejs-dialog` | Modal / headless UI |
| `vuex` v3 | Pinia |
| `vue-router` v3 | v4 |

---

## ✅ Готово (88)

Уже на `<script setup lang="ts">`. Перед Vue 3 — проверить/обновить зависимости библиотек.

### `components/` (16)

| Файл | Строк | Заметки |
|------|------:|---------|
| `components/CardSearch.vue` | 373 | jQuery |
| `components/Collapse.vue` | 115 | — |
| `components/DataList.vue` | 100 | — |
| `components/EditFormList.vue` | 103 | — |
| `components/EditFormTable.vue` | 240 | — |
| `components/EditableList.vue` | 302 | — |
| `components/FetchComponent.vue` | 69 | — |
| `components/ModalForm.vue` | 373 | vue-formulate |
| `components/NavbarDropdownContent.vue` | 60 | — |
| `components/SelectedPatient.vue` | 77 | — |
| `components/SimpleSelectableList.vue` | 56 | — |
| `components/Spinner.vue` | 54 | — |
| `components/TippyBeds.vue` | 67 | — |
| `components/UploadFile.vue` | 341 | — |
| `components/VisibilityFieldWrapper.vue` | 35 | — |
| `components/VisibilityGroupWrapper.vue` | 20 | — |

### `construct/` (16)

| Файл | Строк | Заметки |
|------|------:|---------|
| `construct/ConstructComplexServices.vue` | 393 | — |
| `construct/ConstructEmployees.vue` | 158 | — |
| `construct/ConstructLaboratory.vue` | 265 | — |
| `construct/ConstructRelatedTube.vue` | 160 | — |
| `construct/ConstructTubes/ColorInput.vue` | 44 | — |
| `construct/ConstructTubes/ConstructTubes.vue` | 290 | — |
| `construct/ConstructTubes/InputColorString.vue` | 46 | — |
| `construct/FractionsGroup.vue` | 450 | — |
| `construct/LinkFieldModal.vue` | 203 | — |
| `construct/LinkLabAdd.vue` | 324 | — |
| `construct/ParaclinicResearchEditorComponents/FieldKinds/FileConstructField.vue` | 426 | — |
| `construct/ResearchDetail.vue` | 827 | — |
| `construct/ResearchPermissionsModal.vue` | 153 | — |
| `construct/ResearchesGroup.vue` | 235 | — |
| `construct/TableMutiselectEditor.vue` | 284 | — |
| `construct/TippyTreeselect.vue` | 76 | — |

### `fields/` (4)

| Файл | Строк | Заметки |
|------|------:|---------|
| `fields/AggregateAssignments.vue` | 269 | — |
| `fields/FormulateL2RadioField.vue` | 31 | — |
| `fields/FormulateObjectSelect.vue` | 163 | local filters |
| `fields/LinkToDocumentField.vue` | 396 | — |

### `forms/` (2)

| Файл | Строк | Заметки |
|------|------:|---------|
| `forms/Fields/FileResultField.vue` | 629 | — |
| `forms/Fields/ParagraphResultField.vue` | 289 | — |

### `layouts/` (4)

| Файл | Строк | Заметки |
|------|------:|---------|
| `layouts/ContentCenterLayout.vue` | 28 | — |
| `layouts/PageInnerLayout.vue` | 19 | — |
| `layouts/TopBottomLayout.vue` | 108 | — |
| `layouts/TwoSidedLayout.vue` | 56 | — |

### `modals/` (5)

| Файл | Строк | Заметки |
|------|------:|---------|
| `modals/LabResearchAdditional.vue` | 132 | — |
| `modals/MoveDirectionToCard.vue` | 191 | — |
| `modals/RelationTubeEdit.vue` | 62 | — |
| `modals/ScheduleModal.vue` | 73 | — |
| `modals/UploadFileModal.vue` | 124 | — |

### `pages/` (34)

| Файл | Строк | Заметки |
|------|------:|---------|
| `pages/Billing/index.vue` | 484 | — |
| `pages/CaseControl/Content/TopView.vue` | 209 | — |
| `pages/CaseControl/Content/index.vue` | 112 | — |
| `pages/CaseControl/Sidebar/AnamnesisView.vue` | 138 | — |
| `pages/CaseControl/Sidebar/SearchForm.vue` | 99 | — |
| `pages/CaseControl/Sidebar/index.vue` | 442 | — |
| `pages/CaseControl/index.vue` | 63 | — |
| `pages/DocumentManagement/DocumentManager.vue` | 41 | — |
| `pages/DocumentManagement/DocumentViewer.vue` | 26 | — |
| `pages/DocumentManagement/DocumentsExplorer.vue` | 203 | — |
| `pages/DocumentManagement/DocumentsFilters.vue` | 68 | — |
| `pages/Employees/Employees.vue` | 301 | — |
| `pages/HospitalizationBoard.vue` | 4814 | — |
| `pages/Logs.vue` | 640 | — |
| `pages/ManageChambers/components/VueTippyDiv.vue` | 46 | — |
| `pages/ManageChambers/index.vue` | 985 | — |
| `pages/Profiles.vue` | 1755 | — |
| `pages/RequestCreation/RequestFields.vue` | 536 | vue-formulate |
| `pages/RequestCreation/RequestHistory.vue` | 1465 | — |
| `pages/RequestCreation/RequestImageBinding.vue` | 1009 | — |
| `pages/RequestCreation/index.vue` | 231 | — |
| `pages/RequestsFill/RequestCard.vue` | 238 | — |
| `pages/RequestsFill/index.vue` | 1348 | — |
| `pages/RequestsJournal/index.vue` | 802 | — |
| `pages/TransferDocument/TransferCard.vue` | 305 | — |
| `pages/Turnovers/Turnovers.vue` | 178 | — |
| `pages/WorkingTime/DateCell.vue` | 439 | — |
| `pages/WorkingTime/FillingCell.vue` | 68 | — |
| `pages/WorkingTime/FioCell.vue` | 112 | — |
| `pages/WorkingTime/FioHeader.vue` | 27 | — |
| `pages/WorkingTime/PositionCell.vue` | 338 | — |
| `pages/WorkingTime/PositionHeader.vue` | 126 | — |
| `pages/WorkingTime/TemplateTable.vue` | 196 | — |
| `pages/WorkingTime/WorkingTime.vue` | 917 | — |

### `ui-cards/` (7)

| Файл | Строк | Заметки |
|------|------:|---------|
| `ui-cards/CashRegisters/ChequeModal.vue` | 543 | — |
| `ui-cards/CashRegisters/ShiftButton.vue` | 53 | — |
| `ui-cards/CashRegisters/ShiftModal.vue` | 286 | — |
| `ui-cards/Modal.vue` | 184 | — |
| `ui-cards/MoveHistoryDocs.vue` | 306 | — |
| `ui-cards/PatientCompactPicker.vue` | 982 | jQuery |
| `ui-cards/PharmacotherapyTemplate.vue` | 391 | — |

## 🟢 Фаза 1 — простой перенос (147)

Механический перенос Options API → `<script setup lang="ts">`. Без class components, filters, jQuery, mixins. < 400 строк.

### `construct/` (11)

| Файл | Строк | Заметки |
|------|------:|---------|
| `construct/ConstructControlParam.vue` | 307 | — |
| `construct/ConstructDispensaryPlan.vue` | 65 | — |
| `construct/ConstructDistrict.vue` | 349 | — |
| `construct/ConstructHarmfulFactor.vue` | 373 | — |
| `construct/ConstructRoutePerformService.vue` | 162 | — |
| `construct/ConstructTemplates.vue` | 255 | — |
| `construct/ConstuctResearchSets.vue` | 381 | — |
| `construct/Localizations.vue` | 168 | — |
| `construct/RegexFormatInput.vue` | 55 | — |
| `construct/StationarFormEditor.vue` | 174 | — |
| `construct/VueTippyTd.vue` | 46 | — |

### `fields/` (28)

| Файл | Строк | Заметки |
|------|------:|---------|
| `fields/AggregateDesc.vue` | 302 | — |
| `fields/AggregateTADP.vue` | 202 | — |
| `fields/ConfigureAnesthesiaField.vue` | 174 | — |
| `fields/ConfigureDispenseryResearch.vue` | 258 | — |
| `fields/DateFieldNav2.vue` | 152 | — |
| `fields/DateFieldWithNow.vue` | 99 | — |
| `fields/DateSelector.vue` | 133 | — |
| `fields/DiagnosticPreviousResults.vue` | 172 | — |
| `fields/DocReferralPreviousResults.vue` | 173 | — |
| `fields/DoctorProfileTreeselectField.vue` | 115 | — |
| `fields/FormulaField.vue` | 95 | — |
| `fields/KOEField.vue` | 150 | — |
| `fields/LaboratoryPicker.vue` | 68 | — |
| `fields/LaboratoryPreviousResults.vue` | 218 | — |
| `fields/MKBFieldTreeselect.vue` | 264 | — |
| `fields/NumberField.vue` | 53 | — |
| `fields/NumberRangeField.vue` | 110 | — |
| `fields/PharmacotherapyTime.vue` | 111 | — |
| `fields/ProcedureListResult.vue` | 164 | — |
| `fields/RadioField.vue` | 207 | — |
| `fields/RadioFieldById.vue` | 169 | — |
| `fields/SearchFieldValueField.vue` | 205 | — |
| `fields/SearchFractionValueField.vue` | 123 | — |
| `fields/SelectField.vue` | 62 | — |
| `fields/SelectFieldTitled.vue` | 75 | — |
| `fields/TextareaAutocomplete.vue` | 280 | — |
| `fields/TreeSelectField.vue` | 72 | — |
| `fields/TreeSelectMultiField.vue` | 86 | — |

### `forms/` (3)

| Файл | Строк | Заметки |
|------|------:|---------|
| `forms/DepartmentEditRow.vue` | 167 | — |
| `forms/FastTemplates.vue` | 79 | — |
| `forms/InputTemplates.vue` | 266 | — |

### `modals/` (11)

| Файл | Строк | Заметки |
|------|------:|---------|
| `modals/AmbulatoryData.vue` | 383 | — |
| `modals/BacteriaEditTitleGroup.vue` | 132 | — |
| `modals/DirectionsChangeParent.vue` | 233 | — |
| `modals/FastCreateAndFillBacteriaGroup.vue` | 168 | — |
| `modals/FileAddModal.vue` | 278 | — |
| `modals/FindPatient.vue` | 89 | — |
| `modals/PlanOperationEdit.vue` | 132 | — |
| `modals/ReportChartViewer.vue` | 49 | — |
| `modals/RmisSendDirections.vue` | 82 | — |
| `modals/StatisticsMessagePrintModal.vue` | 138 | — |
| `modals/SubGroupDepartment.vue` | 383 | — |

### `pages/` (37)

| Файл | Строк | Заметки |
|------|------:|---------|
| `pages/Cases.vue` | 159 | — |
| `pages/DepartmentsForm.vue` | 183 | — |
| `pages/DirectionHistory.vue` | 225 | — |
| `pages/DirectionsPrint.vue` | 190 | — |
| `pages/Directories/Directory.vue` | 192 | — |
| `pages/Directories/DirectoryRow.vue` | 59 | — |
| `pages/Directories/DirectoryRowEditor.vue` | 320 | — |
| `pages/Directories/DirectoryRows.vue` | 154 | — |
| `pages/Directories/index.vue` | 209 | — |
| `pages/DocCallLog.vue` | 345 | — |
| `pages/DocCallModal.vue` | 229 | — |
| `pages/DocCallRow.vue` | 218 | — |
| `pages/EmployeeJobs.vue` | 380 | — |
| `pages/IndicatorCuratorRow.vue` | 140 | — |
| `pages/L2queue.vue` | 34 | — |
| `pages/LaboratoryResults/BloodTypeField.vue` | 70 | — |
| `pages/LaboratoryResults/Ref.vue` | 130 | — |
| `pages/LaboratoryResults/RefEditor.vue` | 153 | — |
| `pages/LaboratoryResults/RefSettings.vue` | 85 | — |
| `pages/LaboratoryResults/RefSettingsRow.vue` | 74 | — |
| `pages/LaboratoryResults/index.vue` | 89 | — |
| `pages/ListWait.vue` | 101 | — |
| `pages/ManageAnalyzers/components/Row.vue` | 145 | — |
| `pages/ManageAnalyzers/index.vue` | 63 | — |
| `pages/MonitoringsEnter.vue` | 367 | — |
| `pages/PlanHospitalization/components/MessagesData.vue` | 223 | — |
| `pages/PlanHospitalization/components/Row.vue` | 147 | — |
| `pages/PlanOperations/components/Row.vue` | 155 | — |
| `pages/ReceiveJournal.vue` | 232 | — |
| `pages/Stationar/DisplayDirection.vue` | 156 | — |
| `pages/Stationar/Favorite.vue` | 81 | — |
| `pages/Stationar/LinkPlanOperations.vue` | 27 | — |
| `pages/Stationar/LinkToHistory.vue` | 27 | — |
| `pages/Stationar/PatientCard.vue` | 20 | — |
| `pages/StatisticsReport/Charts.vue` | 215 | — |
| `pages/Ui404.vue` | 35 | — |
| `pages/Utils.vue` | 129 | — |

### `ui-cards/` (57)

| Файл | Строк | Заметки |
|------|------:|---------|
| `ui-cards/AuxResearch.vue` | 169 | — |
| `ui-cards/Card.vue` | 14 | — |
| `ui-cards/CardReader.vue` | 114 | — |
| `ui-cards/CategoryPick.vue` | 32 | — |
| `ui-cards/Chat/ChatDepartment.vue` | 215 | — |
| `ui-cards/Chat/ChatMessage.vue` | 353 | — |
| `ui-cards/Chat/ChatToast.vue` | 106 | — |
| `ui-cards/Chat/ChatUser.vue` | 202 | — |
| `ui-cards/Chat/ChatsBody.vue` | 265 | — |
| `ui-cards/Chat/ChatsDialogs.vue` | 24 | — |
| `ui-cards/ChatsButton.vue` | 122 | — |
| `ui-cards/ColorTitled.vue` | 33 | — |
| `ui-cards/CreateDescriptiveDirection.vue` | 205 | — |
| `ui-cards/DirectAndPlanSwitcher.vue` | 79 | — |
| `ui-cards/DisplayDateTime.vue` | 25 | — |
| `ui-cards/EDSDirection.vue` | 175 | — |
| `ui-cards/EDSDocument.vue` | 393 | — |
| `ui-cards/EDSSignTitle.vue` | 59 | — |
| `ui-cards/EDSSigner.vue` | 328 | — |
| `ui-cards/EcpSchedule.vue` | 235 | — |
| `ui-cards/ExecutionList.vue` | 138 | — |
| `ui-cards/ExpertiseStatus.vue` | 303 | — |
| `ui-cards/Favorites.vue` | 131 | — |
| `ui-cards/FieldHelper.vue` | 236 | — |
| `ui-cards/FileAdd.vue` | 77 | — |
| `ui-cards/HelpLinkField.vue` | 84 | — |
| `ui-cards/HospPlanCancelButton.vue` | 105 | — |
| `ui-cards/HospPlanScheduleButton.vue` | 123 | — |
| `ui-cards/IssStatus.vue` | 73 | — |
| `ui-cards/LPress.vue` | 30 | — |
| `ui-cards/LaboratoryHeader.vue` | 89 | — |
| `ui-cards/LaboratoryJournal.vue` | 255 | — |
| `ui-cards/LaboratoryPrintResults.vue` | 180 | — |
| `ui-cards/LaboratorySelector.vue` | 143 | — |
| `ui-cards/MedicalCertificates.vue` | 105 | — |
| `ui-cards/OperationPlans.vue` | 223 | — |
| `ui-cards/Patient.vue` | 17 | — |
| `ui-cards/PatientCard.vue` | 17 | — |
| `ui-cards/PatientResults/ResultDetails.vue` | 145 | — |
| `ui-cards/PatientResults/ResultsByYear.vue` | 280 | — |
| `ui-cards/PharmacotherapyInput.vue` | 272 | — |
| `ui-cards/PharmacotherapyRow.vue` | 252 | — |
| `ui-cards/PrintQueue.vue` | 220 | — |
| `ui-cards/ReportSelectedResearches.vue` | 226 | — |
| `ui-cards/ResearchDisplay.vue` | 235 | — |
| `ui-cards/ResearchParamsSelect.vue` | 264 | — |
| `ui-cards/ResearchPick.vue` | 78 | — |
| `ui-cards/ResearchesOptions.vue` | 37 | — |
| `ui-cards/ResultsReportViewer.vue` | 330 | — |
| `ui-cards/RmisLink.vue` | 64 | — |
| `ui-cards/RmisLocation.vue` | 50 | — |
| `ui-cards/RmisLocationFull.vue` | 47 | — |
| `ui-cards/ScreeningButton.vue` | 172 | — |
| `ui-cards/SelectedResearchesParams.vue` | 68 | — |
| `ui-cards/ServiceSchedule.vue` | 301 | — |
| `ui-cards/Statement/StatementModal.vue` | 320 | — |
| `ui-cards/StatisticsTicketsViewer.vue` | 291 | — |

## 🟡 Фаза 1b — крупные файлы (24)

Тот же механический перенос, но файл > 400 строк — больше объём работы.

### `components/` (1)

| Файл | Строк | Заметки |
|------|------:|---------|
| `components/PlanOperationsData.vue` | 417 | — |

### `construct/` (4)

| Файл | Строк | Заметки |
|------|------:|---------|
| `construct/ConstructBacteria.vue` | 594 | — |
| `construct/ConstructParaclinic.vue` | 421 | — |
| `construct/ConstructPrice.vue` | 881 | — |
| `construct/FastTemplatesEditor.vue` | 920 | — |

### `fields/` (2)

| Файл | Строк | Заметки |
|------|------:|---------|
| `fields/AggregateLaboratory.vue` | 438 | — |
| `fields/TableField.vue` | 599 | — |

### `forms/` (2)

| Файл | Строк | Заметки |
|------|------:|---------|
| `forms/BacMicroForm.vue` | 697 | — |
| `forms/DescriptiveForm.vue` | 776 | — |

### `modals/` (6)

| Файл | Строк | Заметки |
|------|------:|---------|
| `modals/Benefit.vue` | 478 | — |
| `modals/DReg.vue` | 1029 | — |
| `modals/HarmfulFactor.vue` | 430 | — |
| `modals/ResultsViewer.vue` | 415 | — |
| `modals/RmisDirectionsViewer.vue` | 551 | — |
| `modals/Vaccine.vue` | 523 | — |

### `pages/` (3)

| Файл | Строк | Заметки |
|------|------:|---------|
| `pages/DocCall.vue` | 492 | — |
| `pages/LaboratoryResults/DirectionForm.vue` | 529 | — |
| `pages/StatisticsReport/index.vue` | 435 | — |

### `ui-cards/` (6)

| Файл | Строк | Заметки |
|------|------:|---------|
| `ui-cards/Chat/ChatDialog.vue` | 935 | — |
| `ui-cards/Chat/ChatInput.vue` | 501 | — |
| `ui-cards/DirectionsHistory/index.vue` | 1137 | — |
| `ui-cards/LoadFile.vue` | 448 | — |
| `ui-cards/PatientResults/ResultControlParams.vue` | 445 | — |
| `ui-cards/ServiceScheduleEcp.vue` | 417 | — |

## 🟠 Фаза 2 — с рефакторингом (43)

Перенос на Composition API + замена jQuery / vue2-typeahead / v-calendar / mixins / `new Vue()`.

### `construct/` (2)

| Файл | Строк | Заметки |
|------|------:|---------|
| `construct/MicrobiologyResearchEditor.vue` | 721 | jQuery |
| `construct/TemplateEditor.vue` | 497 | jQuery |

### `fields/` (12)

| Файл | Строк | Заметки |
|------|------:|---------|
| `fields/AggregatePharmacotherapy.vue` | 270 | jQuery |
| `fields/AnesthesiaProcess.vue` | 887 | jQuery |
| `fields/DateField.vue` | 55 | jQuery |
| `fields/DateField2.vue` | 66 | jQuery |
| `fields/DateFieldNav.vue` | 145 | jQuery |
| `fields/LinkSelector.vue` | 119 | jQuery |
| `fields/MKBField.vue` | 72 | vue2-typeahead |
| `fields/MKBFieldForm.vue` | 199 | vue2-typeahead |
| `fields/SelectPicker.vue` | 105 | jQuery |
| `fields/SelectPickerB.vue` | 156 | jQuery |
| `fields/SelectPickerM.vue` | 151 | jQuery |
| `fields/TextFieldWithTemplates.vue` | 156 | jQuery |

### `forms/` (1)

| Файл | Строк | Заметки |
|------|------:|---------|
| `forms/LaboratoryTune.vue` | 189 | vue2-typeahead |

### `modals/` (2)

| Файл | Строк | Заметки |
|------|------:|---------|
| `modals/JournalGetMaterial.vue` | 127 | jQuery |
| `modals/L2CardCreate.vue` | 2094 | jQuery, vue2-typeahead |

### `pages/` (13)

| Файл | Строк | Заметки |
|------|------:|---------|
| `pages/DirectionVisit.vue` | 955 | jQuery |
| `pages/Directions.vue` | 748 | jQuery |
| `pages/LaboratoryResults/ReadyToEnter.vue` | 318 | jQuery |
| `pages/LaboratoryResults/ResultsForm.vue` | 612 | jQuery |
| `pages/LaboratoryResults/SearchToEnter.vue` | 162 | jQuery |
| `pages/LaboratoryResults/TextInputField.vue` | 490 | jQuery, vue2-typeahead |
| `pages/LaboratoryResults/Typeahead.vue` | 227 | jQuery, vue2-typeahead, new Vue() |
| `pages/MonitoringsReport/index.vue` | 744 | jQuery |
| `pages/PlanPharmacotherapy/components/AggregatePharmacoTherapyDepartment.vue` | 305 | jQuery |
| `pages/ResultsParaclinic.vue` | 3969 | jQuery |
| `pages/ResultsReport.vue` | 163 | jQuery |
| `pages/Stationar/index.vue` | 2403 | mixins |
| `pages/StatisticsTickets.vue` | 153 | jQuery |

### `ui-cards/` (13)

| Файл | Строк | Заметки |
|------|------:|---------|
| `ui-cards/CallDoctor.vue` | 537 | jQuery, vue2-typeahead |
| `ui-cards/DateRange.vue` | 173 | jQuery |
| `ui-cards/DirectionsHistory/Bottom/index.vue` | 191 | mixins |
| `ui-cards/IndividualPicker.vue` | 342 | jQuery |
| `ui-cards/LastResult.vue` | 222 | jQuery |
| `ui-cards/ListWaitCreator.vue` | 534 | v-calendar v2 |
| `ui-cards/PatientPicker.vue` | 1899 | jQuery |
| `ui-cards/PatientPickerDocCall.vue` | 997 | jQuery |
| `ui-cards/PatientSmallPicker.vue` | 638 | jQuery |
| `ui-cards/RecipeInput.vue` | 284 | vue2-typeahead |
| `ui-cards/ResearchesPicker.vue` | 1168 | jQuery |
| `ui-cards/SelectedResearches.vue` | 1832 | jQuery, vue2-typeahead |
| `ui-cards/StatisticsTicketCreator.vue` | 353 | jQuery |

## 🔵 Фаза 3 — class components (46)

Полная переписка с `vue-class-component` / `vue-property-decorator` на `<script setup lang="ts">`.

### `App.vue/` (1)

| Файл | Строк | Заметки |
|------|------:|---------|
| `App.vue` | 353 | — |

### `components/` (1)

| Файл | Строк | Заметки |
|------|------:|---------|
| `components/Navbar.vue` | 318 | — |

### `construct/` (5)

| Файл | Строк | Заметки |
|------|------:|---------|
| `construct/ConstructMenu.vue` | 67 | — |
| `construct/ConstructOrg.vue` | 507 | vue-formulate |
| `construct/ConstructScreening.vue` | 504 | mixins, vue2-filters |
| `construct/LayoutTemplate.vue` | 110 | — |
| `construct/PermanentDirectories.vue` | 110 | — |

### `fields/` (5)

| Файл | Строк | Заметки |
|------|------:|---------|
| `fields/AddressFiasField.vue` | 865 | vue2-typeahead |
| `fields/DynamicDirectoryField.vue` | 442 | vue2-typeahead |
| `fields/NumberGeneratorField.vue` | 141 | — |
| `fields/PermanentDirectoryField.vue` | 189 | — |
| `fields/TfomsAttachmentField.vue` | 97 | — |

### `pages/` (23)

| Файл | Строк | Заметки |
|------|------:|---------|
| `pages/BiomaterialGet.vue` | 87 | — |
| `pages/DirectionsPreview.vue` | 171 | — |
| `pages/EDS.vue` | 950 | local filters |
| `pages/EmailOrg.vue` | 402 | — |
| `pages/ExtraNotification.vue` | 396 | — |
| `pages/IndicatorСurator.vue` | 464 | — |
| `pages/LoginPage.vue` | 414 | jQuery |
| `pages/MenuPage.vue` | 1371 | — |
| `pages/PlanHospitalization/index.vue` | 174 | local filters |
| `pages/ReceiveByDirection.vue` | 237 | jQuery |
| `pages/ReceiveOneByOne.vue` | 498 | jQuery |
| `pages/ResultsDepartment.vue` | 260 | — |
| `pages/ResultsPreview.vue` | 261 | — |
| `pages/Schedule/Day.vue` | 233 | — |
| `pages/Schedule/DayHeader.vue` | 399 | — |
| `pages/Schedule/DaysGridNatural.vue` | 136 | — |
| `pages/Schedule/TimeMarker.vue` | 68 | — |
| `pages/Schedule/TimeSlot.vue` | 619 | — |
| `pages/Schedule/index.vue` | 287 | — |
| `pages/Search.vue` | 811 | — |
| `pages/SomeLinks.vue` | 58 | — |
| `pages/Statistics.vue` | 1465 | jQuery, v-calendar v2 |
| `pages/UploadDirections.vue` | 485 | local filters |

### `ui-cards/` (11)

| Файл | Строк | Заметки |
|------|------:|---------|
| `ui-cards/BiomaterialHistory.vue` | 225 | — |
| `ui-cards/BiomaterialSearch.vue` | 862 | jQuery |
| `ui-cards/CheckBackend.vue` | 150 | jQuery |
| `ui-cards/ExtendedPatientSearch/PatientSearchForm.vue` | 230 | — |
| `ui-cards/ExtendedPatientSearch/index.vue` | 419 | — |
| `ui-cards/ExtraNotificationFastEditor.vue` | 178 | — |
| `ui-cards/MonitoringHistoryViewer.vue` | 326 | jQuery |
| `ui-cards/ReplaceAppendModal.vue` | 64 | mixins |
| `ui-cards/ResearchPickById.vue` | 89 | — |
| `ui-cards/ScreeningDate.vue` | 207 | v-calendar v2 |
| `ui-cards/ScreeningDisplay.vue` | 379 | — |

## 🔴 Фаза 4 — блокеры Vue 3 (9)

Сначала заменить Vue 2-only паттерн или библиотеку, затем Composition API.

### `construct/` (3)

| Файл | Строк | Заметки |
|------|------:|---------|
| `construct/ConstructCompany.vue` | 867 | vue-formulate |
| `construct/ParaclinicResearchEditor.vue` | 2372 | mixins, jQuery, vue2-filters |
| `construct/TableConstructor.vue` | 593 | vue-codeditor |

### `fields/` (1)

| Файл | Строк | Заметки |
|------|------:|---------|
| `fields/RichTextEditor.vue` | 363 | tiptap v1 |

### `pages/` (5)

| Файл | Строк | Заметки |
|------|------:|---------|
| `pages/PlanHospitalization/components/Filters.vue` | 54 | local filters |
| `pages/PlanOperations/components/Filters.vue` | 83 | local filters |
| `pages/PlanOperations/index.vue` | 223 | local filters |
| `pages/PlanPharmacotherapy/components/Filters.vue` | 55 | local filters |
| `pages/PlanPharmacotherapy/index.vue` | 71 | local filters |
