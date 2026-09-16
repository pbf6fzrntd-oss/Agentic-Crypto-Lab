"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowUpRight,
  Bot,
  BriefcaseBusiness,
  Check,
  Clock3,
  Database,
  Download,
  Filter,
  Flame,
  Inbox,
  LayoutDashboard,
  Loader2,
  RefreshCcw,
  Search,
  Sparkles,
  Target,
  ThumbsDown,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { PIPELINE_STAGES, type Lead, type PipelineStage } from "@/lib/scoring";

interface LeadsResponse {
  leads: Lead[];
  isoWeek: string;
  addedThisWeek: number;
  weeklyTarget: number;
  lastRun: { runAt: string; added: number; queried: number; errors: string[] } | null;
}

const stageLabel: Record<PipelineStage, string> = Object.fromEntries(
  PIPELINE_STAGES.map((s) => [s.value, s.label])
) as Record<PipelineStage, string>;

export default function Home() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [meta, setMeta] = useState<Omit<LeadsResponse, "leads"> | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [drawer, setDrawer] = useState(true);
  const [highFitOnly, setHighFitOnly] = useState(false);
  const [noteDraft, setNoteDraft] = useState("");

  const loadLeads = useCallback(async () => {
    const res = await fetch("/api/leads", { cache: "no-store" });
    const data = (await res.json()) as LeadsResponse;
    setLeads(data.leads);
    setMeta({
      isoWeek: data.isoWeek,
      addedThisWeek: data.addedThisWeek,
      weeklyTarget: data.weeklyTarget,
      lastRun: data.lastRun,
    });
    setSelectedId((current) => current ?? data.leads[0]?.id ?? null);
  }, []);

  useEffect(() => {
    loadLeads().finally(() => setLoading(false));
  }, [loadLeads]);

  const thisWeekLeads = useMemo(
    () => (meta ? leads.filter((l) => l.weekAdded === meta.isoWeek) : leads),
    [leads, meta]
  );

  const visible = useMemo(
    () =>
      thisWeekLeads.filter(
        (l) =>
          (filter === "all" || l.discovery === filter) &&
          (!highFitOnly || l.fit >= 85) &&
          (l.company.toLowerCase().includes(query.toLowerCase()) ||
            l.focus.toLowerCase().includes(query.toLowerCase()))
      ),
    [thisWeekLeads, filter, highFitOnly, query]
  );

  const selected = useMemo(
    () => leads.find((l) => l.id === selectedId) ?? null,
    [leads, selectedId]
  );

  useEffect(() => {
    setNoteDraft(selected?.notes ?? "");
    // Intentionally only reset the draft when the *selection* changes, not
    // on every notes update (which includes our own optimistic saves).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected?.id]);

  const signalCount = thisWeekLeads.filter((l) => l.discovery === "signal").length;
  const prospectCount = thisWeekLeads.filter((l) => l.discovery === "prospect").length;
  const highFitCount = thisWeekLeads.filter((l) => l.fit >= 85).length;
  const activeCount = leads.filter((l) => l.stage !== "won" && l.stage !== "lost").length;
  const wonCount = leads.filter((l) => l.stage === "won").length;

  const patchLead = useCallback(
    async (id: string, patch: { stage?: PipelineStage; notes?: string }) => {
      setLeads((cur) => cur.map((l) => (l.id === id ? { ...l, ...patch } : l)));
      const res = await fetch(`/api/leads/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!res.ok) {
        toast.error("Couldn't save that change");
        await loadLeads();
      }
    },
    [loadLeads]
  );

  const setStage = (id: string, stage: PipelineStage) => {
    patchLead(id, { stage });
    toast.success(`Moved to "${stageLabel[stage]}"`);
  };

  const saveNotes = () => {
    if (!selected) return;
    patchLead(selected.id, { notes: noteDraft });
    toast.success("Notes saved");
  };

  const runRefresh = async () => {
    setRefreshing(true);
    toast.loading("Pulling this week's leads from the CMS NPI registry…", { id: "run" });
    try {
      const res = await fetch("/api/leads/refresh", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Refresh failed");
      await loadLeads();
      if (data.run.added === 0 && data.run.errors.length > 0) {
        toast.error(`Refresh hit an error: ${data.run.errors[0]}`, { id: "run" });
      } else if (data.run.added === 0) {
        toast.success("Already at this week's target — no new leads to add", { id: "run" });
      } else {
        toast.success(`Added ${data.run.added} new lead${data.run.added === 1 ? "" : "s"}`, {
          id: "run",
        });
      }
    } catch (err) {
      toast.error(`Couldn't reach the data feed: ${(err as Error).message}`, { id: "run" });
    } finally {
      setRefreshing(false);
    }
  };

  const exportCsv = () => {
    const rows = [
      ["Company", "City", "State", "Discovery", "Fit", "Signal", "Keena service", "Stage"],
      ...visible.map((l) => [
        l.company,
        l.city,
        l.state,
        l.discovery,
        String(l.fit),
        l.signal,
        l.focus,
        stageLabel[l.stage],
      ]),
    ];
    const csv = rows
      .map((r) => r.map((v) => `"${v.replaceAll('"', '""')}"`).join(","))
      .join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "keena-weekly-leads.csv";
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Lead queue exported");
  };

  const copyBrief = async () => {
    if (!selected) return;
    await navigator.clipboard.writeText(
      `${selected.company} (${selected.city}, ${selected.state})\nNPI ${selected.npiNumber}\nFit: ${selected.fit}/100\nSignal: ${selected.signal}\nKeena fit: ${selected.focus}\n\n${noteDraft}`
    );
    toast.success("Lead brief copied");
  };

  return (
    <div className="min-h-screen bg-[#f5f6f7] text-[#222]">
      <Toaster position="top-right" richColors />
      <header className="topbar">
        <div className="brand-lockup" aria-label="Keena Growth Operations">
          <span className="brand-mark">
            <span>K</span>
          </span>
          <div>
            <strong>KEENA</strong>
            <small>GROWTH OPS</small>
          </div>
        </div>
        <nav className="topnav" aria-label="Primary navigation">
          <button className="active" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
            <LayoutDashboard />
            Command center
          </button>
          <button onClick={() => document.getElementById("lead-queue")?.scrollIntoView({ behavior: "smooth" })}>
            <Target />
            Pipeline
          </button>
          <button onClick={() => document.getElementById("feed-info")?.scrollIntoView({ behavior: "smooth" })}>
            <Bot />
            Data feed
          </button>
        </nav>
        <div className="top-actions">
          <span className="live-pill">
            <i />
            {loading ? "Loading…" : `${meta?.addedThisWeek ?? 0}/${meta?.weeklyTarget ?? 15} this week`}
          </span>
          <Button className="avatar" aria-label="Account menu">
            KH
          </Button>
        </div>
      </header>
      <main className="shell">
        <section className="intro">
          <div>
            <p className="eyebrow">
              {meta?.isoWeek ?? "…"} · LIVE FEED — CMS NPI REGISTRY
            </p>
            <h1>Your weekly growth briefing</h1>
            <p>Up to 15 real healthcare provider leads a week, sourced and scored automatically.</p>
          </div>
          <div className="intro-actions">
            <Button variant="outline" onClick={exportCsv}>
              <Download />
              Export CSV
            </Button>
            <Button className="run-button" onClick={runRefresh} disabled={refreshing}>
              {refreshing ? <Loader2 className="animate-spin" /> : <RefreshCcw />}
              {refreshing ? "Refreshing…" : "Refresh this week"}
            </Button>
          </div>
        </section>
        <section className="kpis" aria-label="Weekly lead metrics">
          <article>
            <div className="metric-icon red">
              <Target />
            </div>
            <div>
              <span>This week&apos;s leads</span>
              <strong>{meta?.addedThisWeek ?? 0}</strong>
              <small>
                of <b>{meta?.weeklyTarget ?? 15}</b> weekly target
              </small>
            </div>
          </article>
          <article>
            <div className="metric-icon amber">
              <Flame />
            </div>
            <div>
              <span>High intent</span>
              <strong>{highFitCount}</strong>
              <small>Fit score 85 or above</small>
            </div>
          </article>
          <article>
            <div className="metric-icon blue">
              <Inbox />
            </div>
            <div>
              <span>Signal / prospect</span>
              <strong>
                {signalCount} <em>/</em> {prospectCount}
              </strong>
              <small>Recent activity vs. ICP match</small>
            </div>
          </article>
          <article>
            <div className="metric-icon dark">
              <Clock3 />
            </div>
            <div>
              <span>Active pipeline</span>
              <strong>{activeCount}</strong>
              <small>{wonCount} won all-time</small>
            </div>
          </article>
        </section>
        <section className="workspace" id="lead-queue">
          <div className="queue-panel">
            <div className="panel-head">
              <div>
                <h2>This week&apos;s lead queue</h2>
                <p>Ranked by fit, real-world signal, and taxonomy match</p>
              </div>
              <div className="queue-actions">
                <label className="searchbox">
                  <Search />
                  <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search leads" />
                </label>
                <Button
                  variant={highFitOnly ? "secondary" : "outline"}
                  className="filter-btn"
                  onClick={() => setHighFitOnly((v) => !v)}
                >
                  <Filter />
                  {highFitOnly ? "High fit on" : "High fit"}
                </Button>
              </div>
            </div>
            <Tabs value={filter} onValueChange={setFilter} className="lead-tabs">
              <TabsList>
                <TabsTrigger value="all">All {thisWeekLeads.length}</TabsTrigger>
                <TabsTrigger value="signal">Signal {signalCount}</TabsTrigger>
                <TabsTrigger value="prospect">Prospect {prospectCount}</TabsTrigger>
              </TabsList>
            </Tabs>
            <Table className="lead-table">
              <TableHeader>
                <TableRow>
                  <TableHead>ACCOUNT</TableHead>
                  <TableHead>DISCOVERY</TableHead>
                  <TableHead>FIT</TableHead>
                  <TableHead>WHY NOW</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {visible.map((l) => (
                  <TableRow
                    key={l.id}
                    data-state={selected?.id === l.id ? "selected" : undefined}
                    onClick={() => {
                      setSelectedId(l.id);
                      setDrawer(true);
                    }}
                    className="cursor-pointer"
                  >
                    <TableCell>
                      <div className="account">
                        <span className="company-avatar">{l.initials}</span>
                        <div>
                          <strong>{l.company}</strong>
                          <span>
                            {l.city ? `${l.city}, ${l.state}` : l.location}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={`source ${l.discovery === "signal" ? "inbound" : "outbound"}`}>
                        {l.discovery === "signal" ? "Signal" : "Prospect"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="fit-cell">
                        <strong>{l.fit}</strong>
                        <Progress value={l.fit} />
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="signal">
                        <strong>{l.signal}</strong>
                        <span>{l.focus}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {l.stage === "won" ? (
                        <span className="approved">
                          <Check />
                          Won
                        </span>
                      ) : l.stage === "lost" ? (
                        <span className="rejected">
                          <ThumbsDown />
                          Lost
                        </span>
                      ) : (
                        <span className="stage-pill">{stageLabel[l.stage]}</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {!loading && visible.length === 0 && (
              <div className="empty-state">
                <Search />
                <strong>No leads match</strong>
                <span>
                  {thisWeekLeads.length === 0
                    ? "No leads yet this week — click Refresh this week to pull real data."
                    : "Clear the search or high-fit filter."}
                </span>
              </div>
            )}
            <div className="table-foot">
              <span>Showing {visible.length} of {thisWeekLeads.length} leads this week</span>
              <span>{leads.length} total in pipeline</span>
            </div>
          </div>
          <aside className={`detail-panel ${drawer && selected ? "open" : "closed"}`} aria-label="Selected lead details">
            {selected && (
              <>
                <div className="detail-head">
                  <p>LEAD BRIEF</p>
                  <button onClick={() => setDrawer(false)} aria-label="Close lead details">
                    <X />
                  </button>
                </div>
                <div className="detail-company">
                  <span className="company-avatar large">{selected.initials}</span>
                  <div>
                    <h2>{selected.company}</h2>
                    <p>
                      {selected.city ? `${selected.city}, ${selected.state}` : selected.location} · NPI {selected.npiNumber}
                    </p>
                  </div>
                </div>
                <div className="score-block">
                  <div>
                    <span>KEENA FIT SCORE</span>
                    <strong>
                      {selected.fit}
                      <small>/100</small>
                    </strong>
                  </div>
                  <Progress value={selected.fit} />
                </div>
                <div className="brief-section">
                  <h3>Why this account, why now</h3>
                  <p>
                    {selected.company} is a real CMS-registered provider organization matching{" "}
                    <strong>{selected.focus}</strong>. Matched taxonomy: {selected.matchedTaxonomy}.
                    Signal: <strong>{selected.signal.toLowerCase()}</strong>.
                  </p>
                </div>
                <div className="brief-section">
                  <h3>Pipeline stage</h3>
                  <div className="stage-grid">
                    {PIPELINE_STAGES.map((s) => (
                      <button
                        key={s.value}
                        className={`stage-chip ${selected.stage === s.value ? "active" : ""}`}
                        onClick={() => setStage(selected.id, s.value)}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="brief-section">
                  <h3>Source record</h3>
                  <div className="buyer-card">
                    <BriefcaseBusiness />
                    <div>
                      <strong>CMS NPI Registry</strong>
                      <span>Public organizational NPI record #{selected.npiNumber}</span>
                    </div>
                  </div>
                </div>
                <div className="brief-section">
                  <h3>Research notes</h3>
                  <textarea
                    className="notes"
                    value={noteDraft}
                    onChange={(e) => setNoteDraft(e.target.value)}
                    onBlur={saveNotes}
                    placeholder="Add qualification notes, objections, or next steps…"
                  />
                </div>
                <div className="detail-actions three">
                  <Button onClick={() => setStage(selected.id, "won")} disabled={selected.stage === "won"}>
                    <Check />
                    Won
                  </Button>
                  <Button variant="outline" onClick={() => setStage(selected.id, "lost")}>
                    <ThumbsDown />
                    Lost
                  </Button>
                  <Button variant="outline" onClick={copyBrief}>
                    <ArrowUpRight />
                    Copy brief
                  </Button>
                </div>
              </>
            )}
          </aside>
        </section>
        <section className="agent-section" id="feed-info">
          <div className="agent-heading">
            <div>
              <p className="eyebrow">HOW THIS FEED WORKS</p>
              <h2>A real data feed, not a demo.</h2>
            </div>
            <p>
              <Database />
              Last run: {meta?.lastRun ? new Date(meta.lastRun.runAt).toLocaleString() : "never"}
            </p>
          </div>
          <div className="agent-grid">
            <article className="chief">
              <div className="agent-top">
                <span className="agent-icon">
                  <Sparkles />
                </span>
                <span className="agent-status">
                  <i />
                  {meta?.addedThisWeek ?? 0}/{meta?.weeklyTarget ?? 15} added this week
                </span>
              </div>
              <h3>Weekly cadence</h3>
              <p>A scheduled job tops the pipeline up to 15 new leads every week and never repeats a lead.</p>
            </article>
            <article>
              <div className="agent-top">
                <span className="agent-icon">
                  <Database />
                </span>
                <span className="agent-status">Live</span>
              </div>
              <h3>CMS NPI Registry</h3>
              <p>Official, free, public U.S. government registry of real healthcare provider organizations.</p>
            </article>
            <article>
              <div className="agent-top">
                <span className="agent-icon">
                  <Target />
                </span>
                <span className="agent-status">Scored</span>
              </div>
              <h3>ICP taxonomy match</h3>
              <p>Each org&apos;s registered taxonomy is matched to a Keena service line for a fit score.</p>
            </article>
            <article>
              <div className="agent-top">
                <span className="agent-icon">
                  <Flame />
                </span>
                <span className="agent-status">Signal</span>
              </div>
              <h3>Recency signal</h3>
              <p>Recently registered or updated NPI records surface first as timelier signal leads.</p>
            </article>
          </div>
        </section>
      </main>
    </div>
  );
}
