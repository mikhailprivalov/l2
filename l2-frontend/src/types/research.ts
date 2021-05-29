import { Fraction } from '@/types/fraction';

export type ResearchPk = number;

export interface Research {
  pk: ResearchPk
  title: string
  full_title: string | void
  dateConfirm: string | void
  fractions: Fraction[]
  fio?: string
}
