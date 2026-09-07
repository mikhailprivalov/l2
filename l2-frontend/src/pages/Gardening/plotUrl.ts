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
