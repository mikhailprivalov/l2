type FinSourceRow = { pk: number; title: string };
type BaseRow = { pk: number; fin_sources?: FinSourceRow[] };

export default function finSourceOptionsForBase(bases: BaseRow[] | undefined, basePk?: number | null) {
  const found = (bases || []).find((row) => row.pk === basePk);
  return (found?.fin_sources || []).map((row) => ({
    id: row.pk,
    label: row.title,
  }));
}
