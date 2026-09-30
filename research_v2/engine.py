"""Snapshot-only paper methodology v2. No network, credentials, LLM call or order path."""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3

MANIFEST={'version':'snapshot-paper-v2','interval':'1d','holding_period_bars':5,'position_size_fraction':0.10,'min_confidence':0.4,'max_gross_exposure_fraction':1.0,'round_trip_cost_bps':30,'symbols':{'BTC-USD':'BTC/USD','ETH-USD':'ETH/USD'},'benchmark':'fixed equal-weight normalized BTC/ETH basket','benchmark_anchor':'2026-09-01T00:00:00+00:00'}

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def fingerprint(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def timestamp(value):
    time=datetime.fromisoformat(value.replace('Z','+00:00'))
    if time.tzinfo is None:raise ValueError('Timestamps require timezone')
    return time.astimezone(timezone.utc)
def finite(value,positive=False):
    if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or (positive and value<=0):raise ValueError('Nonfinite/invalid numeric input')
    return float(value)

def validate_snapshot(snapshot):
    observed=timestamp(snapshot['observed_at'])
    if snapshot['evidence_class'] not in ['DEMO_FIXED','SNAPSHOT_PAPER']:raise ValueError('Unsupported evidence class')
    if snapshot['evidence_class']=='SNAPSHOT_PAPER' and not timedelta(0)<=datetime.now(timezone.utc)-observed<=timedelta(days=1):raise ValueError('Paper snapshot is future-dated or stale against wall clock')
    if snapshot['interval']!=MANIFEST['interval']:raise ValueError('Interval mismatch')
    if set(snapshot['markets'])!=set(MANIFEST['symbols']):raise ValueError('Fixed benchmark requires every component')
    histories={}
    for ticker,market in snapshot['markets'].items():
        if market['provider_symbol']!=MANIFEST['symbols'][ticker] or not market.get('source'):raise ValueError('Provider lineage mismatch')
        history={}
        last=None
        for bar in market['bars']:
            time=timestamp(bar['start']);price=finite(bar['open'],True)
            if time.time()!=datetime.min.time() or time>observed or (last is not None and time!=last+timedelta(days=1)):raise ValueError('Unordered, missing, future or off-interval bars')
            history[time]=price;last=time
        if len(history)<2 or observed-last>timedelta(days=1):raise ValueError('Missing or stale market data')
        histories[ticker]=history
    if len({tuple(h) for h in histories.values()})!=1:raise ValueError('Benchmark bars must align exactly')
    for ticker,thesis in snapshot.get('theses',{}).items():
        if ticker not in histories:raise ValueError('Unknown thesis ticker')
        completed=timestamp(thesis['completed_at']);cutoff=timestamp(thesis['input_cutoff'])
        if cutoff not in histories[ticker] or cutoff+timedelta(days=1)>completed or completed>observed:raise ValueError('Thesis chronology invalid')
        if cutoff!=max(time for time in histories[ticker] if time+timedelta(days=1)<=observed):raise ValueError('Stale thesis input cutoff')
        confidence=finite(thesis['confidence'])
        if not 0<=confidence<=1 or thesis['direction'] not in ['LONG','FLAT']:raise ValueError('Invalid thesis')
        if not isinstance(thesis.get('reasoning'),str) or not thesis['reasoning'].strip() or not thesis.get('source'):raise ValueError('Missing thesis lineage')
    return observed,histories

class Engine:
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path,timeout=10,isolation_level=None)
        self.db.row_factory=sqlite3.Row
        self.db.executescript('CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT);CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY,observed TEXT UNIQUE,body TEXT);CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY,economic_key TEXT UNIQUE,body TEXT);')
    def close(self):self.db.close()
    def rows(self):return [json.loads(r['body']) for r in self.db.execute('SELECT body FROM decisions ORDER BY economic_key')]
    def _put(self,row):self.db.execute('INSERT INTO decisions VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',(row['id'],row['economic_key'],canonical(row)))
    def apply(self,snapshot):
        observed,histories=validate_snapshot(snapshot)
        snapshot_id=fingerprint(snapshot);observed_text=observed.isoformat()
        formed_time=observed if snapshot['evidence_class']=='DEMO_FIXED' else datetime.now(timezone.utc)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            existing=self.db.execute('SELECT value FROM metadata WHERE key="manifest"').fetchone()
            if existing and existing['value']!=canonical(MANIFEST):raise ValueError('Methodology changed; use a separate database')
            self.db.execute('INSERT OR IGNORE INTO metadata VALUES("manifest",?)',(canonical(MANIFEST),))
            cohort=self.db.execute('SELECT value FROM metadata WHERE key="evidence_class"').fetchone()
            if cohort and cohort['value']!=snapshot['evidence_class']:raise ValueError('Cannot mix demo and paper snapshots')
            self.db.execute('INSERT OR IGNORE INTO metadata VALUES("evidence_class",?)',(snapshot['evidence_class'],))
            if self.db.execute('SELECT id FROM snapshots WHERE id=?',(snapshot_id,)).fetchone():
                rows=self.rows();self.db.execute('COMMIT');return rows
            latest=self.db.execute('SELECT observed FROM snapshots ORDER BY observed DESC LIMIT 1').fetchone()
            if latest and timestamp(latest['observed'])>=observed:raise ValueError('Conflicting or out-of-order snapshot')
            anchor=timestamp(MANIFEST['benchmark_anchor'])
            if any(anchor not in history for history in histories.values()):raise ValueError('Benchmark anchor missing')
            base={ticker:history[anchor] for ticker,history in histories.items()}
            old_base=self.db.execute('SELECT value FROM metadata WHERE key="benchmark_base"').fetchone()
            if old_base and json.loads(old_base['value'])!=base:raise ValueError('Frozen benchmark anchor revised')
            self.db.execute('INSERT OR IGNORE INTO metadata VALUES("benchmark_base",?)',(canonical(base),))
            def benchmark(time):
                # No skipping missing basket legs, and no changing weights/base.
                return sum(histories[ticker][time]/base[ticker] for ticker in sorted(base))/len(base)
            # Fill then settle mature positions before evaluating new exposure.
            for row in self.rows():
                if row['state']=='AWAITING_FILL':
                    formed=timestamp(row['decision_formed_at'])
                    candidates=[time for time in histories[row['ticker']] if time>formed and time<=observed]
                    if candidates:
                        fill=min(candidates);row.update(state='OPEN',entry_date=fill.isoformat(),entry_price=histories[row['ticker']][fill],benchmark_entry=benchmark(fill),fill_snapshot=snapshot_id)
                if row['state']=='OPEN':
                    exit_time=timestamp(row['entry_date'])+timedelta(days=row['holding_period_bars'])
                    if exit_time in histories[row['ticker']] and exit_time<=observed:
                        price=histories[row['ticker']][exit_time]
                        gross=price/row['entry_price']-1;bench=benchmark(exit_time)/row['benchmark_entry']-1
                        row.update(state='COMPLETE',exit_date=exit_time.isoformat(),exit_price=price,gross_return=gross,benchmark_return=bench,excess_return=gross-bench,net_return=gross-row['round_trip_cost_bps']/10000,exit_snapshot=snapshot_id)
                self._put(row)
            rows=self.rows();exposure=sum(row['size_fraction'] for row in rows if row['state'] in ['AWAITING_FILL','OPEN'])
            for ticker,thesis in sorted(snapshot.get('theses',{}).items()):
                cutoff=timestamp(thesis['input_cutoff']).isoformat()
                economic_key='|'.join([fingerprint(MANIFEST),ticker,MANIFEST['interval'],cutoff])
                if any(row['economic_key']==economic_key for row in rows):continue
                approved=thesis['direction']=='LONG' and thesis['confidence']>=MANIFEST['min_confidence'] and exposure+MANIFEST['position_size_fraction']<=MANIFEST['max_gross_exposure_fraction']+1e-12
                row={'id':hashlib.sha256(economic_key.encode()).hexdigest(),'economic_key':economic_key,'methodology':MANIFEST['version'],'evidence_class':snapshot['evidence_class'],'ticker':ticker,'provider_symbol':MANIFEST['symbols'][ticker],'interval':MANIFEST['interval'],'holding_period_bars':MANIFEST['holding_period_bars'],'round_trip_cost_bps':MANIFEST['round_trip_cost_bps'],'input_cutoff':cutoff,'thesis_completed_at':timestamp(thesis['completed_at']).isoformat(),'decision_formed_at':formed_time.isoformat(),'clock_source':'fixed replay clock' if snapshot['evidence_class']=='DEMO_FIXED' else 'process UTC wall clock','thesis':thesis,'market_source':snapshot['markets'][ticker]['source'],'decision_snapshot':snapshot_id,'state':'AWAITING_FILL' if approved else 'HOLD','size_fraction':MANIFEST['position_size_fraction'] if approved else 0,'risk_reason':'Approved within gross exposure' if approved else 'Flat/low-confidence thesis or gross exposure limit','entry_date':None,'entry_price':None}
                self._put(row);rows.append(row)
                if approved:exposure+=row['size_fraction']
            self.db.execute('INSERT INTO snapshots VALUES(?,?,?)',(snapshot_id,observed_text,canonical(snapshot)))
            self.db.execute('COMMIT');return self.rows()
        except BaseException:
            self.db.execute('ROLLBACK');raise
