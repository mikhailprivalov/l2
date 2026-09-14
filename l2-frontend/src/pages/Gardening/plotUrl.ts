export const gardeningPlotHref = (realEstateId: number, year?: number | null) => {
  const params = new URLSearchParams();
  params.set('id', String(realEstateId));
  if (year) {
    params.set('year', String(year));
  }
  return `/ui/gardening?${params.toString()}`;
};

export const openGardeningAllPrint = (
  format: 'pdf' | 'xlsx',
  params: Record<string, string | number | boolean | null | undefined>,
) => {
  const query = new URLSearchParams();
  query.set('type', '115.02');
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '' || value === false) {
      return;
    }
    if (value === true) {
      query.set(key, '1');
      return;
    }
    query.set(key, String(value));
  });
  const path = format === 'xlsx' ? '/forms/xlsx' : '/forms/pdf';
  window.open(`${path}?${query.toString()}`, '_blank');
};

const firstQueryValue = (value: unknown) => {
  if (Array.isArray(value)) {
    return value[0];
  }
  return value;
};

const parsePositiveInt = (value: unknown) => {
  const raw = firstQueryValue(value);
  if (raw === null || raw === undefined || raw === '') {
    return null;
  }
  const parsed = Number(raw);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return null;
  }
  return parsed;
};

export const parseGardeningPlotQuery = (query: Record<string, unknown> | undefined | null) => ({
  id: parsePositiveInt(query?.id),
  year: parsePositiveInt(query?.year),
});

const plotSortParts = (num: string | number | null | undefined): [number, number, string] => {
  if (num === null || num === undefined || num === '') {
    return [1, Number.POSITIVE_INFINITY, ''];
  }
  const text = String(num);
  const match = text.match(/^(\d+)(.*)$/);
  if (match) {
    return [0, Number(match[1]), match[2]];
  }
  return [0, Number.POSITIVE_INFINITY, text];
};

export const comparePlotNumbers = (
  left: string | number | null | undefined,
  right: string | number | null | undefined,
) => {
  const a = plotSortParts(left);
  const b = plotSortParts(right);
  if (a[0] !== b[0]) {
    return a[0] - b[0];
  }
  if (a[1] !== b[1]) {
    return a[1] - b[1];
  }
  return a[2].localeCompare(b[2], 'ru');
};
