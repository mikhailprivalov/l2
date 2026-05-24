import { HolidaysMap, TableColumn } from '@/pages/WorkingTime/types/types';
import { formatDateKey, formatDateTitle, isWeekend } from '@/pages/WorkingTime/utils/date';

const buildDateColumns = (
  monthDays: Date[],
  holidays: HolidaysMap,
  renderBodyCell: TableColumn['renderBodyCell'],
): TableColumn[] => monthDays.map((day) => {
  const dateString = formatDateKey(day);
  return {
    key: dateString,
    field: dateString,
    title: formatDateTitle(day),
    align: 'center',
    width: 47,
    isWeekend: isWeekend(day),
    isHoliday: holidays[dateString]?.kind === 'HOLIDAY',
    renderBodyCell,
  };
});

export default buildDateColumns;
