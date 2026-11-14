import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, BadgeCheck, Flag, Info } from "lucide-react";

import { ReportDialog } from "@/components/ReportDialog";
import { Alert, Badge, Button, Card, ErrorState, SkeletonList, Textarea } from "@/components/ui";
import { fieldReportsApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { formatDate } from "@/lib/utils";

export default function FieldReportDetailsPage() {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [comment, setComment] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [reportOpen, setReportOpen] = useState(false);

  const report = useQuery({ queryKey: ["field-report", id], queryFn: () => fieldReportsApi.get(id) });
  const confirm = useMutation({
    mutationFn: () => fieldReportsApi.confirm(id, comment || undefined),
    onSuccess: () => {
      setNotice(t("fieldReports.confirmed"));
      setComment("");
      void queryClient.invalidateQueries({ queryKey: ["field-report", id] });
    },
  });

  if (report.isLoading) return <SkeletonList rows={4} />;
  if (report.isError || !report.data) {
    return <ErrorState message={t("errors.notFound")} retryLabel={t("common.retry")} onRetry={() => void report.refetch()} />;
  }

  const data = report.data;
  const sameCountry = Boolean(user?.country && data.country && user.country.code === data.country.code);

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/field-reports" className="mb-4 inline-flex items-center gap-1 text-sm text-muted hover:text-primary-700">
        <ArrowLeft className="size-4" aria-hidden="true" /> {t("common.back")}
      </Link>

      {notice ? <div className="mb-4"><Alert tone="success">{notice}</Alert></div> : null}

      <header className="surface-card mb-5 p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={data.status === "confirmed" ? "accent" : "primary"}>{data.status.replaceAll("_", " ")}</Badge>
          {data.country ? (
            <Badge tone="neutral">{data.country.flag_emoji ?? ""} {language === "fr" ? data.country.name_fr : data.country.name}</Badge>
          ) : null}
          {user ? (
            <Button variant="ghost" size="sm" className="ml-auto" onClick={() => setReportOpen(true)} icon={<Flag className="size-4" aria-hidden="true" />}>
              {t("common.report")}
            </Button>
          ) : null}
        </div>
        <h1 className="mt-3 text-2xl font-bold text-primary-800">{data.title}</h1>
        <p className="mt-1 text-xs text-muted">
          @{data.author.username} · {formatDate(data.created_at, language)} · {data.confirmation_count} {t("fieldReports.confirmations")}
        </p>
        <p className="mt-4 whitespace-pre-line text-sm leading-relaxed">{data.problem_summary}</p>
      </header>

      <div className="space-y-4">
        <Card>
          <h2 className="text-sm font-semibold text-primary-800">{t("fieldReports.solutionLabel")}</h2>
          <p className="mt-2 whitespace-pre-line text-sm leading-relaxed">{data.solution_summary}</p>
        </Card>

        {data.common_errors ? (
          <Card>
            <h2 className="text-sm font-semibold text-primary-800">{t("fieldReports.commonErrors")}</h2>
            <p className="mt-2 whitespace-pre-line text-sm text-muted">{data.common_errors}</p>
          </Card>
        ) : null}

        {data.workarounds ? (
          <Card>
            <h2 className="text-sm font-semibold text-primary-800">{t("fieldReports.workarounds")}</h2>
            <p className="mt-2 whitespace-pre-line text-sm text-muted">{data.workarounds}</p>
          </Card>
        ) : null}

        <Card>
          <div className="flex items-start gap-2 rounded-xl bg-primary-50 p-3 text-xs text-primary-700">
            <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            {t("fieldReports.validationInfo")}
          </div>
          {data.problem_id ? (
            <Link to={`/knowledge/${data.problem_id}`} className="mt-3 inline-block text-sm font-medium text-primary-700 hover:underline">
              {t("fieldReports.linkedProblem")}
            </Link>
          ) : null}
        </Card>

        <Card>
          <h2 className="flex items-center gap-2 text-sm font-semibold text-primary-800">
            <BadgeCheck className="size-4 text-accent-600" aria-hidden="true" /> {t("fieldReports.confirm")}
          </h2>
          {!user ? (
            <div className="mt-3"><Alert tone="info">{t("common.loginRequired")}</Alert></div>
          ) : !sameCountry ? (
            <p className="mt-2 text-sm text-muted">{t("fieldReports.confirmRequiresCountry")}</p>
          ) : (
            <form
              className="mt-3 space-y-3"
              onSubmit={(event) => {
                event.preventDefault();
                confirm.mutate();
              }}
            >
              <Textarea
                rows={3}
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                aria-label={t("project.message")}
                placeholder={t("project.message")}
              />
              <Button type="submit" loading={confirm.isPending}>{t("fieldReports.confirm")}</Button>
            </form>
          )}
        </Card>
      </div>

      <ReportDialog open={reportOpen} onClose={() => setReportOpen(false)} targetType="field_report" targetId={id} />
    </div>
  );
}
