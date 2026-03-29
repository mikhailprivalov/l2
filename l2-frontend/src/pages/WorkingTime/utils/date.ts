import moment from 'moment';

import { SelectOptionItem } from '@/pages/WorkingTime/types/types';

export const getMonthDays = (year: number, month: number): Date[] => {
  const result: Date[] = [];

  const currentDate = new Date(year, month, 1);

  while (currentDate.getMonth() === month) {
    result.push(new Date(currentDate)); // важно: копия
    currentDate.setDate(currentDate.getDate() + 1);
  }

  return result;
};

export const MONTHS: SelectOptionItem[] = [
  { id: 0, label: 'Январь' },
  { id: 1, label: 'Февраль' },
  { id: 2, label: 'Март' },
  { id: 3, label: 'Апрель' },
  { id: 4, label: 'Май' },
  { id: 5, label: 'Июнь' },
  { id: 6, label: 'Июль' },
  { id: 7, label: 'Август' },
  { id: 8, label: 'Сентябрь' },
  { id: 9, label: 'Октябрь' },
  { id: 10, label: 'Ноябрь' },
  { id: 11, label: 'Декабрь' },
];

export const getYears = (currentYear: number, yearStart = 2023): SelectOptionItem[] => {
  const years: SelectOptionItem[] = [];
  for (let year = yearStart; year <= currentYear; year += 1) {
    years.push({
      id: year,
      label: String(year),
    });
  }
  return years;
};

export const isISODateString = (value: string): boolean => moment(value, 'YYYY-MM-DD', true).isValid();

export const formatDateKey = (date: Date): string => moment(date).format('YYYY-MM-DD');
