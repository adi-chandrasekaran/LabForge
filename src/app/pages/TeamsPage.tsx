import { useEffect, useMemo, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { Hash, ImagePlus, MessageSquare, Plus, Send, Users, X } from "lucide-react";
import {
  createChatChannel,
  createChatMessage,
  fetchChatChannels,
  fetchChatMessages,
  fetchExperimentReferenceOptions,
  fetchWorkflowReferenceOptions,
  uploadChatMessageAttachment,
  type ChatChannelRecord,
  type ChatMessageRecord,
  type ReferenceOptionRecord,
} from "../api";

function formatTimestamp(value?: string) {
  if (!value) {
    return "No activity yet";
  }
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

const inputCls =
  "w-full bg-secondary border border-border text-[11px] font-mono text-foreground rounded-sm px-2 py-1.5 focus:outline-none focus:border-[#00c9a7]/50 placeholder:text-muted-foreground/40";

export default function TeamsPage() {
  const [channels, setChannels] = useState<ChatChannelRecord[]>([]);
  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageRecord[]>([]);
  const [workflowOptions, setWorkflowOptions] = useState<ReferenceOptionRecord[]>([]);
  const [experimentOptions, setExperimentOptions] = useState<ReferenceOptionRecord[]>([]);
  const [loadingChannels, setLoadingChannels] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [channelDialogOpen, setChannelDialogOpen] = useState(false);
  const [creatingChannel, setCreatingChannel] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [channelForm, setChannelForm] = useState({ name: "", topic: "" });
  const [messageForm, setMessageForm] = useState({
    body: "",
    workflowId: "",
    experimentId: "",
  });
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  const selectedChannel = useMemo(
    () => channels.find((channel) => channel.id === selectedChannelId) ?? null,
    [channels, selectedChannelId],
  );

  useEffect(() => {
    let cancelled = false;

    async function loadTeamsPage() {
      try {
        setLoadingChannels(true);
        setError(null);
        const [nextChannels, nextWorkflowOptions, nextExperimentOptions] = await Promise.all([
          fetchChatChannels(),
          fetchWorkflowReferenceOptions(),
          fetchExperimentReferenceOptions(),
        ]);
        if (cancelled) {
          return;
        }
        setChannels(nextChannels);
        setSelectedChannelId((current) => current ?? nextChannels[0]?.id ?? null);
        setWorkflowOptions(nextWorkflowOptions);
        setExperimentOptions(nextExperimentOptions);
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load teams");
        }
      } finally {
        if (!cancelled) {
          setLoadingChannels(false);
        }
      }
    }

    void loadTeamsPage();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadMessages() {
      if (!selectedChannelId) {
        setMessages([]);
        return;
      }

      try {
        setLoadingMessages(true);
        setError(null);
        const nextMessages = await fetchChatMessages(selectedChannelId);
        if (!cancelled) {
          setMessages(nextMessages);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load channel messages");
        }
      } finally {
        if (!cancelled) {
          setLoadingMessages(false);
        }
      }
    }

    void loadMessages();
    return () => {
      cancelled = true;
    };
  }, [selectedChannelId]);

  async function handleCreateChannel() {
    if (!channelForm.name.trim()) {
      return;
    }

    try {
      setCreatingChannel(true);
      setError(null);
      const created = await createChatChannel({
        name: channelForm.name.trim(),
        topic: channelForm.topic.trim(),
      });
      setChannels((current) => [created, ...current]);
      setSelectedChannelId(created.id);
      setChannelDialogOpen(false);
      setChannelForm({ name: "", topic: "" });
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Failed to create channel");
    } finally {
      setCreatingChannel(false);
    }
  }

  async function handleSendMessage() {
    if (!selectedChannelId || !messageForm.body.trim()) {
      return;
    }

    try {
      setSendingMessage(true);
      setError(null);
      let created = await createChatMessage(selectedChannelId, {
        body: messageForm.body.trim(),
        referencedWorkflowId: messageForm.workflowId || undefined,
        referencedExperimentId: messageForm.experimentId || undefined,
      });
      if (pendingFile) {
        const attachment = await uploadChatMessageAttachment(selectedChannelId, created.id, pendingFile);
        created = { ...created, attachments: [...created.attachments, attachment] };
      }
      setMessages((current) => [...current, created]);
      setChannels((current) =>
        current.map((channel) =>
          channel.id === selectedChannelId
            ? {
                ...channel,
                messageCount: channel.messageCount + 1,
                lastMessagePreview: created.body.slice(0, 120),
                lastMessageAt: created.createdAt,
              }
            : channel,
        ),
      );
      setMessageForm({ body: "", workflowId: "", experimentId: "" });
      setPendingFile(null);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Failed to send message");
    } finally {
      setSendingMessage(false);
    }
  }

  return (
    <div className="min-h-full bg-background px-7 py-7" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
        <div>
          <div className="text-[9px] font-mono tracking-[0.25em] text-muted-foreground mb-1">LAB DISPATCH</div>
          <h1 className="text-xl font-mono font-semibold text-foreground">Teams & Chats</h1>
          <p className="text-[10px] font-mono text-muted-foreground mt-1">
            Local lab channels for workflows, experiments, and troubleshooting notes.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setChannelDialogOpen(true)}
          data-testid="open-new-channel"
          className="flex items-center gap-2 bg-[#00c9a7] hover:bg-[#00b899] text-[#080c12] text-[10px] font-mono font-semibold px-3 py-2 rounded-sm transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          NEW CHANNEL
        </button>
      </div>

      {error && (
        <div className="border border-red-400/25 rounded-sm bg-red-400/10 px-4 py-4 mb-5">
          <div className="text-[10px] font-mono text-red-300">Teams API error</div>
          <div className="text-[10px] font-mono text-red-200/80 mt-1 break-words">{error}</div>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[320px_minmax(0,1fr)] gap-4">
        <aside className="border border-border rounded-sm bg-card min-h-[680px]">
          <div className="px-4 py-4 border-b border-border">
            <div className="flex items-center gap-2 text-[10px] font-mono text-foreground">
              <Users className="w-3.5 h-3.5 text-[#00c9a7]" />
              LAB CHANNELS
            </div>
            <div className="text-[9px] font-mono text-muted-foreground mt-1">
              {channels.length} channel{channels.length !== 1 ? "s" : ""} available
            </div>
          </div>
          <div className="p-2 space-y-2">
            {loadingChannels ? (
              <div className="px-3 py-3 text-[10px] font-mono text-muted-foreground">Loading channels...</div>
            ) : channels.length === 0 ? (
              <div className="px-3 py-6 text-center">
                <Hash className="w-5 h-5 text-muted-foreground mx-auto mb-2" />
                <div className="text-[10px] font-mono text-muted-foreground">No channels yet.</div>
              </div>
            ) : (
              channels.map((channel) => {
                const active = channel.id === selectedChannelId;
                return (
                  <button
                    key={channel.id}
                    type="button"
                    onClick={() => setSelectedChannelId(channel.id)}
                    data-testid={`channel-${channel.id}`}
                    className={`w-full text-left border rounded-sm px-3 py-3 transition-colors ${
                      active
                        ? "border-[#00c9a7]/30 bg-[#00c9a7]/10"
                        : "border-border bg-background hover:bg-secondary"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 text-[11px] font-mono text-foreground">
                          <Hash className="w-3 h-3 text-[#00c9a7]" />
                          <span className="truncate">{channel.name}</span>
                        </div>
                        <div className="text-[9px] font-mono text-muted-foreground mt-1 line-clamp-2">
                          {channel.topic || "No topic set."}
                        </div>
                      </div>
                      <div className="text-[8px] font-mono text-muted-foreground">{channel.messageCount}</div>
                    </div>
                    <div className="text-[8px] font-mono text-muted-foreground mt-2">
                      {formatTimestamp(channel.lastMessageAt)}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </aside>

        <section className="border border-border rounded-sm bg-card min-h-[680px] flex flex-col">
          <div className="px-5 py-4 border-b border-border">
            {selectedChannel ? (
              <>
                <div className="flex items-center gap-2 text-[11px] font-mono text-foreground">
                  <MessageSquare className="w-3.5 h-3.5 text-[#00c9a7]" />
                  <span>#{selectedChannel.name}</span>
                </div>
                <div className="text-[10px] font-mono text-muted-foreground mt-1">
                  {selectedChannel.topic || "No topic set for this channel."}
                </div>
              </>
            ) : (
              <div className="text-[10px] font-mono text-muted-foreground">Choose or create a channel to begin.</div>
            )}
          </div>

          <div className="flex-1 px-5 py-5 space-y-3 overflow-y-auto">
            {!selectedChannel ? (
              <div className="h-full flex items-center justify-center text-[10px] font-mono text-muted-foreground">
                No channel selected.
              </div>
            ) : loadingMessages ? (
              <div className="text-[10px] font-mono text-muted-foreground">Loading messages...</div>
            ) : messages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-[10px] font-mono text-muted-foreground">
                No messages in this channel yet.
              </div>
            ) : (
              messages.map((message) => (
                <article key={message.id} className="border border-border rounded-sm bg-background px-4 py-3">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <div className="text-[10px] font-mono text-foreground">
                        {message.authorDisplayName || "Unknown author"}
                      </div>
                      <div className="text-[8px] font-mono text-muted-foreground mt-0.5">
                        {formatTimestamp(message.createdAt)}
                      </div>
                    </div>
                    {(message.referencedWorkflowTitle || message.referencedExperimentTitle) && (
                      <div className="flex flex-wrap gap-1 justify-end">
                        {message.referencedWorkflowTitle && (
                          <span className="text-[8px] font-mono text-cyan-300 border border-cyan-400/20 bg-cyan-400/10 px-1.5 py-0.5 rounded-sm">
                            workflow · {message.referencedWorkflowTitle}
                          </span>
                        )}
                        {message.referencedExperimentTitle && (
                          <span className="text-[8px] font-mono text-violet-300 border border-violet-400/20 bg-violet-400/10 px-1.5 py-0.5 rounded-sm">
                            experiment · {message.referencedExperimentTitle}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <p className="text-[10px] font-mono text-foreground/90 whitespace-pre-wrap leading-relaxed">
                    {message.body}
                  </p>

                  {message.attachments.length > 0 && (
                    <div className="flex flex-wrap gap-3 mt-3">
                      {message.attachments.map((attachment) => (
                        <a
                          key={attachment.id}
                          href={attachment.downloadUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="border border-border rounded-sm overflow-hidden bg-card hover:border-[#00c9a7]/30 transition-colors"
                        >
                          <img
                            src={attachment.downloadUrl}
                            alt={attachment.filename}
                            className="w-28 h-28 object-cover block"
                          />
                          <div className="px-2 py-1 text-[8px] font-mono text-muted-foreground truncate max-w-28">
                            {attachment.filename}
                          </div>
                        </a>
                      ))}
                    </div>
                  )}
                </article>
              ))
            )}
          </div>

          <div className="border-t border-border px-5 py-4">
            <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_180px_180px] gap-2 mb-2">
              <textarea
                data-testid="chat-message-body"
                className={inputCls + " min-h-[96px] resize-none"}
                placeholder="Post a lab update, troubleshooting note, or workflow observation..."
                value={messageForm.body}
                onChange={(event) => setMessageForm((current) => ({ ...current, body: event.target.value }))}
                disabled={!selectedChannel || sendingMessage}
              />
              <select
                data-testid="chat-workflow-reference"
                className={inputCls}
                value={messageForm.workflowId}
                onChange={(event) => setMessageForm((current) => ({ ...current, workflowId: event.target.value }))}
                disabled={!selectedChannel || sendingMessage}
              >
                <option value="">Reference workflow</option>
                {workflowOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
              <select
                data-testid="chat-experiment-reference"
                className={inputCls}
                value={messageForm.experimentId}
                onChange={(event) => setMessageForm((current) => ({ ...current, experimentId: event.target.value }))}
                disabled={!selectedChannel || sendingMessage}
              >
                <option value="">Reference experiment</option>
                {experimentOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center justify-between gap-3 flex-wrap">
              <label className="flex items-center gap-2 text-[10px] font-mono text-muted-foreground cursor-pointer">
                <span className="inline-flex items-center gap-1 border border-border rounded-sm px-2 py-1 hover:bg-secondary transition-colors">
                  <ImagePlus className="w-3 h-3" />
                  ATTACH IMAGE
                </span>
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml"
                  className="hidden"
                  data-testid="chat-attachment-input"
                  onChange={(event) => setPendingFile(event.target.files?.[0] ?? null)}
                  disabled={!selectedChannel || sendingMessage}
                />
                <span>{pendingFile?.name ?? "Optional"}</span>
              </label>

              <button
                type="button"
                onClick={() => void handleSendMessage()}
                data-testid="chat-send-message"
                disabled={!selectedChannel || !messageForm.body.trim() || sendingMessage}
                className="flex items-center gap-2 bg-[#00c9a7] hover:bg-[#00b899] disabled:opacity-40 text-[#080c12] text-[10px] font-mono font-semibold px-3 py-2 rounded-sm transition-colors"
              >
                <Send className="w-3.5 h-3.5" />
                {sendingMessage ? "POSTING..." : "POST MESSAGE"}
              </button>
            </div>
          </div>
        </section>
      </div>

      <Dialog.Root open={channelDialogOpen} onOpenChange={setChannelDialogOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
          <Dialog.Content
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[420px] max-w-[95vw] bg-background border border-border rounded-sm shadow-2xl p-5"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="text-xs font-mono text-foreground font-medium">NEW CHANNEL</div>
              <button type="button" onClick={() => setChannelDialogOpen(false)}>
                <X className="w-3.5 h-3.5 text-muted-foreground" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">CHANNEL NAME *</div>
                <input
                  data-testid="new-channel-name"
                  className={inputCls}
                  placeholder="e.g. anc2-troubleshooting"
                  value={channelForm.name}
                  onChange={(event) => setChannelForm((current) => ({ ...current, name: event.target.value }))}
                />
              </div>
              <div>
                <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">TOPIC</div>
                <textarea
                  data-testid="new-channel-topic"
                  className={inputCls + " min-h-[72px] resize-none"}
                  placeholder="What should this channel be used for?"
                  value={channelForm.topic}
                  onChange={(event) => setChannelForm((current) => ({ ...current, topic: event.target.value }))}
                />
              </div>
              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setChannelDialogOpen(false)}
                  className="flex-1 text-[10px] font-mono text-muted-foreground border border-border rounded-sm py-1.5 hover:bg-secondary transition-colors"
                >
                  CANCEL
                </button>
                <button
                  type="button"
                  disabled={!channelForm.name.trim() || creatingChannel}
                  onClick={() => void handleCreateChannel()}
                  data-testid="confirm-create-channel"
                  className="flex-1 text-[10px] font-mono text-[#080c12] bg-[#00c9a7] hover:bg-[#00b899] disabled:opacity-40 rounded-sm py-1.5 font-semibold transition-colors"
                >
                  {creatingChannel ? "CREATING..." : "CREATE CHANNEL"}
                </button>
              </div>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
