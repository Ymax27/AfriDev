import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { z } from "zod";

import { PageHeader } from "@/components/layout/PageHeader";
import { Alert, Button, CountrySelector, Field, Input, Select, Textarea } from "@/components/ui";
import { useCountries } from "@/hooks/useCountries";
import { knowledgeApi } from "@/services/api";
import { useUiStore } from "@/stores/ui-store";

const schema = z.object({
  title: z.string().min(8).max(200),
  description: z.string().min(30).max(8000),
  category: z.string().min(2),
  technology: z.string().optional(),
  country: z.string().optional(),
  code_snippet: z.string().optional(),
  documentation_links: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

const CATEGORIES = ["payments", "authentication", "sms", "kyc", "mapping", "offline", "performance", "localization"];

export default function CreateProblemPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { language } = useUiStore();
  const { data: countries } = useCountries();
  const { register, handleSubmit, setValue, watch, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { category: "payments" },
  });

  const create = useMutation({
    mutationFn: (values: FormValues) =>
      knowledgeApi.create({
        title: values.title,
        description: values.description,
        category: values.category,
        technology: values.technology || null,
        country_code: values.country || null,
        code_snippet: values.code_snippet || null,
        documentation_links: (values.documentation_links ?? "").split("\n").map((line) => line.trim()).filter(Boolean),
      }),
    onSuccess: (problem) => navigate(`/knowledge/${problem.id}`),
  });

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={t("knowledge.createTitle")} description={t("knowledge.createSubtitle")} />

      <form className="space-y-5" onSubmit={handleSubmit((values) => create.mutate(values))} noValidate>
        {create.isError ? <Alert tone="error">{t("errors.validation")}</Alert> : null}

        <div className="surface-card space-y-4 p-5">
          <Field label={t("knowledge.titleLabel")} error={errors.title?.message} htmlFor="problem-title">
            <Input id="problem-title" {...register("title")} placeholder={t("knowledge.titlePlaceholder")} />
          </Field>

          <Field label={t("knowledge.description")} error={errors.description?.message} htmlFor="problem-description">
            <Textarea id="problem-description" rows={6} {...register("description")} placeholder={t("knowledge.descriptionPlaceholder")} />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={t("knowledge.category")} htmlFor="problem-category">
              <Select id="problem-category" {...register("category")}>
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </Select>
            </Field>
            <Field label={t("knowledge.technology")} htmlFor="problem-technology">
              <Input id="problem-technology" {...register("technology")} placeholder={t("knowledge.technologyPlaceholder")} />
            </Field>
          </div>

          <Field label={t("knowledge.country")} htmlFor="problem-country">
            <CountrySelector
              id="problem-country"
              countries={countries ?? []}
              value={watch("country")}
              onChange={(code) => setValue("country", code)}
              language={language}
            />
          </Field>

          <Field label={t("knowledge.codeSnippet")} hint={t("common.optional")} htmlFor="problem-code">
            <Textarea id="problem-code" rows={5} className="font-mono" {...register("code_snippet")} />
          </Field>

          <Field label={t("knowledge.documentationLinks")} hint={t("knowledge.documentationHelp")} htmlFor="problem-links">
            <Textarea id="problem-links" rows={3} {...register("documentation_links")} placeholder="https://…" />
          </Field>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={() => navigate(-1)}>{t("common.cancel")}</Button>
          <Button type="submit" loading={isSubmitting || create.isPending}>{t("knowledge.publish")}</Button>
        </div>
      </form>
    </div>
  );
}
