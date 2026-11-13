import { buildQuery, request } from "@/lib/api-client";
import type {
  AdminOverview,
  APIEntry,
  Contribution,
  Conversation,
  Country,
  CountryHub,
  CountryRank,
  DeveloperRank,
  FieldReport,
  Message,
  Mission,
  MissionSubmission,
  Paginated,
  Problem,
  ProblemDetail,
  Project,
  ProjectFeedback,
  ProjectRank,
  ReputationSummary,
  Solution,
  Transaction,
  User,
  UserProfile,
} from "@/types/api";

export interface ListParams {
  page?: number;
  page_size?: number;
  q?: string;
  country?: string;
  category?: string;
  technology?: string;
  mode?: string;
  creator?: string;
  sort?: string;
  status?: string;
  skill?: string;
  period?: string;
  unread_only?: boolean;
}

export const authApi = {
  status: () => request<{ authenticated: boolean; github_oauth_enabled: boolean; demo_mode: boolean }>({ url: "/auth/status" }),
  me: () => request<User>({ url: "/auth/me" }),
  githubUrl: () => request<{ authorization_url: string }>({ url: "/auth/github" }),
  devLogin: (username?: string, as_admin = false) =>
    request<User>({ method: "POST", url: "/auth/dev-login", data: { username, as_admin } }),
  logout: () => request<void>({ method: "POST", url: "/auth/logout" }),
};

export const usersApi = {
  me: () => request<UserProfile>({ url: "/users/me" }),
  updateMe: (payload: Record<string, unknown>) =>
    request<UserProfile>({ method: "PATCH", url: "/users/me", data: payload }),
  list: (params: ListParams = {}) =>
    request<Paginated<User>>({ url: `/users${buildQuery({ ...params })}` }),
  profile: (username: string) => request<UserProfile>({ url: `/users/${username}` }),
};

export const projectsApi = {
  list: (params: ListParams = {}) =>
    request<Paginated<Project>>({ url: `/projects${buildQuery({ ...params })}` }),
  discover: (params: ListParams = {}) =>
    request<Paginated<Project>>({ url: `/projects/discover${buildQuery({ ...params })}` }),
  get: (id: string) => request<Project>({ url: `/projects/${id}` }),
  create: (payload: Record<string, unknown>) =>
    request<Project>({ method: "POST", url: "/projects", data: payload }),
  update: (id: string, payload: Record<string, unknown>) =>
    request<Project>({ method: "PATCH", url: `/projects/${id}`, data: payload }),
  like: (id: string) => request<void>({ method: "POST", url: `/projects/${id}/like` }),
  pass: (id: string) => request<void>({ method: "POST", url: `/projects/${id}/pass` }),
  feedback: (id: string) => request<ProjectFeedback[]>({ url: `/projects/${id}/feedback` }),
  submitFeedback: (id: string, payload: Record<string, unknown>) =>
    request<ProjectFeedback>({ method: "POST", url: `/projects/${id}/feedback`, data: payload }),
  markFeedbackUseful: (projectId: string, feedbackId: string) =>
    request<ProjectFeedback>({ method: "POST", url: `/projects/${projectId}/feedback/${feedbackId}/useful` }),
  startOwnershipVerification: (id: string) =>
    request<{ id: string; challenge_token: string; status: string }>({
      method: "POST",
      url: `/projects/${id}/ownership-verification`,
      data: { method: "repository_file" },
    }),
  confirmOwnershipVerification: (projectId: string, verificationId: string) =>
    request<{ status: string }>({
      method: "POST",
      url: `/projects/${projectId}/ownership-verification/${verificationId}/confirm`,
    }),
};

export const contributionsApi = {
  create: (projectId: string, payload: Record<string, unknown>) =>
    request<Contribution>({ method: "POST", url: `/projects/${projectId}/contributions`, data: payload }),
  mine: () => request<Paginated<Contribution>>({ url: "/contributions/me" }),
  forProject: (projectId: string) =>
    request<Paginated<Contribution>>({ url: `/projects/${projectId}/contributions` }),
  accept: (id: string) => request<Contribution>({ method: "POST", url: `/contributions/${id}/accept` }),
  reject: (id: string) => request<Contribution>({ method: "POST", url: `/contributions/${id}/reject`, data: {} }),
  merged: (id: string) => request<Contribution>({ method: "POST", url: `/contributions/${id}/merged` }),
};

