import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CalendarClock, Gift, Target } from "lucide-react";

import { Alert, Badge, Button, Card, ErrorState, Field, Input, SkeletonList, TechnologyTag, Textarea } from "@/components/ui";
import { missionsApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { formatDate } from "@/lib/utils";

export default function MissionDetailsPage() {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ summary: "", solution_url: "" });
  const [reviewNote, setReviewNote] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  const mission = useQuery({ queryKey: ["mission", id], queryFn: () => missionsApi.get(id) });
  const isSponsor = Boolean(user && mission.data && user.username === mission.data.sponsor.username);

  const submissions = useQuery({
    queryKey: ["mission", id, "submissions"],
    queryFn: () => missionsApi.submissions(id),
    enabled: isSponsor,
  });

  const submit = useMutation({
    mutationFn: () =>
      missionsApi.submit(id, { summary: form.summary, solution_url: form.solution_url || null }),
    onSuccess: () => {
      setNotice(t("missions.submitSuccess"));
      setForm({ summary: "", solution_url: "" });
      void queryClient.invalidateQueries({ queryKey: ["mission", id] });
    },
  });

  const review = useMutation({
    mutationFn: ({ submissionId, approve }: { submissionId: string; approve: boolean }) =>
      missionsApi.review(submissionId, approve, reviewNote || undefined),
    onSuccess: () => {
      setReviewNote("");
      void queryClient.invalidateQueries({ queryKey: ["mission", id, "submissions"] });
      void queryClient.invalidateQueries({ queryKey: ["mission", id] });
    },
  });

  if (mission.isLoading) return <SkeletonList rows={4} />;
  if (mission.isError || !mission.data) {
    return <ErrorState message={t("errors.notFound")} retryLabel={t("common.retry")} onRetry={() => void mission.refetch()} />;
  }

  const data = mission.data;
  const alreadySubmitted = submissions.data?.some((item) => item.developer_id === user?.id) ?? false;

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/missions" className="mb-4 inline-flex items-center gap-1 text-sm text-muted hover:text-primary-700">
        <ArrowLeft className="size-4" aria-hidden="true" /> {t("common.back")}
      </Link>

      {notice ? <div className="mb-4"><Alert tone="success">{notice}</Alert></div> : null}

      <header className="surface-card mb-5 p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">{data.status.replaceAll("_", " ")}</Badge>
          {data.country ? <Badge tone="neutral">{data.country.flag_emoji ?? ""} {language === "fr" ? data.country.name_fr : data.country.name}</Badge> : null}
        </div>
        <h1 className="mt-3 text-2xl font-bold text-primary-800">{data.title}</h1>
        <p className="mt-1 text-xs text-muted">{t("missions.sponsor")} : @{data.sponsor.username} · {formatDate(data.created_at, language)}</p>
        <p className="mt-4 whitespace-pre-line text-sm leading-relaxed">{data.description}</p>

        <dl className="mt-5 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-slate-100 p-3">
            <dt className="flex items-center gap-1 text-xs text-muted"><Gift className="size-3.5" aria-hidden="true" /> {t("missions.reward")}</dt>
            <dd className="mt-1 text-sm font-medium text-primary-800">{data.reward_description ?? `${data.reward_points} ${t("missions.points")}`}</dd>
          </div>
          <div className="rounded-xl border border-slate-100 p-3">
            <dt className="flex items-center gap-1 text-xs text-muted"><CalendarClock className="size-3.5" aria-hidden="true" /> {t("missions.deadline")}</dt>
            <dd className="mt-1 text-sm font-medium text-primary-800">{formatDate(data.deadline, language)}</dd>
          </div>
        </dl>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {data.required_skills.map((skill) => (
            <TechnologyTag key={skill}>{skill}</TechnologyTag>
          ))}
        </div>
      </header>

      <Card className="mb-5">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-primary-800">
          <Target className="size-4 text-accent-600" aria-hidden="true" /> {t("missions.objectives")}
        </h2>
        <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-muted">{data.objectives}</p>
      </Card>

      {isSponsor ? (
        <Card>
          <h2 className="text-sm font-semibold text-primary-800">{t("missions.submissions")} ({data.submissions_count})</h2>
          <p className="mt-1 text-xs text-muted">{t("missions.ownMission")}</p>
          {submissions.isLoading ? (
            <SkeletonList rows={2} />
          ) : submissions.data && submissions.data.length > 0 ? (
            <ul className="mt-3 space-y-3">
              {submissions.data.map((submission) => (
                <li key={submission.id} className="rounded-xl border border-slate-100 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-primary-800">{submission.status}</p>
                    {submission.points_awarded > 0 ? <Badge tone="accent">+{submission.points_awarded} pts</Badge> : null}
                  </div>
                  <p className="mt-1 whitespace-pre-line text-sm text-muted">{submission.summary}</p>
                  {submission.solution_url ? (
                    <a href={submission.solution_url} target="_blank" rel="noreferrer noopener" className="mt-1 inline-block text-xs text-primary-700 hover:underline">
                      {submission.solution_url}
                    </a>
                  ) : null}
                  {submission.review_note ? <p className="mt-1 text-xs text-muted">{submission.review_note}</p> : null}
                  {submission.status === "submitted" || submission.status === "under_review" ? (
                    <div className="mt-3 space-y-2">
                      <Input
                        value={reviewNote}
                        onChange={(event) => setReviewNote(event.target.value)}
                        placeholder={t("missions.reviewNote")}
                        aria-label={t("missions.reviewNote")}
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => review.mutate({ submissionId: submission.id, approve: true })} loading={review.isPending}>
                          {t("missions.approve")}
                        </Button>
                        <Button size="sm" variant="secondary" onClick={() => review.mutate({ submissionId: submission.id, approve: false })}>
                          {t("missions.reject")}
                        </Button>
                      </div>
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-muted">{t("missions.empty")}</p>
          )}
        </Card>
      ) : (
        <Card>
          <h2 className="text-sm font-semibold text-primary-800">{t("missions.submitTitle")}</h2>
          {!user ? (
            <div className="mt-3"><Alert tone="info">{t("common.loginRequired")}</Alert></div>
          ) : alreadySubmitted ? (
            <p className="mt-2 text-sm text-muted">{t("missions.alreadySubmitted")}</p>
          ) : (
            <form
              className="mt-4 space-y-3"
              onSubmit={(event) => {
                event.preventDefault();
                submit.mutate();
              }}
            >
              <Field label={t("missions.summary")} hint={t("missions.summaryHelp")} htmlFor="mission-summary">
                <Textarea id="mission-summary" rows={4} value={form.summary} onChange={(event) => setForm({ ...form, summary: event.target.value })} />
              </Field>
              <Field label={t("missions.solutionUrl")} htmlFor="mission-url">
                <Input id="mission-url" type="url" value={form.solution_url} onChange={(event) => setForm({ ...form, solution_url: event.target.value })} placeholder="https://github.com/…" />
              </Field>
              <Button type="submit" loading={submit.isPending} disabled={form.summary.trim().length < 30}>
                {t("missions.submit")}
              </Button>
            </form>
          )}
        </Card>
      )}
    </div>
  );
}
