export type StepStatus = "complete" | "running" | "pending" | "error";

export interface IOItem {
  id: string;
  name: string;
  type: "sample" | "reagent" | "buffer" | "equipment" | "waste" | "data";
  value?: string;
  unit?: string;
  note?: string;
}

export interface Param {
  id: string;
  label: string;
  value: string;
}

export interface BranchTrack {
  id: string;
  label: string;
  steps: WorkflowStep[];
}

export interface WorkflowStep {
  id: string;
  index: number;
  label: string;
  sublabel?: string;
  status: StepStatus;
  duration?: string;
  inputs: IOItem[];
  parameters: Param[];
  outputs: IOItem[];
  notes?: string;
  branchTrack?: BranchTrack;
}
