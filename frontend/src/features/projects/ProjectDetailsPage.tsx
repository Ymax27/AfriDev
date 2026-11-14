import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, ExternalLink, Code2, Flag, GitMerge, Heart, Pencil, ShieldCheck, Star, Trash2, Users } from "lucide-react";

import {
  Alert,
  Avatar,
  Badge,
  Button,
  Card,
  DemoBadge,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  Select,
  SkeletonList,
  Tabs,
  TechnologyTag,
  Textarea,
} from "@/components/ui";
import { ReportDialog } from "@/components/ReportDialog";
import { contributionsApi, projectsApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { formatDate } from "@/lib/utils";

const DOMAINS = ["code", "documentation", "testing", "translation"] as const;

export default function ProjectDetailsPage() {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"overview" | "feedback" | "contributions">("overview");
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [contributionOpen, setContributionOpen] = useState(false);
  const [feedback, setFeedback] = useState({ concept_answer: "", improvement_answer: "", feature_answer: "" });
  const [contribution, setContribution] = useState<{ message: string; domain: string }>({ message: "", domain: "code" });
  const [notice, setNotice] = useState<string | null>(null);
  const [reportOpen, setReportOpen] = useState(false);
  const [verifyOpen, setVerifyOpen] = useState(false);
  const [verifyMethod, setVerifyMethod] = useState("repository_file");
  const [verifyToken, setVerifyToken] = useState("");
  const [challenge, setChallenge] = useState<{ id: string; token: string } | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState({ name: "", description: "", collaboration_mode: "showcase" });

  const project = useQuery({ queryKey: ["project", id], queryFn: () => projectsApi.get(id) });
  const feedbackList = useQuery({ queryKey: ["project", id, "feedback"], queryFn: () => projectsApi.feedback(id) });
  const contributionList = useQuery({
    queryKey: ["project", id, "contributions"],
    queryFn: () => contributionsApi.forProject(id),
    enabled: Boolean(user),
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["project", id] });
  };

  const like = useMutation({ mutationFn: () => projectsApi.like(id), onSuccess: invalidate });
  const pass = useMutation({ mutationFn: () => projectsApi.pass(id), onSuccess: invalidate });
  const submitFeedback = useMutation({
    mutationFn: () => projectsApi.submitFeedback(id, feedback),
    onSuccess: () => {
      setFeedbackOpen(false);
      setFeedback({ concept_answer: "", improvement_answer: "", feature_answer: "" });
      setNotice(t("project.feedbackSent"));
      void queryClient.invalidateQueries({ queryKey: ["project", id, "feedback"] });
    },
  });
  const markUseful = useMutation({
    mutationFn: (feedbackId: string) => projectsApi.markFeedbackUseful(id, feedbackId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["project", id, "feedback"] }),
  });
  const requestContribution = useMutation({
    mutationFn: () => contributionsApi.create(id, contribution),
    onSuccess: () => {
      setContributionOpen(false);
      setNotice(t("project.requestPending"));
      invalidate();
    },
  });
  const acceptContribution = useMutation({
    mutationFn: (contributionId: string) => contributionsApi.accept(contributionId),
    onSuccess: () => {
      setNotice(t("project.requestAccepted"));
      invalidate();
      void queryClient.invalidateQueries({ queryKey: ["project", id, "contributions"] });
    },
  });
  const rejectContribution = useMutation({
    mutationFn: (contributionId: string) => contributionsApi.reject(contributionId),
    onSuccess: () => {
      setNotice(t("project.requestRejected"));
      void queryClient.invalidateQueries({ queryKey: ["project", id, "contributions"] });
    },
  });
  const verifyStart = useMutation({
    mutationFn: () => projectsApi.startOwnershipVerification(id, verifyMethod),
    onSuccess: (record) => {
      setChallenge({ id: record.id, token: record.challenge_token });
      setNotice(t("project.verificationStarted"));
    },
  });
  const verifyConfirm = useMutation({
    mutationFn: () =>
      projectsApi.confirmOwnershipVerification(id, challenge?.id ?? "", verifyToken || undefined),
    onSuccess: () => {
      setVerifyOpen(false);
      setChallenge(null);
      setVerifyToken("");
      setNotice(t("project.verificationDone"));
      invalidate();
    },
  });
  const updateProject = useMutation({
    mutationFn: () => projectsApi.update(id, editForm),
    onSuccess: () => {
      setEditOpen(false);
      setNotice(t("project.updated"));
      invalidate();
    },
  });
  const deleteProject = useMutation({
    mutationFn: () => projectsApi.remove(id),
    onSuccess: () => navigate("/dashboard"),
  });
  const mergeContribution = useMutation({
    mutationFn: (contributionId: string) => contributionsApi.merged(contributionId),
    onSuccess: () => {
      setNotice(t("project.merged"));
      void queryClient.invalidateQueries({ queryKey: ["project", id, "contributions"] });
      invalidate();
    },
  });

  if (project.isLoading) return <SkeletonList rows={4} />;
  if (project.isError || !project.data) {
    return <ErrorState message={t("errors.notFound")} retryLabel={t("common.retry")} onRetry={() => void project.refetch()} />;
  }

  const data = project.data;
  const isOwner = user?.username === data.creator.username;
  const verifyError = verifyStart.error ?? verifyConfirm.error;

  return (
    <div>
      <Link to="/discover" className="mb-4 inline-flex items-center gap-1 text-sm text-muted hover:text-primary-700">
        <ArrowLeft className="size-4" aria-hidden="true" /> {t("common.back")}
      </Link>

      {notice ? (
        <div className="mb-4">
          <Alert tone="success">{notice}</Alert>
        </div>
      ) : null}

      <header className="surface-card mb-5 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 items-start gap-4">
            <Avatar name={data.name} src={data.cover_image_url} size={60} />
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-bold text-primary-800">{data.name}</h1>
                <DemoBadge show={data.is_demo} />
                {data.ownership_status === "verified" ? (
                  <Badge tone="accent"><ShieldCheck className="size-3" aria-hidden="true" /> {t("project.verified")}</Badge>
                ) : null}
              </div>
              <p className="mt-1 text-sm text-muted">
                {t("project.publishedBy")}{" "}
                <Link to={`/profile/${data.creator.username}`} className="font-medium text-primary-700 hover:underline">
                  @{data.creator.username}
                </Link>
                {data.country ? ` · ${data.country.flag_emoji ?? ""} ${language === "fr" ? data.country.name_fr : data.country.name}` : ""}
                {" · "}{formatDate(data.created_at, language)}
              </p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                <Badge tone="primary">{t(`modes.${data.collaboration_mode}.title`)}</Badge>
                {data.technologies.map((technology) => (
                  <TechnologyTag key={technology}>{technology}</TechnologyTag>
                ))}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              variant={data.liked_by_me ? "secondary" : "primary"}
              size="sm"
              onClick={() => like.mutate()}
              disabled={data.liked_by_me || !user}
              loading={like.isPending}
              icon={<Heart className="size-4" aria-hidden="true" />}
            >
              {data.liked_by_me ? t("project.liked") : t("project.like")} ({data.likes_count})
            </Button>
            {!isOwner ? (
              <Button variant="secondary" size="sm" onClick={() => pass.mutate()} loading={pass.isPending}>
                {t("project.pass")}
              </Button>
            ) : null}
            {data.collaboration_mode === "open_to_contributors" && !isOwner ? (
              <Button size="sm" onClick={() => setContributionOpen(true)} disabled={!user} icon={<Users className="size-4" aria-hidden="true" />}>
                {t("project.contribute")}
              </Button>
            ) : null}
            {data.collaboration_mode === "feedback" && !isOwner ? (
              <Button size="sm" onClick={() => setFeedbackOpen(true)} disabled={!user}>
                {t("project.feedback")}
              </Button>
            ) : null}
            {isOwner ? (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setEditForm({ name: data.name, description: data.description, collaboration_mode: data.collaboration_mode });
                    setEditOpen(true);
                  }}
                  icon={<Pencil className="size-4" aria-hidden="true" />}
                >
                  {t("common.edit")}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    if (window.confirm(t("project.deleteConfirm"))) deleteProject.mutate();
                  }}
                  loading={deleteProject.isPending}
                  icon={<Trash2 className="size-4" aria-hidden="true" />}
                >
                  {t("common.delete")}
                </Button>
              </>
            ) : user ? (
              <Button variant="ghost" size="sm" onClick={() => setReportOpen(true)} icon={<Flag className="size-4" aria-hidden="true" />}>
                {t("common.report")}
              </Button>
            ) : null}
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-4 text-xs text-muted">
          <span className="inline-flex items-center gap-1"><Star className="size-3.5" aria-hidden="true" /> {data.github_stars} {t("project.stars")}</span>
          <span>{data.view_count} {t("project.views")}</span>
          <span>{data.feedback_count} {t("project.tabFeedback").toLowerCase()}</span>
          {data.repository_url ? (
            <a href={data.repository_url} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-1 text-primary-700 hover:underline">
              <Code2 className="size-3.5" aria-hidden="true" /> {t("project.repository")}
            </a>
          ) : null}
          {data.demo_url ? (
            <a href={data.demo_url} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-1 text-primary-700 hover:underline">
              <ExternalLink className="size-3.5" aria-hidden="true" /> {t("project.demoLink")}
            </a>
          ) : null}
        </div>

        {isOwner ? (
          <div className="mt-4 flex flex-wrap items-center gap-2 rounded-xl bg-primary-50 p-3 text-xs text-primary-700">
            <ShieldCheck className="size-4" aria-hidden="true" />
            {t("project.ownership")} : {data.ownership_status === "verified" ? t("project.verified") : t("project.pending")}
            {data.ownership_status !== "verified" ? (
              <Button size="sm" variant="secondary" className="ml-auto" onClick={() => setVerifyOpen(true)}>
                {t("project.verifyOwnership")}
              </Button>
            ) : null}
          </div>
        ) : null}
      </header>

      <div className="mb-4">
        <Tabs
          active={tab}
          onChange={setTab}
          tabs={[
            { id: "overview", label: t("project.tabOverview") },
            { id: "feedback", label: t("project.tabFeedback"), count: data.feedback_count },
            { id: "contributions", label: t("project.tabContributions"), count: data.contributions_count },
          ]}
        />
      </div>

      {tab === "overview" ? (
        <Card>
          <p className="whitespace-pre-line text-sm leading-relaxed text-ink">{data.description}</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-100 p-3">
              <p className="text-xs text-muted">{t("project.mode")}</p>
              <p className="text-sm font-medium text-primary-800">{t(`modes.${data.collaboration_mode}.title`)}</p>
              <p className="mt-0.5 text-xs text-muted">{t(`modes.${data.collaboration_mode}.text`)}</p>
            </div>
            <div className="rounded-xl border border-slate-100 p-3">
              <p className="text-xs text-muted">{t("project.stack")}</p>
              <p className="text-sm font-medium text-primary-800">{data.technologies.join(" · ") || "—"}</p>
              <p className="mt-0.5 text-xs text-muted">{data.category}</p>
            </div>
          </div>
        </Card>
      ) : null}

      {tab === "feedback" ? (
        <div className="space-y-3">
          {!user ? <Alert tone="info">{t("common.loginRequired")}</Alert> : null}
          {feedbackList.isLoading ? (
            <SkeletonList rows={2} />
          ) : feedbackList.data && feedbackList.data.length > 0 ? (
            feedbackList.data.map((item) => (
              <Card key={item.id} className="space-y-3">
                <div className="flex items-center gap-2">
                  <Avatar name={item.author.full_name ?? item.author.username} src={item.author.avatar_url} size={32} />
                  <div>
                    <p className="text-sm font-medium text-primary-800">@{item.author.username}</p>
                    <p className="text-xs text-muted">{formatDate(item.created_at, language)}</p>
                  </div>
                  {item.is_useful ? <Badge tone="accent" className="ml-auto">{t("project.useful")}</Badge> : null}
                </div>
                <dl className="space-y-2 text-sm">
                  <div><dt className="text-xs text-muted">{t("project.feedbackConcept")}</dt><dd>{item.concept_answer}</dd></div>
                  <div><dt className="text-xs text-muted">{t("project.feedbackImprovement")}</dt><dd>{item.improvement_answer}</dd></div>
                  <div><dt className="text-xs text-muted">{t("project.feedbackFeature")}</dt><dd>{item.feature_answer}</dd></div>
                </dl>
                {!item.is_useful && user && !isOwner ? (
                  <Button size="sm" variant="ghost" onClick={() => markUseful.mutate(item.id)}>
                    {t("project.markUseful")}
                  </Button>
                ) : null}
              </Card>
            ))
          ) : (
            <EmptyState title={t("project.feedbackEmpty")} />
          )}
        </div>
      ) : null}

      {tab === "contributions" ? (
        <div className="space-y-3">
          {contributionList.isLoading ? (
            <SkeletonList rows={2} />
          ) : contributionList.data && contributionList.data.items.length > 0 ? (
            contributionList.data.items.map((item) => (
              <Card key={item.id} className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex min-w-0 items-start gap-3">
                  <Avatar name={item.requester.full_name ?? item.requester.username} src={item.requester.avatar_url} size={36} />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-primary-800">
                      @{item.requester.username} · <span className="text-muted">{t(`domains.${item.domain}`, { defaultValue: item.domain })}</span>
                    </p>
                    <p className="mt-1 text-sm text-muted">{item.message}</p>
                    <p className="mt-1 text-xs text-muted">{formatDate(item.created_at, language)}</p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge tone={item.status === "accepted" ? "accent" : item.status === "rejected" ? "danger" : "highlight"}>
                    {t(`status.${item.status}`, { defaultValue: item.status })}
                  </Badge>
                  {isOwner && item.status === "pending" ? (
                    <>
                      <Button size="sm" onClick={() => acceptContribution.mutate(item.id)} icon={<Check className="size-3.5" aria-hidden="true" />}>
                        {t("project.accept")}
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => rejectContribution.mutate(item.id)}>
                        {t("project.reject")}
                      </Button>
                    </>
                  ) : null}
                  {isOwner && item.status === "accepted" ? (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => mergeContribution.mutate(item.id)}
                      loading={mergeContribution.isPending}
                      icon={<GitMerge className="size-3.5" aria-hidden="true" />}
                    >
                      {t("project.markMerged")}
                    </Button>
                  ) : null}
                  {item.merged_at ? <Badge tone="accent">{t("project.mergedBadge")}</Badge> : null}
                  {item.conversation_id ? (
                    <Link to="/messages" className="text-xs font-medium text-primary-700 hover:underline">
                      {t("nav.messages")}
                    </Link>
                  ) : null}
                </div>
              </Card>
            ))
          ) : (
            <EmptyState title={t("project.contributionsEmpty")} />
          )}
        </div>
      ) : null}

      <Modal
        open={feedbackOpen}
        onClose={() => setFeedbackOpen(false)}
        title={t("project.feedback")}
        closeLabel={t("common.close")}
        footer={
          <>
            <Button variant="secondary" onClick={() => setFeedbackOpen(false)}>{t("common.cancel")}</Button>
            <Button
              onClick={() => submitFeedback.mutate()}
              loading={submitFeedback.isPending}
              disabled={Object.values(feedback).some((value) => value.trim().length < 5)}
            >
              {t("project.submitFeedback")}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label={t("project.feedbackConcept")} htmlFor="feedback-concept">
            <Textarea id="feedback-concept" rows={3} value={feedback.concept_answer} onChange={(event) => setFeedback({ ...feedback, concept_answer: event.target.value })} />
          </Field>
          <Field label={t("project.feedbackImprovement")} htmlFor="feedback-improvement">
            <Textarea id="feedback-improvement" rows={3} value={feedback.improvement_answer} onChange={(event) => setFeedback({ ...feedback, improvement_answer: event.target.value })} />
          </Field>
          <Field label={t("project.feedbackFeature")} htmlFor="feedback-feature">
            <Textarea id="feedback-feature" rows={3} value={feedback.feature_answer} onChange={(event) => setFeedback({ ...feedback, feature_answer: event.target.value })} />
          </Field>
        </div>
      </Modal>

      <Modal
        open={contributionOpen}
        onClose={() => setContributionOpen(false)}
        title={t("project.contribute")}
        closeLabel={t("common.close")}
        footer={
          <>
            <Button variant="secondary" onClick={() => setContributionOpen(false)}>{t("common.cancel")}</Button>
            <Button
              onClick={() => requestContribution.mutate()}
              loading={requestContribution.isPending}
              disabled={contribution.message.trim().length < 20}
            >
              {t("project.sendRequest")}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label={t("project.domain")} htmlFor="contribution-domain">
            <Select id="contribution-domain" value={contribution.domain} onChange={(event) => setContribution({ ...contribution, domain: event.target.value })}>
              {DOMAINS.map((domain) => (
                <option key={domain} value={domain}>{t(`domains.${domain}`)}</option>
              ))}
            </Select>
          </Field>
          <Field label={t("project.message")} hint={t("project.messageHelp")} htmlFor="contribution-message">
            <Textarea id="contribution-message" rows={4} value={contribution.message} onChange={(event) => setContribution({ ...contribution, message: event.target.value })} />
          </Field>
          {contribution.message.length > 0 && contribution.message.trim().length < 20 ? (
            <p className="text-xs text-red-600">20</p>
          ) : null}
        </div>
      </Modal>

      <ReportDialog open={reportOpen} onClose={() => setReportOpen(false)} targetType="project" targetId={id} />

      <Modal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        title={t("project.editTitle")}
        closeLabel={t("common.close")}
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditOpen(false)}>{t("common.cancel")}</Button>
            <Button onClick={() => updateProject.mutate()} loading={updateProject.isPending}>
              {t("common.save")}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {updateProject.isError ? <Alert tone="error">{t("errors.validation")}</Alert> : null}
          <Field label={t("project.name")} htmlFor="project-edit-name">
            <Input
              id="project-edit-name"
              value={editForm.name}
              onChange={(event) => setEditForm({ ...editForm, name: event.target.value })}
            />
          </Field>
          <Field label={t("project.description")} htmlFor="project-edit-description">
            <Textarea
              id="project-edit-description"
              rows={5}
              value={editForm.description}
              onChange={(event) => setEditForm({ ...editForm, description: event.target.value })}
            />
          </Field>
          <Field label={t("project.mode")} hint={t("project.modeHelp")} htmlFor="project-edit-mode">
            <Select
              id="project-edit-mode"
              value={editForm.collaboration_mode}
              onChange={(event) => setEditForm({ ...editForm, collaboration_mode: event.target.value })}
            >
              {["showcase", "feedback", "open_to_contributors"].map((mode) => (
                <option key={mode} value={mode}>{t(`modes.${mode}.title`)}</option>
              ))}
            </Select>
          </Field>
        </div>
      </Modal>

      <Modal
        open={verifyOpen}
        onClose={() => setVerifyOpen(false)}
        title={t("project.verifyOwnership")}
        closeLabel={t("common.close")}
        footer={
          challenge ? (
            <>
              <Button variant="secondary" onClick={() => setVerifyOpen(false)}>{t("common.cancel")}</Button>
              <Button onClick={() => verifyConfirm.mutate()} loading={verifyConfirm.isPending}>
                {t("project.verifyConfirm")}
              </Button>
            </>
          ) : (
            <>
              <Button variant="secondary" onClick={() => setVerifyOpen(false)}>{t("common.cancel")}</Button>
              <Button onClick={() => verifyStart.mutate()} loading={verifyStart.isPending}>
                {t("project.verifyStart")}
              </Button>
            </>
          )
        }
      >
        <div className="space-y-4">
          {verifyError ? (
            <Alert tone="error">{verifyError instanceof Error ? verifyError.message : t("errors.validation")}</Alert>
          ) : null}
          <Field label={t("project.verifyMethod")} hint={t("project.verifyMethodHelp")} htmlFor="verify-method">
            <Select id="verify-method" value={verifyMethod} onChange={(event) => setVerifyMethod(event.target.value)}>
              <option value="repository_owner">{t("project.verifyRepositoryOwner")}</option>
              <option value="repository_file">{t("project.verifyRepositoryFile")}</option>
              <option value="domain">{t("project.verifyDomain")}</option>
            </Select>
          </Field>

          {challenge ? (
            <div className="space-y-3 rounded-xl bg-slate-50 p-3 text-sm">
              <p className="text-muted">
                {verifyMethod === "repository_owner"
                  ? t("project.verifyOwnerHint")
                  : verifyMethod === "domain"
                    ? t("project.verifyDomainHint")
                    : t("project.verifyFileHint")}
              </p>
              <p className="rounded-lg bg-white px-3 py-2 font-mono text-xs text-primary-800">{challenge.token}</p>
              {verifyMethod !== "repository_owner" ? (
                <Field label={t("project.verifyToken")} htmlFor="verify-token">
                  <Input id="verify-token" value={verifyToken} onChange={(event) => setVerifyToken(event.target.value)} />
                </Field>
              ) : null}
            </div>
          ) : null}
        </div>
      </Modal>
    </div>
  );
}
