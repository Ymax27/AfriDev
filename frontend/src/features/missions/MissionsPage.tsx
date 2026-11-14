import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, Gift, Plus } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import {
  Badge,
  Button,
  Card,
  CountrySelector,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  Pagination,
  SearchBar,
  Select,
  SkeletonList,
  TechnologyTag,
  Textarea,
} from "@/components/ui";
import { useCountries } from "@/hooks/useCountries";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { missionsApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { formatDate, truncate } from "@/lib/utils";

const STATUS_TONE: Record<string, "accent" | "primary" | "highlight" | "neutral"> = {
  published: "accent",
  in_progress: "primary",
  submitted: "highlight",
  under_review: "highlight",
  approved: "accent",
  completed: "neutral",
};

export default function MissionsPage() {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [draft, setDraft] = useState({
    title: "",
    description: "",
    objectives: "",
    reward_description: "",
    required_skills: "",
    country_code: "",
  });
  const debounced = useDebouncedValue(query);
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const { data: countries } = useCountries();
  const canPublish = Boolean(
    user &&
      (user.is_admin || user.roles.some((role) => ["api_provider", "company", "sponsor"].includes(role.role))),
  );

  const createMission = useMutation({
    mutationFn: () =>
      missionsApi.create({
        title: draft.title,
        description: draft.description,
        objectives: draft.objectives,
        reward_description: draft.reward_description || null,
        required_skills: draft.required_skills.split(",").map((item) => item.trim()).filter(Boolean),
        country_code: draft.country_code || null,
      }),
    onSuccess: () => {
      setCreateOpen(false);
      setDraft({ title: "", description: "", objectives: "", reward_description: "", required_skills: "", country_code: "" });
      void queryClient.invalidateQueries({ queryKey: ["missions"] });
    },
  });

  const missions = useQuery({
    queryKey: ["missions", { q: debounced, status, page }],
    queryFn: () => missionsApi.list({ q: debounced || undefined, status: status || undefined, page, page_size: 9 }),
  });

  return (
    <div>
      <PageHeader title={t("missions.title")} description={t("missions.subtitle")} />

      {canPublish ? (
        <div className="mb-4 flex justify-end">
          <Button onClick={() => setCreateOpen(true)} icon={<Plus className="size-4" aria-hidden="true" />}>
            {t("missions.publishMission")}
          </Button>
        </div>
      ) : null}

      <div className="mb-5 flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <SearchBar
            label={t("common.search")}
            value={query}
            onChange={(value) => {
              setQuery(value);
              setPage(1);
            }}
            placeholder={t("missions.searchPlaceholder")}
          />
        </div>
        <label className="sm:w-52">
          <Select
            aria-label={t("missions.statusPublished")}
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
          >
            <option value="">{t("common.all")}</option>
            <option value="published">{t("missions.statusPublished")}</option>
            <option value="in_progress">{t("missions.statusInProgress")}</option>
            <option value="under_review">{t("missions.statusUnderReview")}</option>
            <option value="completed">{t("missions.statusCompleted")}</option>
          </Select>
        </label>
      </div>

      {missions.isLoading ? (
        <SkeletonList rows={4} />
      ) : missions.isError ? (
        <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void missions.refetch()} />
      ) : missions.data && missions.data.items.length > 0 ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {missions.data.items.map((mission) => (
              <Card key={mission.id} className="flex h-full flex-col gap-3">
                <div className="flex items-start justify-between gap-2">
                  <h2 className="text-base font-semibold text-primary-800">
                    <Link to={`/missions/${mission.id}`} className="hover:underline">{mission.title}</Link>
                  </h2>
                  <Badge tone={STATUS_TONE[mission.status] ?? "neutral"}>
                    {t(`missions.status${mission.status.split("_").map((part) => part[0]?.toUpperCase() + part.slice(1)).join("")}`, { defaultValue: mission.status })}
                  </Badge>
                </div>
                <p className="text-sm text-muted">{truncate(mission.description, 150)}</p>
                <div className="flex flex-wrap gap-1.5">
                  {mission.required_skills.slice(0, 3).map((skill) => (
                    <TechnologyTag key={skill}>{skill}</TechnologyTag>
                  ))}
                </div>
                <dl className="mt-auto space-y-1 text-xs text-muted">
                  <div className="flex items-center gap-1">
                    <Gift className="size-3.5" aria-hidden="true" /> {t("missions.reward")} : {mission.reward_description ?? `${mission.reward_points} ${t("missions.points")}`}
                  </div>
                  <div className="flex items-center gap-1">
                    <CalendarClock className="size-3.5" aria-hidden="true" /> {t("missions.deadline")} : {formatDate(mission.deadline, language)}
                  </div>
                  <div>
                    {t("missions.sponsor")} : @{mission.sponsor.username} · {mission.submissions_count} {t("missions.submissions")}
                  </div>
                </dl>
                <Link to={`/missions/${mission.id}`} className="text-sm font-medium text-primary-700 hover:underline">
                  {t("project.viewProject")}
                </Link>
              </Card>
            ))}
          </div>
          <Pagination
            page={missions.data.page}
            pageSize={missions.data.page_size}
            total={missions.data.total}
            onChange={setPage}
            labels={{ previous: t("common.previous"), next: t("common.next"), page: t("common.page") }}
          />
        </>
      ) : (
        <EmptyState title={t("missions.empty")} />
      )}

      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title={t("missions.publishMission")}
        closeLabel={t("common.close")}
        footer={
          <>
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>{t("common.cancel")}</Button>
            <Button
              onClick={() => createMission.mutate()}
              loading={createMission.isPending}
              disabled={draft.title.trim().length < 8 || draft.description.trim().length < 30 || draft.objectives.trim().length < 20}
            >
              {t("missions.publish")}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label={t("missions.formTitle")} htmlFor="mission-title">
            <Input id="mission-title" value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} />
          </Field>
          <Field label={t("missions.formDescription")} htmlFor="mission-description">
            <Textarea id="mission-description" rows={4} value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} />
          </Field>
          <Field label={t("missions.objectives")} htmlFor="mission-objectives">
            <Textarea id="mission-objectives" rows={3} value={draft.objectives} onChange={(event) => setDraft({ ...draft, objectives: event.target.value })} />
          </Field>
          <Field label={t("missions.skills")} hint={t("missions.skillsHelp")} htmlFor="mission-skills">
            <Input id="mission-skills" value={draft.required_skills} onChange={(event) => setDraft({ ...draft, required_skills: event.target.value })} />
          </Field>
          <Field label={t("missions.reward")} htmlFor="mission-reward">
            <Input id="mission-reward" value={draft.reward_description} onChange={(event) => setDraft({ ...draft, reward_description: event.target.value })} />
          </Field>
          <Field label={t("leaderboard.country")} htmlFor="mission-country">
            <CountrySelector
              id="mission-country"
              countries={countries ?? []}
              value={draft.country_code}
              onChange={(code) => setDraft({ ...draft, country_code: code })}
              includeAll
              allLabel={t("common.all")}
              language={language}
            />
          </Field>
          <p className="text-xs text-muted">{t("missions.manualReviewNote")}</p>
        </div>
      </Modal>
    </div>
  );
}
