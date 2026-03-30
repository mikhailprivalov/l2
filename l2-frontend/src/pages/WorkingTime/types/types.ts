import type * as Vue from 'vue';

export type HolidayKind = 'HOLIDAY' | 'WORKING';
export interface HolidayItem {
  kind: HolidayKind;
  shorten_minutes: number | null;
}
export type ISODateString = string
export type HolidaysMap = Record<ISODateString, HolidayItem>;

export interface RefBookItem {
  id: string | number;
  label: string;
}

export interface DepartmentItem extends RefBookItem {
  lunchDuration: number | null;
}

export type DepartmentsResponse = DepartmentItem[];

export type WorkDayStatusItem = RefBookItem;
export type ShiftVariantItem = RefBookItem;

export interface RefBooksResponse {
  workDayStatuses: WorkDayStatusItem[];
  shiftsVariants: ShiftVariantItem[];
}

export interface TimeOptionItem {
  id: string | number;
  start: string;
  end: string;
}

export type Nullable<T> = T | null;

export interface WorkTimeDayCell {
  startWorkTime: Nullable<string>;
  endWorkTime: Nullable<string>;
  typeId: Nullable<number>;
  blocked?: boolean;
}

export const EMPTY_WORK_TIME_DAY_CELL: WorkTimeDayCell = {
  startWorkTime: null,
  endWorkTime: null,
  typeId: null,
};

export interface GetEmployeesWorkTimeResult {
  data: object[];
  documentPk: number | null;
  documentIsBlocked: boolean;
  documentIsCreated: boolean;
}

type RenderFn = typeof Vue.h;
type VNode = Vue.VNode;

export interface TableColumn {
  field: string;
  key: string;
  title: string;
  align: 'left' | 'center' | 'right';
  width: number;
  fixed?: 'left' | 'right';
  type?: string;
  isWeekend?: boolean;
  isHoliday?: boolean;
  renderHeaderCell?: (params: any, h: RenderFn) => VNode;
  renderBodyCell?: (params: any, h: RenderFn) => VNode;
}

export interface SelectOptionItem {
  id: string | number;
  label: string;
}
