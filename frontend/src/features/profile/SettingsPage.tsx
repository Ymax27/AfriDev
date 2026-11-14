import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LogOut } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Alert, Button, Card, CountrySelector, Field, Input, SkeletonList, Textarea } from "@/components/ui";
import { useCountries } from "@/hooks/useCountries";
import { usersApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import type { UserProfile } from "@/types/api";

const ROLE_OPTIONS = ["developer", "project_creator", "api_provider", "company"] as const;

function ProfileEditor({ profile, onSaved }: { profile: UserProfile; onSaved: () => void }) {
  const { t } = useTranslation();
  const { language } = useUiStore();
  const { data: countries } = useCountries();
  const { setUser } = useAuthStore();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    full_name: profile.full_name ?? "",
    bio: profile.bio ?? "",
    city: profile.city ?? "",
    country: profile.country?.code ?? "",
    website_url: profile.website_url ?? "",
    github_url: profile.github_url ?? "",
    skills: profile.skills.map((skill) => skill.name).join(", "),
    roles: profile.roles.map((role) => role.role),
  });

  const save = useMutation({
    mutationFn: () =>
      usersApi.updateMe({
        full_name: form.full_name || null,
        bio: form.bio || null,
        city: form.city || null,
        country_code: form.country || null,
        website_url: form.website_url || null,
        github_url: form.github_url || null,
        skills: form.skills.split(",").map((item) => item.trim()).filter(Boolean),
        roles: form.roles,
      }),
    onSuccess: (updated) => {
      setUser(updated);
      void queryClient.invalidateQueries({ queryKey: ["users", "me"] });
      void queryClient.invalidateQueries({ queryKey: ["auth"] });
      onSaved();
    },
  });

  return (
    <form
      className="space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        save.mutate();
      }}
    >
      <Card className="space-y-4">
        <h2 className="text-sm font-semibold text-primary-800">{t("settings.profileSection")}</h2>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("settings.fullName")} htmlFor="settings-name">
            <Input id="settings-name" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
          </Field>
          <Field label={t("settings.city")} htmlFor="settings-city">
            <Input id="settings-city" value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} />
          </Field>
        </div>

        <Field label={t("settings.bio")} htmlFor="settings-bio">
          <Textarea id="settings-bio" rows={4} value={form.bio} onChange={(event) => setForm({ ...form, bio: event.target.value })} />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("settings.country")} htmlFor="settings-country">
            <CountrySelector
              id="settings-country"
              countries={countries ?? []}
              value={form.country}
              onChange={(code) => setForm({ ...form, country: code })}
              language={language}
            />
          </Field>
          <Field label={t("settings.website")} htmlFor="settings-website">
            <Input id="settings-website" type="url" value={form.website_url} onChange={(event) => setForm({ ...form, website_url: event.target.value })} />
          </Field>
        </div>

        <Field label={t("settings.github")} htmlFor="settings-github">
          <Input id="settings-github" type="url" value={form.github_url} onChange={(event) => setForm({ ...form, github_url: event.target.value })} />
        </Field>

        <Field label={t("settings.skills")} hint={t("settings.skillsHelp")} htmlFor="settings-skills">
          <Input id="settings-skills" value={form.skills} onChange={(event) => setForm({ ...form, skills: event.target.value })} />
        </Field>

        <fieldset>
          <legend className="mb-1.5 text-sm font-medium text-primary-800">{t("settings.roles")}</legend>
          <p className="mb-2 text-xs text-muted">{t("settings.roleHelp")}</p>
          <div className="flex flex-wrap gap-2">
            {ROLE_OPTIONS.map((role) => {
              const checked = form.roles.includes(role);
              return (
                <label
                  key={role}
                  className={
                    checked
                      ? "cursor-pointer rounded-xl border border-accent-300 bg-accent-50 px-3 py-1.5 text-xs font-medium text-accent-700"
                      : "cursor-pointer rounded-xl border border-slate-300 px-3 py-1.5 text-xs font-medium text-muted"
                  }
                >
                  <input
                    type="checkbox"
                    className="sr-only"
                    checked={checked}
                    onChange={() =>
                      setForm({
                        ...form,
                        roles: checked ? form.roles.filter((item) => item !== role) : [...form.roles, role],
                      })
                    }
                  />
                  {t(`roles.${role}`, { defaultValue: role })}
                </label>
              );
            })}
          </div>
        </fieldset>

        <div className="flex justify-end">
          <Button type="submit" loading={save.isPending}>{t("common.save")}</Button>
        </div>
      </Card>
    </form>
  );
}

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const { language, setLanguage, lightweightMode, setLightweightMode } = useUiStore();
  const { user, logout } = useAuthStore();
  const [notice, setNotice] = useState<string | null>(null);

  const profile = useQuery({ queryKey: ["users", "me"], queryFn: usersApi.me });

  const changeLanguage = (next: "fr" | "en") => {
    setLanguage(next);
    void i18n.changeLanguage(next);
  };

  if (profile.isLoading) return <SkeletonList rows={4} />;

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={t("settings.title")} description={t("settings.subtitle")} />

      {notice ? <div className="mb-4"><Alert tone="success">{notice}</Alert></div> : null}

      {profile.data ? <ProfileEditor profile={profile.data} onSaved={() => setNotice(t("settings.saved"))} /> : null}

      <Card className="mt-5 space-y-4">
        <h2 className="text-sm font-semibold text-primary-800">{t("settings.language")}</h2>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant={language === "fr" ? "primary" : "secondary"} size="sm" onClick={() => changeLanguage("fr")}>
            {t("settings.french")}
          </Button>
          <Button variant={language === "en" ? "primary" : "secondary"} size="sm" onClick={() => changeLanguage("en")}>
            {t("settings.english")}
          </Button>
          <p className="text-xs text-muted">{t("settings.languageHelp")}</p>
        </div>

        <div className="border-t border-slate-100 pt-4">
          <h2 className="text-sm font-semibold text-primary-800">{t("settings.appearance")}</h2>
          <label className="mt-2 flex items-start gap-3 text-sm">
            <input
              type="checkbox"
              checked={lightweightMode}
              onChange={(event) => setLightweightMode(event.target.checked)}
              className="mt-1 size-4 accent-[#16a078]"
            />
            <span>
              <span className="block font-medium text-primary-800">{t("settings.lightweight")}</span>
              <span className="block text-xs text-muted">{t("settings.lightweightHelp")}</span>
            </span>
          </label>
        </div>

        <div className="border-t border-slate-100 pt-4">
          <h2 className="text-sm font-semibold text-primary-800">{t("settings.account")}</h2>
          <p className="mt-1 text-xs text-muted">
            @{user?.username} · {user?.is_demo ? t("settings.demoAccount") : "GitHub"}
          </p>
          <Button variant="secondary" className="mt-3" onClick={() => void logout()} icon={<LogOut className="size-4" aria-hidden="true" />}>
            {t("settings.logout")}
          </Button>
        </div>
      </Card>
    </div>
  );
}
