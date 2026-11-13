import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, ExternalLink } from "lucide-react";

import {
  Alert,
  Avatar,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  Input,
  SkeletonList,
  TechnologyTag,
  Textarea,
} from "@/components/ui";
import { knowledgeApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { formatDate } from "@/lib/utils";

export default function ProblemDetailsPage() {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ explanation: "", code_snippet: "", implementation_steps: "", references: "" });
  const [notice, setNotice] = useState<string | null>(null);

  const problem = useQuery({ queryKey: ["knowledge", id], queryFn: () => knowledgeApi.get(id) });

  const addSolution = useMutation({
    mutationFn: () =>
      knowledgeApi.addSolution(id, {
        explanation: form.explanation,
        code_snippet: form.code_snippet || null,
        implementation_steps: form.implementation_steps || null,
        references: form.references.split("\n").map((line) => line.trim()).filter(Boolean),
      }),
    onSuccess: () => {
      setForm({ explanation: "", code_snippet: "", implementation_steps: "", references: "" });
      setNotice(t("knowledge.created"));
      void queryClient.invalidateQueries({ queryKey: ["knowledge", id] });
    },
  });

  const acceptSolution = useMutation({
    mutationFn: (solutionId: string) => knowledgeApi.acceptSolution(id, solutionId),
    onSuccess: () => {
      setNotice(t("project.accepted"));
      void queryClient.invalidateQueries({ queryKey: ["knowledge", id] });
    },
  });

  if (problem.isLoading) return <SkeletonList rows={4} />;
  if (problem.isError || !problem.data) {
    return <ErrorState message={t("errors.notFound")} retryLabel={t("common.retry")} onRetry={() => void problem.refetch()} />;
  }

  const data = problem.data;
  const isAuthor = user?.username === data.author.username;

  return (
    <div className="mx-auto max-w-4xl">
      <Link to="/knowledge" className="mb-4 inline-flex items-center gap-1 text-sm text-muted hover:text-primary-700">
        <ArrowLeft className="size-4" aria-hidden="true" /> {t("common.back")}
      </Link>

      {notice ? <div className="mb-4"><Alert tone="success">{notice}</Alert></div> : null}

      <header className="surface-card mb-5 p-6">
        <div className="flex flex-wrap items-center gap-2">
          <TechnologyTag>{data.category}</TechnologyTag>
          {data.technology ? <TechnologyTag>{data.technology}</TechnologyTag> : null}
          {data.has_accepted_solution ? <Badge tone="accent"><CheckCircle2 className="size-3" aria-hidden="true" /> {t("knowledge.accepted")}</Badge> : null}
        </div>
        <h1 className="mt-3 text-2xl font-bold text-primary-800">{data.title}</h1>
        <p className="mt-1 text-xs text-muted">
          {t("knowledge.askedOn")} {formatDate(data.created_at, language)} · @{data.author.username}
          {data.country ? ` · ${data.country.flag_emoji ?? ""} ${language === "fr" ? data.country.name_fr : data.country.name}` : ""}
        </p>
        <p className="mt-4 whitespace-pre-line text-sm leading-relaxed">{data.description}</p>

        {data.code_snippet ? (
          <pre className="prose-code mt-4"><code>{data.code_snippet}</code></pre>
        ) : null}

        {data.documentation_links.length > 0 ? (
          <ul className="mt-4 space-y-1 text-sm">
            {data.documentation_links.map((link) => (
              <li key={link}>
                <a href={link} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-1 text-primary-700 hover:underline">
                  <ExternalLink className="size-3.5" aria-hidden="true" /> {link}
                </a>
              </li>
            ))}
          </ul>
        ) : null}
      </header>

      <section className="mb-5">
        <h2 className="mb-3 text-lg font-semibold text-primary-800">{t("knowledge.solutions")} ({data.solutions.length})</h2>
        {data.solutions.length === 0 ? (
          <EmptyState title={t("knowledge.noSolutions")} description={t("knowledge.noSolutionsHelp")} />
        ) : (
          <ul className="space-y-3">
            {data.solutions.map((solution) => (
              <li key={solution.id}>
                <Card className={solution.is_accepted ? "border-accent-300 bg-accent-50/30" : undefined}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <Avatar name={solution.author.full_name ?? solution.author.username} src={solution.author.avatar_url} size={32} />
                      <div>
                        <p className="text-sm font-medium text-primary-800">@{solution.author.username}</p>
                        <p className="text-xs text-muted">{formatDate(solution.created_at, language)}</p>
                      </div>
                    </div>
                    {solution.is_accepted ? <Badge tone="accent">{t("knowledge.accepted")}</Badge> : null}
                  </div>

                  <p className="mt-3 whitespace-pre-line text-sm leading-relaxed">{solution.explanation}</p>
                  {solution.implementation_steps ? (
                    <p className="mt-3 whitespace-pre-line rounded-xl bg-slate-50 p-3 text-sm text-muted">{solution.implementation_steps}</p>
                  ) : null}
                  {solution.code_snippet ? <pre className="prose-code mt-3"><code>{solution.code_snippet}</code></pre> : null}
                  {solution.references.length > 0 ? (
                    <ul className="mt-3 space-y-1 text-xs">
                      {solution.references.map((reference) => (
                        <li key={reference}>
                          <a href={reference} target="_blank" rel="noreferrer noopener" className="text-primary-700 hover:underline">{reference}</a>
                        </li>
                      ))}
                    </ul>
                  ) : null}

                  {isAuthor && !solution.is_accepted && !data.has_accepted_solution ? (
                    <div className="mt-4">
                      <Button size="sm" onClick={() => acceptSolution.mutate(solution.id)} loading={acceptSolution.isPending}>
                        {t("knowledge.accept")}
                      </Button>
                      <p className="mt-1 text-xs text-muted">{t("knowledge.fieldReportNote")}</p>
                    </div>
                  ) : null}
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <Card>
          <h2 className="text-base font-semibold text-primary-800">{t("knowledge.submitSolution")}</h2>
          {!user ? (
            <div className="mt-3">
              <Alert tone="info">
                {t("common.loginRequired")} <Link to="/login" className="font-medium underline">{t("nav.login")}</Link>
              </Alert>
            </div>
          ) : (
            <form
              className="mt-4 space-y-4"
              onSubmit={(event) => {
                event.preventDefault();
                addSolution.mutate();
              }}
            >
              <Field label={t("knowledge.explanation")} hint={t("knowledge.explanationHelp")} htmlFor="solution-explanation">
                <Textarea id="solution-explanation" rows={4} value={form.explanation} onChange={(event) => setForm({ ...form, explanation: event.target.value })} />
              </Field>
              <Field label={t("knowledge.steps")} htmlFor="solution-steps">
                <Textarea id="solution-steps" rows={3} value={form.implementation_steps} onChange={(event) => setForm({ ...form, implementation_steps: event.target.value })} />
              </Field>
              <Field label={t("knowledge.code")} htmlFor="solution-code">
                <Textarea id="solution-code" rows={5} className="font-mono" value={form.code_snippet} onChange={(event) => setForm({ ...form, code_snippet: event.target.value })} />
              </Field>
              <Field label={t("knowledge.references")} htmlFor="solution-references">
                <Input id="solution-references" value={form.references} onChange={(event) => setForm({ ...form, references: event.target.value })} />
              </Field>
              <Button type="submit" loading={addSolution.isPending} disabled={form.explanation.trim().length < 30}>
                {t("common.submit")}
              </Button>
            </form>
          )}
        </Card>
      </section>
    </div>
  );
}
