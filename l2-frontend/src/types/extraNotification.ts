export interface ExtraNotificationResearch {
  id: number,
  title: string,
  shortTitle: string,
}

export interface ExtraNotificationData {
  hospital: string,
  issPk: number,
  mainConfirm: string,
  mainDirection: number,
  patient: string,
  born: string,
  slaveConfirm: string | null,
  slaveDir: number,
  value: string | null,
  researchId: number,
  researchTitle: string,
}
