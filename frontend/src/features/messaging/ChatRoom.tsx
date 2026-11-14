import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Send, Wifi, WifiOff } from "lucide-react";

import { Alert, Button, Card } from "@/components/ui";
import { useAuthStore } from "@/stores/auth-store";

interface RoomEntry {
  id: string;
  author: string;
  body: string;
  mine: boolean;
}

export function ChatRoom({ roomPath, title, description }: { roomPath: string; title: string; description?: string }) {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [entries, setEntries] = useState<RoomEntry[]>([]);
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState<"idle" | "open" | "closed" | "error">("idle");
  const socketRef = useRef<WebSocket | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const connect = useCallback(() => {
    if (!user) return;
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}${roomPath}`);
    socketRef.current = socket;

    socket.onopen = () => setStatus("open");
    socket.onclose = () => setStatus("closed");
    socket.onerror = () => setStatus("error");
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as { type: string; author?: string; body?: string; members?: number };
        if (payload.type === "presence" && typeof payload.members === "number") {
          setEntries((current) => [
            ...current.slice(-49),
            { id: `presence-${Date.now()}`, author: "", body: t("rooms.presence", { count: payload.members }), mine: false },
          ]);
        }
        if (payload.type === "room.message" && payload.body) {
          setEntries((current) => [
            ...current.slice(-99),
            {
              id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
              author: payload.author ?? "?",
              body: payload.body ?? "",
              mine: payload.author === user.username,
            },
          ]);
        }
        if (payload.type === "error") {
          setEntries((current) => [
            ...current,
            { id: `error-${Date.now()}`, author: "", body: t("rooms.slowDown"), mine: false },
          ]);
        }
      } catch {
        /* ignore malformed frames */
      }
    };
  }, [roomPath, t, user]);

  useEffect(() => {
    connect();
    return () => {
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [connect]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [entries]);

  const send = () => {
    const body = draft.trim();
    if (!body || socketRef.current?.readyState !== WebSocket.OPEN) return;
    socketRef.current.send(JSON.stringify({ type: "message.send", body }));
    setDraft("");
  };

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-primary-800">{title}</h2>
          {description ? <p className="text-xs text-muted">{description}</p> : null}
        </div>
        <span className="inline-flex items-center gap-1 text-xs text-muted">
          {status === "open" ? (
            <>
              <Wifi className="size-3.5 text-accent-600" aria-hidden="true" /> {t("rooms.connected")}
            </>
          ) : (
            <>
              <WifiOff className="size-3.5" aria-hidden="true" /> {t("rooms.disconnected")}
            </>
          )}
        </span>
      </div>

      {!user ? (
        <div className="mt-3">
          <Alert tone="info">{t("common.loginRequired")}</Alert>
        </div>
      ) : (
        <>
          <div
            ref={listRef}
            className="mt-3 h-56 space-y-2 overflow-y-auto rounded-xl bg-slate-50 p-3"
            aria-live="polite"
            aria-label={title}
          >
            {entries.length === 0 ? (
              <p className="text-xs text-muted">{t("rooms.empty")}</p>
            ) : (
              entries.map((entry) => (
                <p key={entry.id} className="text-sm">
                  {entry.author ? (
                    <span className={entry.mine ? "font-semibold text-accent-700" : "font-semibold text-primary-700"}>
                      @{entry.author}{" "}
                    </span>
                  ) : null}
                  <span className={entry.author ? "text-ink" : "text-xs italic text-muted"}>{entry.body}</span>
                </p>
              ))
            )}
          </div>

          <div className="mt-3 flex items-end gap-2">
            <label className="flex-1">
              <span className="sr-only">{t("rooms.placeholder")}</span>
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    send();
                  }
                }}
                rows={1}
                maxLength={2000}
                placeholder={t("rooms.placeholder")}
                className="w-full resize-none rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-100"
              />
            </label>
            <Button
              type="button"
              onClick={send}
              disabled={!draft.trim() || status !== "open"}
              icon={<Send className="size-4" aria-hidden="true" />}
            >
              {t("rooms.send")}
            </Button>
          </div>
          <p className="mt-2 text-xs text-muted">{t("rooms.rules")}</p>
        </>
      )}
    </Card>
  );
}
