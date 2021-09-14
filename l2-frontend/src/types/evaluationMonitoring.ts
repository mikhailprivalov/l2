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

export interface IEvaluationMonitoringGroup {
  title: string,
  fields: EvaluationMonitoringField[],
  grade: EvaluationMonitoringGrade,
}

export class EvaluationMonitoringGroup {
  title: string;

  fields: EvaluationMonitoringField[];

  editing: boolean;

  grade: EvaluationMonitoringGrade;

  constructor(group: IEvaluationMonitoringGroup) {
    this.title = group.title;
    this.fields = group.fields;
    this.editing = false;
    this.grade = group.grade;
  }

  public edit() {
    this.editing = true;
  }

  public cancel_edit() {
    this.editing = false;
  }

  public can_view_field() {
    return this.grade.grade !== null && !this.editing;
  }
}
