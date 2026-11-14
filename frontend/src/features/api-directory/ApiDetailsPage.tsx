import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink, Pencil } from "lucide-react";

import { Badge, Button, Card, ErrorState, Field, Input, Modal, Select, SkeletonList, Textarea } from "@/components/ui";
import { apisDirectoryApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";

const STATUS_TONE: Record<string, "accent" | "highlight" | "danger"> = {
  operational: "accent",
  degraded: "highlight",
  maintenance: "danger",
};

const STATUSES = ["operational", "degraded", "maintenance"] as const;

export default function ApiDetailsPage() {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const entry = useQuery({ queryKey: ["api", id], queryFn: () => apisDirectoryApi.get(id) });
  const [editOpen, setEditOpen] = useState(false);
  const [form, setForm] = useState({ description: "", pricing: "", api_status: "operational", integration_notes: "" });

  const update = useMutation({
    mutationFn: () =>
      apisDirectoryApi.update(id, {
        description: form.description,
        pricing: form.pricing || null,
        api_status: form.api_status,
        integration_notes: form.integration_notes || null,
      }),
    onSuccess: () => {
      setEditOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["api", id] });
      void queryClient.invalidateQueries({ queryKey: ["apis"] });
    },
  });

  if (entry.isLoading) return <SkeletonList rows={3} />;
  if (entry.isError || !entry.data) {
    return <ErrorState message={t("errors.notFound")} retryLabel={t("common.retry")} onRetry={() => void entry.refetch()} />;
  }

  const data = entry.data;
  const canEdit = Boolean(user && (user.is_admin || (data.owner_id && data.owner_id === user.id)));

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/api-directory" className="mb-4 inline-flex items-center gap-1 text-sm text-muted hover:text-primary-700">
        <ArrowLeft className="size-4" aria-hidden="true" /> {t("common.back")}
      </Link>

      <header className="surface-card mb-5 p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="primary">{t(`apis.categories.${data.category}`, { defaultValue: data.category })}</Badge>
          <Badge tone={STATUS_TONE[data.api_status] ?? "neutral"}>{t(`apis.${data.api_status}`, { defaultValue: data.api_status })}</Badge>
          {canEdit ? (
            <Button
              size="sm"
              variant="secondary"
              className="ml-auto"
              onClick={() => {
                setForm({
                  description: data.description,
                  pricing: data.pricing ?? "",
                  api_status: data.api_status,
                  integration_notes: data.integration_notes ?? "",
                });
                setEditOpen(true);
              }}
              icon={<Pencil className="size-3.5" aria-hidden="true" />}
            >
              {t("common.edit")}
            </Button>
          ) : null}
        </div>
        <h1 className="mt-3 text-2xl font-bold text-primary-800">{data.name}</h1>
        <p className="mt-1 text-sm text-muted">{t("apis.provider")} : {data.provider_name}</p>
        <p className="mt-4 whitespace-pre-line text-sm leading-relaxed">{data.description}</p>

        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
          <a href={data.documentation_url} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-1 text-primary-700 hover:underline">
            <ExternalLink className="size-4" aria-hidden="true" /> {t("apis.viewDocs")}
          </a>
          {data.pricing ? <span className="text-muted">{t("apis.pricing")} : {data.pricing}</span> : null}
        </div>
      </header>

      <div className="space-y-4">
        <Card>
          <h2 className="text-sm font-semibold text-primary-800">{t("apis.countries")}</h2>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {data.countries.length > 0 ? data.countries.map((code) => (
              <Badge key={code} tone="neutral">{code}</Badge>
            )) : <p className="text-sm text-muted">—</p>}
          </div>
        </Card>

        {data.integration_notes ? (
          <Card>
            <h2 className="text-sm font-semibold text-primary-800">{t("apis.integrationNotes")}</h2>
            <p className="mt-2 whitespace-pre-line text-sm text-muted">{data.integration_notes}</p>
          </Card>
        ) : null}

        <Card>
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-primary-800">{t("apis.relatedReports")}</h2>
            <Badge tone="accent">{data.related_field_reports}</Badge>
          </div>
          <Link to="/field-reports" className="mt-2 inline-block text-sm font-medium text-primary-700 hover:underline">
            {t("landing.statsReports")}
          </Link>
        </Card>
      </div>

      <Modal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        title={t("apis.editTitle")}
        closeLabel={t("common.close")}
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditOpen(false)}>{t("common.cancel")}</Button>
            <Button onClick={() => update.mutate()} loading={update.isPending}>{t("common.save")}</Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label={t("apis.description")} htmlFor="api-edit-description">
            <Textarea id="api-edit-description" rows={4} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          </Field>
          <Field label={t("apis.pricing")} htmlFor="api-edit-pricing">
            <Input id="api-edit-pricing" value={form.pricing} onChange={(event) => setForm({ ...form, pricing: event.target.value })} />
          </Field>
          <Field label={t("apis.status")} htmlFor="api-edit-status">
            <Select id="api-edit-status" value={form.api_status} onChange={(event) => setForm({ ...form, api_status: event.target.value })}>
              {STATUSES.map((status) => (
                <option key={status} value={status}>{t(`apis.${status}`)}</option>
              ))}
            </Select>
          </Field>
          <Field label={t("apis.integrationNotes")} htmlFor="api-edit-notes">
            <Textarea id="api-edit-notes" rows={3} value={form.integration_notes} onChange={(event) => setForm({ ...form, integration_notes: event.target.value })} />
          </Field>
        </div>
      </Modal>
    </div>
  );
}
