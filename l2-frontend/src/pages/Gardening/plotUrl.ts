export const gardeningPlotHref = (realEstateId: number, year?: number | null) => {
  const params = new URLSearchParams();
  params.set('id', String(realEstateId));
  if (year) {
    params.set('year', String(year));
  }
  return `/ui/gardening?${params.toString()}`;
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
