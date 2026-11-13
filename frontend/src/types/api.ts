export interface Country {
  id: string;
  code: string;
  name: string;
  name_fr: string;
  flag_emoji?: string | null;
  region?: string | null;
}

export interface UserSummary {
  id: string;
  username: string;
  full_name?: string | null;
  avatar_url?: string | null;
  level: string;
  reputation_points: number;
  country?: Country | null;
}

export interface Skill {
  id: string;
  name: string;
  level: string;
  years_experience?: number | null;
}

export interface Role {
  role: string;
}

export interface User extends UserSummary {
  bio?: string | null;
  city?: string | null;
  website_url?: string | null;
  github_url?: string | null;
  github_login?: string | null;
  is_admin: boolean;
  is_demo: boolean;
  roles: Role[];
  skills: Skill[];
  created_at: string;
}

export interface UserProfile extends User {
  projects_count: number;
  accepted_solutions_count: number;
  field_reports_count: number;
}

export type CollaborationMode = "showcase" | "feedback" | "open_to_contributors";

export interface Project {
  id: string;
  name: string;
  slug: string;
  description: string;
  repository_url?: string | null;
  demo_url?: string | null;
  cover_image_url?: string | null;
  technologies: string[];
  tags: string[];
  category: string;
  collaboration_mode: CollaborationMode;
  ownership_status: string;
  is_published: boolean;
  is_demo: boolean;
  is_featured: boolean;
  view_count: number;
  github_stars: number;
  creator: UserSummary;
  country?: Country | null;
  created_at: string;
  likes_count: number;
  contributions_count: number;
  feedback_count: number;
  liked_by_me: boolean;
  passed_by_me: boolean;
}

export interface ProjectFeedback {
  id: string;
  project_id: string;
  concept_answer: string;
  improvement_answer: string;
  feature_answer: string;
  is_useful: boolean;
  author: UserSummary;
  created_at: string;
}

export interface Contribution {
  id: string;
  project_id: string;
  message: string;
  domain: string;
  status: string;
  requester: UserSummary;
  conversation_id?: string | null;
  created_at: string;
  reviewed_at?: string | null;
}

export interface Solution {
  id: string;
  problem_id: string;
  explanation: string;
  code_snippet?: string | null;
  implementation_steps?: string | null;
  references: string[];
  is_accepted: boolean;
  accepted_at?: string | null;
  author: UserSummary;
  created_at: string;
}

export interface Problem {
  id: string;
  title: string;
  slug: string;
  description: string;
  category: string;
  technology?: string | null;
  code_snippet?: string | null;
  documentation_links: string[];
  country?: Country | null;
  api_entry_id?: string | null;
  author: UserSummary;
  is_demo: boolean;
  created_at: string;
  solution_count: number;
  has_accepted_solution: boolean;
}

export interface ProblemDetail extends Problem {
  solutions: Solution[];
}

export interface FieldReport {
  id: string;
  title: string;
  problem_summary: string;
  solution_summary: string;
  common_errors?: string | null;
  workarounds?: string | null;
  status: string;
  confirmation_count: number;
  last_validated_at?: string | null;
  problem_id?: string | null;
  solution_id?: string | null;
  api_entry_id?: string | null;
  author: UserSummary;
  country?: Country | null;
  is_demo: boolean;
  created_at: string;
}

export interface Mission {
  id: string;
  title: string;
  slug: string;
  description: string;
  objectives: string;
  required_skills: string[];
  reward_points: number;
  reward_description?: string | null;
  deadline?: string | null;
  status: string;
  sponsor: UserSummary;
  country?: Country | null;
  api_entry_id?: string | null;
  is_demo: boolean;
  created_at: string;
  submissions_count: number;
}

export interface MissionSubmission {
  id: string;
  mission_id: string;
  developer_id: string;
  summary: string;
  solution_url?: string | null;
  status: string;
  review_note?: string | null;
  points_awarded: number;
  created_at: string;
}

export interface APIEntry {
  id: string;
  name: string;
  provider_name: string;
  slug: string;
  description: string;
  category: string;
  countries: string[];
  documentation_url: string;
  pricing?: string | null;
  api_status: string;
  integration_notes?: string | null;
  is_published: boolean;
  is_demo: boolean;
  created_at: string;
  related_field_reports: number;
}

export interface CountryStats {
  developers: number;
  projects: number;
  field_reports: number;
  accepted_contributions: number;
  reputation_points: number;
  activity_score: number;
}

export interface CountryHub {
  country: Country;
  stats: CountryStats;
  top_developers: Array<{
    username: string;
    full_name?: string | null;
    avatar_url?: string | null;
    level: string;
    reputation_points: number;
  }>;
  recent_projects: Array<{ id: string; name: string; slug: string; mode: string }>;
  recent_field_reports: Array<{ id: string; title: string; status: string }>;
  open_missions: Array<{ id: string; title: string; reward_points: number }>;
}

export interface DeveloperRank {
  rank: number;
  user_id: string;
  username: string;
  full_name?: string | null;
  avatar_url?: string | null;
  country?: Country | null;
  level: string;
  reputation_points: number;
  period_points: number;
}

export interface ProjectRank {
  rank: number;
  project_id: string;
  name: string;
  slug: string;
  creator_username: string;
  country?: Country | null;
  likes: number;
  accepted_contributors: number;
  useful_feedback: number;
  visits: number;
  score: number;
}

export interface CountryRank {
  rank: number;
  country: Country;
  active_developers: number;
  total_points: number;
  average_points: number;
}

export interface ConversationMember {
  user_id: string;
  role: string;
}

export interface Conversation {
  id: string;
  type: string;
  title: string;
  project_id?: string | null;
  country_id?: string | null;
  mission_id?: string | null;
  last_message_at?: string | null;
  created_at: string;
  members: ConversationMember[];
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  body: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  points: number;
  action_type: string;
  reference_type: string;
  reference_id: string;
  status: string;
  note?: string | null;
  is_demo: boolean;
  created_at: string;
}

export interface ReputationSummary {
  user_id: string;
  username: string;
  reputation_points: number;
  level: string;
  next_level?: string | null;
  points_to_next_level: number;
  recent_transactions: Transaction[];
}

export interface NotificationItem {
  id: string;
  type: string;
  title: string;
  body?: string | null;
  link?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface AdminOverview {
  users: number;
  active_users: number;
  demo_users: number;
  projects: number;
  problems: number;
  field_reports: number;
  missions: number;
  api_entries: number;
  open_reports: number;
  reputation_transactions: number;
  points_awarded: number;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
