export interface EvaluationMonitoringGrade {
    grade: string | null,
    comment: string | null,
    grader: string | null,
}

export interface EvaluationMonitoringField {
    result_id: number,
    field_id: number,
    value_aggregate: number,
    value_text: string,
}
  
export interface EvaluationMonitoringGroup {
    title: string,
    fields: EvaluationMonitoringField[],
    editing: boolean,
    grade: EvaluationMonitoringGrade,
}