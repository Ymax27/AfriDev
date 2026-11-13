import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquare, Send, Wifi, WifiOff } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Alert, Badge, Button, EmptyState, ErrorState, SkeletonList, Textarea } from "@/components/ui";
import { messagingApi } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { relativeTime } from "@/lib/utils";
import type { Message } from "@/types/api";

export default function MessagesPage() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const { language } = useUiStore();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const conversations = useQuery({ queryKey: ["conversations"], queryFn: () => messagingApi.conversations() });

  const activeId = selectedId ?? conversations.data?.items[0]?.id ?? null;

  const messages = useQuery({
    queryKey: ["messages", activeId],
    queryFn: () => messagingApi.messages(activeId ?? ""),
    enabled: Boolean(activeId),
  });

  useEffect(() => {
    if (!activeId) return;
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/conversations/${activeId}`);
    socketRef.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as { type: string; message?: Message };
        if (payload.type === "message.created" && payload.message) {
          const incoming = payload.message;
          queryClient.setQueryData<Message[]>(["messages", activeId], (current) => {
            if (!current) return [incoming];
            if (current.some((item) => item.id === incoming.id)) return current;
            return [...current, incoming];
          });
          void queryClient.invalidateQueries({ queryKey: ["conversations"] });
        }
      } catch {
        return;
      }
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [activeId, queryClient]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages.data]);

  const send = useMutation({
    mutationFn: (body: string) => messagingApi.send(activeId ?? "", body),
    onSuccess: (message) => {
      queryClient.setQueryData<Message[]>(["messages", activeId], (current) => (current ? [...current, message] : [message]));
      setDraft("");
      void queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  const handleSend = () => {
    const body = draft.trim();
    if (!body || !activeId) return;
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "message.send", body }));
      setDraft("");
    } else {
      send.mutate(body);
    }
  };

  const activeConversation = conversations.data?.items.find((item) => item.id === activeId);

  if (conversations.isLoading) return <SkeletonList rows={3} />;
  if (conversations.isError) {
    return <ErrorState message={t("errors.generic")} retryLabel={t("common.retry")} onRetry={() => void conversations.refetch()} />;
  }
  if (!conversations.data || conversations.data.items.length === 0) {
    return (
      <div>
        <PageHeader title={t("messages.title")} description={t("messages.subtitle")} />
        <EmptyState title={t("messages.empty")} description={t("messages.emptyHelp")} />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={t("messages.title")}
        description={t("messages.subtitle")}
        action={
          <Badge tone={connected ? "accent" : "neutral"}>
            {connected ? <Wifi className="size-3" aria-hidden="true" /> : <WifiOff className="size-3" aria-hidden="true" />}
            {connected ? t("messages.connected") : t("messages.disconnected")}
          </Badge>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
        <aside className="surface-card overflow-hidden p-0">
          <ul className="max-h-[60vh] divide-y divide-slate-100 overflow-y-auto">
            {conversations.data.items.map((conversation) => (
              <li key={conversation.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(conversation.id)}
                  aria-current={conversation.id === activeId}
                  className={
                    conversation.id === activeId
                      ? "w-full bg-primary-50 px-4 py-3 text-left"
                      : "w-full px-4 py-3 text-left hover:bg-slate-50"
                  }
                >
                  <span className="flex items-center gap-2">
                    <MessageSquare className="size-4 shrink-0 text-primary-600" aria-hidden="true" />
                    <span className="truncate text-sm font-medium text-primary-800">{conversation.title}</span>
                  </span>
                  <span className="mt-1 block text-xs text-muted">
                    {conversation.type === "contribution"
                      ? t("messages.contribution")
                      : conversation.type === "country"
                        ? t("messages.country")
                        : t("messages.mission")}{" "}
                    · {relativeTime(conversation.last_message_at, language)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="surface-card flex min-h-[60vh] flex-col p-0">
          <header className="border-b border-slate-100 px-4 py-3">
            <h2 className="text-sm font-semibold text-primary-800">{activeConversation?.title ?? t("messages.select")}</h2>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.isLoading ? (
              <SkeletonList rows={3} />
            ) : messages.data && messages.data.length > 0 ? (
              messages.data.map((message) => {
                const mine = message.sender_id === user?.id;
                return (
                  <div key={message.id} className={mine ? "flex justify-end" : "flex justify-start"}>
                    <div
                      className={
                        mine
                          ? "max-w-[80%] rounded-2xl rounded-br-sm bg-primary-700 px-4 py-2 text-sm text-white"
                          : "max-w-[80%] rounded-2xl rounded-bl-sm bg-slate-100 px-4 py-2 text-sm text-ink"
                      }
                    >
                      <p className="whitespace-pre-line">{message.body}</p>
                      <p className={mine ? "mt-1 text-[10px] text-primary-200" : "mt-1 text-[10px] text-muted"}>
                        {relativeTime(message.created_at, language)}
                      </p>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="py-10 text-center text-sm text-muted">{t("messages.noMessages")}</p>
            )}
            <div ref={bottomRef} />
          </div>

          {!connected ? (
            <div className="px-4 pb-2">
              <Alert tone="info">{t("messages.disconnected")} — HTTP</Alert>
            </div>
          ) : null}

          <form
            className="flex items-end gap-2 border-t border-slate-100 p-3"
            onSubmit={(event) => {
              event.preventDefault();
              handleSend();
            }}
          >
            <Textarea
              rows={2}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={t("messages.placeholder")}
              aria-label={t("messages.placeholder")}
              className="resize-none"
            />
            <Button type="submit" disabled={!draft.trim()} loading={send.isPending} icon={<Send className="size-4" aria-hidden="true" />}>
              {t("common.send")}
            </Button>
          </form>
        </section>
      </div>
    </div>
  );
}
