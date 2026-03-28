export type HolidayKind = 'HOLIDAY' | 'WORKING';
export interface HolidayItem {
  kind: HolidayKind;
  shorten_minutes: number | null;
}
export type ISODateString = string
export type HolidaysMap = Record<ISODateString, HolidayItem>;
