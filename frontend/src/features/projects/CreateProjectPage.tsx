import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { z } from "zod";

import { PageHeader } from "@/components/layout/PageHeader";
import { Alert, Button, CountrySelector, Field, Input, Select, Textarea } from "@/components/ui";
import { useCountries } from "@/hooks/useCountries";
import { projectsApi } from "@/services/api";
import { useUiStore } from "@/stores/ui-store";

const schema = z.object({
  name: z.string().min(3, "3 caractères minimum").max(120),
  description: z.string().min(30, "30 caractères minimum").max(4000),
  category: z.string().min(1),
  collaboration_mode: z.enum(["showcase", "feedback", "open_to_contributors"]),
  country: z.string().optional(),
  technologies: z.string().min(1),
  repository_url: z.string().url().optional().or(z.literal("")),
  demo_url: z.string().url().optional().or(z.literal("")),
});

type FormValues = z.infer<typeof schema>;

const CATEGORIES = ["fintech", "health", "education", "agriculture", "logistics", "civic_tech", "developer_tools", "energy"];

export default function CreateProjectPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { language } = useUiStore();
  const { data: countries } = useCountries();
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { collaboration_mode: "open_to_contributors", category: "fintech" },
  });

  const create = useMutation({
    mutationFn: (values: FormValues) =>
      projectsApi.create({
        name: values.name,
        description: values.description,
        category: values.category,
        collaboration_mode: values.collaboration_mode,
        country_code: values.country || null,
        technologies: values.technologies.split(",").map((item) => item.trim()).filter(Boolean),
        repository_url: values.repository_url || null,
        demo_url: values.demo_url || null,
      }),
    onSuccess: (project) => navigate(`/projects/${project.id}`),
  });

  const mode = watch("collaboration_mode");

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={t("project.createTitle")} description={t("project.createSubtitle")} />

      <form
        className="space-y-5"
        onSubmit={handleSubmit((values) => create.mutate(values))}
        noValidate
      >
        {create.isError ? <Alert tone="error">{t("errors.validation")}</Alert> : null}

        <div className="surface-card space-y-4 p-5">
          <Field label={t("project.name")} error={errors.name?.message} htmlFor="project-name">
            <Input id="project-name" {...register("name")} placeholder={t("project.namePlaceholder")} />
          </Field>

          <Field label={t("project.description")} error={errors.description?.message} htmlFor="project-description">
            <Textarea id="project-description" rows={5} {...register("description")} placeholder={t("project.descriptionPlaceholder")} />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={t("project.category")} error={errors.category?.message} htmlFor="project-category">
              <Select id="project-category" {...register("category")}>
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>{category.replaceAll("_", " ")}</option>
                ))}
              </Select>
            </Field>
            <Field label={t("project.country")} htmlFor="project-country">
              <CountrySelector
                id="project-country"
                countries={countries ?? []}
                value={watch("country")}
                onChange={(code) => setValue("country", code)}
                language={language}
              />
            </Field>
          </div>

          <Field label={t("project.mode")} hint={t("project.modeHelp")} htmlFor="project-mode">
            <Select id="project-mode" {...register("collaboration_mode")}>
              {(["showcase", "feedback", "open_to_contributors"] as const).map((item) => (
                <option key={item} value={item}>{t(`modes.${item}.title`)} — {t(`modes.${item}.text`)}</option>
              ))}
            </Select>
          </Field>
          <p className="rounded-xl bg-primary-50 px-3 py-2 text-xs text-primary-700">{t(`modes.${mode}.text`)}</p>

          <Field label={t("project.technologies")} hint={t("project.technologiesHelp")} error={errors.technologies?.message} htmlFor="project-tech">
            <Input id="project-tech" {...register("technologies")} placeholder="React, FastAPI, PostgreSQL" />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={t("project.repositoryUrl")} error={errors.repository_url?.message} htmlFor="project-repo">
              <Input id="project-repo" type="url" {...register("repository_url")} placeholder="https://github.com/…" />
            </Field>
            <Field label={t("project.demoUrl")} error={errors.demo_url?.message} htmlFor="project-demo">
              <Input id="project-demo" type="url" {...register("demo_url")} placeholder="https://…" />
            </Field>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={() => navigate(-1)}>{t("common.cancel")}</Button>
          <Button type="submit" loading={isSubmitting || create.isPending}>{t("common.submit")}</Button>
        </div>
      </form>
    </div>
  );
}
