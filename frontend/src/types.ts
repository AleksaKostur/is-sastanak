export interface User {
  id: number;
  org_unit_id: number;
  first_name: string;
  father_name: string;
  last_name: string;
  jmbg: string;
  job_title: string;
  work_phone: string | null;
  mobile_phone: string | null;
  email: string;
  is_active: boolean;
}

export interface Meeting {
  id: number;
  topic: string;
  category_id: number;
  organizer_id: number;
  org_unit_id: number;
  meeting_type: "STALNI" | "VANREDNI";
  recurrence: string | null;
  scheduled_at: string;
  location: string;
  room: string;
  status: "PLANIRAN" | "ODRZAN" | "ODLOZEN" | "OTKAZAN";
  status_reason: string | null;
  act_number: string | null;
  act_date: string | null;
  act_organization: string | null;
  intro: string | null;
  conclusion: string | null;
}

export interface AgendaItem {
  id: number;
  meeting_id: number;
  order_no: number;
  title: string;
  discussion: string | null;
}

export interface Participant {
  id: number;
  meeting_id: number;
  user_id: number | null;
  external_person_id: number | null;
  role_in_meeting: "RUKOVODILAC" | "ZAPISNICAR" | "UCESNIK";
  is_planned: boolean;
  attended: boolean | null;
  substitute_for_id: number | null;
  recorded_at: string | null;
}

export interface AppNotification {
  id: number;
  user_id: number;
  meeting_id: number | null;
  type: string;
  message: string;
  is_read: boolean;
  created_at: string | null;
}

export interface MeetingCategory {
  id: number;
  name: string;
}

export interface TokenPayload {
  sub: string;
  roles: string[];
  type: string;
  exp: number;
}