export const knowledgeApi = {
  list: (params: ListParams = {}) =>
    request<Paginated<Problem>>({ url: `/knowledge${buildQuery({ ...params })}` }),
  get: (id: string) => request<ProblemDetail>({ url: `/knowledge/${id}` }),
  create: (payload: Record<string, unknown>) =>
    request<Problem>({ method: "POST", url: "/knowledge", data: payload }),
  addSolution: (problemId: string, payload: Record<string, unknown>) =>
    request<Solution>({ method: "POST", url: `/knowledge/${problemId}/solutions`, data: payload }),
  acceptSolution: (problemId: string, solutionId: string) =>
    request<Solution>({ method: "POST", url: `/knowledge/${problemId}/solutions/${solutionId}/accept` }),
};

export const fieldReportsApi = {
  list: (params: ListParams = {}) =>
    request<Paginated<FieldReport>>({ url: `/field-reports${buildQuery({ ...params })}` }),
  get: (id: string) => request<FieldReport>({ url: `/field-reports/${id}` }),
  confirm: (id: string, comment?: string) =>
    request<FieldReport>({ method: "POST", url: `/field-reports/${id}/confirm`, data: { comment } }),
};

export const countriesApi = {
  list: () => request<Country[]>({ url: "/countries" }),
  hub: (code: string) => request<CountryHub>({ url: `/countries/${code}` }),
};

export const leaderboardApi = {
  developers: (period = "all", country?: string) =>
    request<{ items: DeveloperRank[]; scope: string; period: string; country?: string | null }>({
      url: `/leaderboard/developers${buildQuery({ period, country })}`,
    }),
  projects: () => request<ProjectRank[]>({ url: "/leaderboard/projects" }),
  countries: () => request<CountryRank[]>({ url: "/leaderboard/countries" }),
};

export const missionsApi = {
  list: (params: ListParams = {}) =>
    request<Paginated<Mission>>({ url: `/missions${buildQuery({ ...params })}` }),
  get: (id: string) => request<Mission>({ url: `/missions/${id}` }),
  create: (payload: Record<string, unknown>) =>
    request<Mission>({ method: "POST", url: "/missions", data: payload }),
  submit: (id: string, payload: Record<string, unknown>) =>
    request<MissionSubmission>({ method: "POST", url: `/missions/${id}/submissions`, data: payload }),
  submissions: (id: string) => request<MissionSubmission[]>({ url: `/missions/${id}/submissions` }),
  review: (submissionId: string, approve: boolean, review_note?: string) =>
    request<MissionSubmission>({
      method: "POST",
      url: `/missions/submissions/${submissionId}/review`,
      data: { approve, review_note },
    }),
};

export const apisDirectoryApi = {
  list: (params: ListParams = {}) =>
    request<Paginated<APIEntry>>({ url: `/apis${buildQuery({ ...params })}` }),
  get: (id: string) => request<APIEntry>({ url: `/apis/${id}` }),
  categories: () => request<Array<{ category: string; count: number }>>({ url: "/apis/categories" }),
};

export const messagingApi = {
  conversations: () => request<Paginated<Conversation>>({ url: "/conversations" }),
  messages: (conversationId: string) =>
    request<Message[]>({ url: `/conversations/${conversationId}/messages` }),
  send: (conversationId: string, body: string) =>
    request<Message>({
      method: "POST",
      url: `/conversations/${conversationId}/messages`,
      data: { body },
    }),
};

export const reputationApi = {
  me: () => request<ReputationSummary>({ url: "/reputation/me" }),
  transactions: () => request<{ items: Transaction[]; total: number }>({ url: "/reputation/transactions" }),
};

export const moderationApi = {
  report: (payload: Record<string, unknown>) =>
    request<void>({ method: "POST", url: "/reports", data: payload }),
  block: (username: string) =>
    request<void>({ method: "POST", url: "/blocks", data: { username } }),
};

export const adminApi = {
  overview: () => request<AdminOverview>({ url: "/admin/overview" }),
  users: (q?: string) => request<{ items: Array<Record<string, unknown>>; total: number }>({
    url: `/admin/users${buildQuery({ q })}`,
  }),
  suspend: (id: string) => request<User>({ method: "POST", url: `/admin/users/${id}/suspend` }),
  reactivate: (id: string) => request<User>({ method: "POST", url: `/admin/users/${id}/reactivate` }),
  reports: () => request<Array<Record<string, unknown>>>({ url: "/admin/reports" }),
  resolveReport: (id: string, status: "resolved" | "dismissed") =>
    request<void>({ method: "POST", url: `/admin/reports/${id}/resolve`, data: { status } }),
  recalculate: () => request<{ users_recalculated: number }>({ method: "POST", url: "/admin/reputation/recalculate" }),
  purgeDemo: () => request<Record<string, number>>({ method: "POST", url: "/admin/demo/purge" }),
};
