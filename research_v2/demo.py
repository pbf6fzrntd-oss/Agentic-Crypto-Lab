"""Deterministic fixture replay and escaped static cockpit. No live provider calls."""
import argparse
from datetime import datetime,timedelta,timezone
import html
import json
from pathlib import Path
import tempfile
from .engine import Engine,MANIFEST,canonical,fingerprint

ROOT=Path(__file__).resolve().parents[1]
def snapshots():
    start=datetime(2026,9,1,tzinfo=timezone.utc)
    result=[]
    for last_day in [2,3,8]:
        observed=start+timedelta(days=last_day,minutes=1 if last_day!=2 else 720)
        markets={ticker:{'provider_symbol':symbol,'source':'FIXTURE:deterministic-example','bars':[{'start':(start+timedelta(days=i)).isoformat(),'open':(100 if ticker=='BTC-USD' else 50)+i} for i in range(last_day+1)]} for ticker,symbol in MANIFEST['symbols'].items()}
        thesis={'BTC-USD':{'direction':'LONG','confidence':0.6,'reasoning':'Fixed demonstration thesis, not an edge claim.','source':'FIXTURE:manual-example','completed_at':observed.isoformat(),'input_cutoff':(start+timedelta(days=last_day-1)).isoformat()}} if last_day==2 else {}
        result.append({'observed_at':observed.isoformat(),'evidence_class':'DEMO_FIXED','interval':'1d','markets':markets,'theses':thesis})
    return result

def cockpit(rows,historical):
    esc=lambda value:html.escape(str(value))
    cards=[]
    for row in rows:
        details=esc(json.dumps(row,indent=2,sort_keys=True))
        cards.append(f'<article data-cohort="v2"><h2>{esc(row["ticker"])} · {esc(row["state"])}</h2><p>{esc(row["evidence_class"])} / {esc(row["methodology"])}</p><p>Input cutoff: {esc(row["input_cutoff"])}<br>Thesis complete: {esc(row["thesis_completed_at"])}<br>Decision formed: {esc(row["decision_formed_at"])}<br>Credited fill: {esc(row.get("entry_date"))}<br>Interval: {esc(row["interval"])} · Hold: {row["holding_period_bars"]} bars · Round-trip cost: {row["round_trip_cost_bps"]} bps</p><p>{esc(row["risk_reason"])}</p><details><summary>Snapshot, thesis and outcome lineage</summary><pre>{details}</pre></details></article>')
    for row in historical:
        entry=row.get('entry_date');run=row.get('run_timestamp');problem='Unverified legacy timing / interval / benchmark lineage'
        try:
            from .engine import timestamp
            if entry and timestamp(entry if 'T' in entry or ' ' in entry else entry+'T00:00:00+00:00')<timestamp(run):problem='Credited fill precedes recorded run; exclude from v2 chronology claims'
        except (ValueError,TypeError):pass
        cards.append(f'<article data-cohort="legacy"><h2>{esc(row.get("ticker"))} · frozen historical row</h2><p>{esc(row.get("data_source"))} / {esc(row.get("thesis_source"))}</p><p>{esc(problem)}</p><p>Signal: {esc(row.get("signal_date"))} · Run: {esc(run)} · Fill: {esc(entry)}</p><details><summary>Original immutable record</summary><pre>{esc(json.dumps(row,indent=2,sort_keys=True))}</pre></details></article>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Crypto Lab research cockpit</title><style>body{font:17px system-ui;max-width:1100px;margin:auto;padding:24px;background:#111c29;color:#e1ecf1}article{border:1px solid #456;padding:20px;margin:18px 0;border-radius:12px}input,select{padding:12px;margin:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}summary{cursor:pointer}</style><h1>Crypto Lab research cockpit</h1><p>Read-only deterministic replay and frozen historical evidence. No live market refresh, billed thesis call or order execution. Demo results are not investment performance or new experiment evidence.</p><p>V2 waits for a bar opening strictly after decision formation, stores interval/holding policy, freezes basket components, settles mature positions before new exposure, and deduplicates economic decisions transactionally. Snapshot paper inputs remain operator supplied and unverified.</p><label>Cohort <select id="cohort"><option value="v2">Version 2</option><option value="legacy">Frozen historical rows</option><option value="">Both (separate labels)</option></select></label><label>Ticker / state search <input id="search" type="search"></label><p id="status" role="status"></p>'''+''.join(cards)+'''<script>const cohort=document.getElementById('cohort'),search=document.getElementById('search');function filter(){let n=0;document.querySelectorAll('article').forEach(a=>{a.hidden=(cohort.value&&a.dataset.cohort!==cohort.value)||!a.textContent.toLowerCase().includes(search.value.toLowerCase());if(!a.hidden)n++;});document.getElementById('status').textContent=n+' records shown';}cohort.onchange=search.oninput=filter;filter();</script></html>'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'.demo'/'cockpit');ap.add_argument('--snapshot',type=Path);ap.add_argument('--database',type=Path);ap.add_argument('--historical',type=Path,default=ROOT/'output'/'decision_journal.jsonl');args=ap.parse_args()
    if args.snapshot and not args.database:ap.error('--snapshot requires a separate durable --database')
    if args.database and not args.snapshot:ap.error('Demo replay does not use a persistent paper database')
    with tempfile.TemporaryDirectory() as directory:
        database=args.database or Path(directory)/'demo.sqlite'
        engine=Engine(str(database))
        try:
            for snapshot in [json.loads(args.snapshot.read_text())] if args.snapshot else snapshots():engine.apply(snapshot)
            rows=engine.rows()
        finally:engine.close()
    historical=[json.loads(line) for line in args.historical.read_text().splitlines() if line.strip()] if args.historical.exists() else []
    args.out.mkdir(parents=True,exist_ok=True)
    # Derived export only: never writes legacy journals or reports.
    (args.out/'index.html').write_text(cockpit(rows,historical),encoding='utf-8')
    (args.out/'decisions.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    (args.out/'manifest.json').write_text(json.dumps({'methodology':MANIFEST,'manifest_sha256':fingerprint(MANIFEST),'evidence_class':'SNAPSHOT_PAPER' if args.snapshot else 'DEMO_FIXED','historical_journal_sha256':__import__('hashlib').sha256(args.historical.read_bytes()).hexdigest() if args.historical.exists() else None},indent=2,sort_keys=True)+'\n')
    print(f'{len(rows)} v2 records, {len(historical)} separately labeled legacy records -> {args.out}/index.html')
if __name__=='__main__':main()
