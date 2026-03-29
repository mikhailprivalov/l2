import { buildDateTime, isISODateString } from '@/pages/WorkingTime/utils/date';
import { EMPTY_WORK_TIME_DAY_CELL, WorkTimeDayCell } from '@/pages/WorkingTime/types/types';

export const calculateEmployeeWorkTimeTotals = (employee) => {
  let totalDiffTime = 0;
  const keys = Object.keys(employee);
  const lunchDuration = employee.lunchDuration * 60 * 1000;
  for (const key of keys) {
    if (isISODateString(key)) {
      const currentDay: WorkTimeDayCell = employee[key];
      if (currentDay.startWorkTime && currentDay.endWorkTime && !currentDay.typeId) {
        const startTime = buildDateTime(key, currentDay.startWorkTime);
        let endTime;
        if (currentDay.endWorkTime === '00:00') {
          endTime = new Date(startTime.getFullYear(), startTime.getMonth(), startTime.getDate() + 1, 0, 0);
        } else {
          endTime = buildDateTime(key, currentDay.endWorkTime);
        }
        const dayDiffTime = endTime.getTime() - startTime.getTime() - lunchDuration;
        totalDiffTime += dayDiffTime;
      }
    }
  }
  const totalDiffSec = totalDiffTime / (1000 * 60);
  const totalHoursDecimal = totalDiffSec / 60;
  const totalHours = Math.trunc(totalHoursDecimal);
  const totalMin = totalDiffSec % 60;
  return {
    totalHoursDecimal: totalHoursDecimal.toFixed(1),
    totalHours: `${totalHours}ч ${totalMin}м`,
  };
};

export const createEmptyWorkTimeDayCell = (): WorkTimeDayCell => ({
  ...EMPTY_WORK_TIME_DAY_CELL,
});

export const createWorkTimeDayCell = (
  startWorkTime: string | null = null,
  endWorkTime: string | null = null,
  typeId: number | null = null,
): WorkTimeDayCell => ({
  startWorkTime,
  endWorkTime,
  typeId,
});

export const createDayOffWorkTimeDayCell = (
  typeId: number | null,
): WorkTimeDayCell => ({
  startWorkTime: null,
  endWorkTime: null,
  typeId,
});
