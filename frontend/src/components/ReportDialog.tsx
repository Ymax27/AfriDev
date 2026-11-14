import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation } from "@tanstack/react-query";

import { Button, Field, Modal, Select, Textarea } from "@/components/ui";
import { moderationApi } from "@/services/api";

const REASONS = ["spam", "misleading", "harassment", "copyright", "other"] as const;

export function ReportDialog({
  open,
  onClose,
  targetType,
  targetId,
}: {
  open: boolean;
  onClose: () => void;
  targetType: "project" | "problem" | "solution" | "field_report" | "message" | "user" | "mission";
  targetId: string;
}) {
  const { t } = useTranslation();
  const [reason, setReason] = useState<string>("spam");
  const [details, setDetails] = useState("");
  const [sent, setSent] = useState(false);

  const report = useMutation({
    mutationFn: () => moderationApi.report({ target_type: targetType, target_id: targetId, reason, details: details || null }),
    onSuccess: () => setSent(true),
  });

  const close = () => {
    setSent(false);
    setDetails("");
    onClose();
  };

  return (
    <Modal
      open={open}
      onClose={close}
      title={t("moderation.reportTitle")}
      closeLabel={t("common.close")}
      footer={
        sent ? (
          <Button onClick={close}>{t("common.close")}</Button>
        ) : (
          <>
            <Button variant="secondary" onClick={close}>
              {t("common.cancel")}
            </Button>
            <Button onClick={() => report.mutate()} loading={report.isPending}>
              {t("moderation.reportSubmit")}
            </Button>
          </>
        )
      }
    >
      {sent ? (
        <p className="text-sm text-muted">{t("moderation.reportThanks")}</p>
      ) : (
        <div className="space-y-4">
          <Field label={t("moderation.reason")} htmlFor="report-reason">
            <Select id="report-reason" value={reason} onChange={(event) => setReason(event.target.value)}>
              {REASONS.map((value) => (
                <option key={value} value={value}>
                  {t(`moderation.reasons.${value}`)}
                </option>
              ))}
            </Select>
          </Field>
          <Field label={t("moderation.details")} hint={t("moderation.detailsHelp")} htmlFor="report-details">
            <Textarea id="report-details" rows={3} value={details} onChange={(event) => setDetails(event.target.value)} />
          </Field>
          <p className="text-xs text-muted">{t("moderation.freezeNote")}</p>
        </div>
      )}
    </Modal>
  );
}
