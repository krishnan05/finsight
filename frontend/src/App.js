import React, { useState } from 'react';
import LiveData        from './components/LiveData';
import ValuationChart  from './components/ValuationChart';
import ScenarioExplorer from './components/ScenarioExplorer';
import SentimentFeed   from './components/SentimentFeed';

const tabs = [
  { id:'live',      label:'📊 Live Data'     },
  { id:'valuation', label:'🎯 Valuation'     },
  { id:'scenarios', label:'⚡ Scenarios'     },
  { id:'sentiment', label:'📰 Sentiment'     },
];

export default function App() {
  const [active, setActive] = useState('live');

  return (
    <div style={{ minHeight:'100vh', background:'#0a0e1a' }}>
      {/* Header */}
      <div style={{ background:'#111827',
                    borderBottom:'1px solid #1f2937',
                    padding:'16px 32px',
                    display:'flex', alignItems:'center',
                    justifyContent:'space-between' }}>
        <div>
          <div style={{ fontSize:18, fontWeight:800,
                        color:'#f1f5f9', letterSpacing:'-0.02em' }}>
            ICICI Bank
          </div>
          <div style={{ fontSize:11, color:'#4b5563', marginTop:2 }}>
            Equity Research Platform · NSE: ICICIBANK
          </div>
        </div>
        <div style={{ fontSize:11, color:'#374151',
                      textAlign:'right' }}>
          <div>MBA Financial Modelling Project</div>
          <div style={{ color:'#1d4ed8', marginTop:2 }}>
            Phases 1–4 Complete
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ background:'#111827',
                    borderBottom:'1px solid #1f2937',
                    padding:'0 32px',
                    display:'flex', gap:4 }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActive(t.id)}
            style={{
              padding:'12px 20px', border:'none', cursor:'pointer',
              background:'transparent', fontSize:13, fontWeight:500,
              color: active===t.id ? '#3b82f6' : '#6b7280',
              borderBottom: active===t.id
                ? '2px solid #3b82f6' : '2px solid transparent',
              transition:'all 0.15s',
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ maxWidth:1200, margin:'0 auto',
                    padding:'28px 32px' }}>
        {active === 'live'      && <LiveData />}
        {active === 'valuation' && <ValuationChart />}
        {active === 'scenarios' && <ScenarioExplorer />}
        {active === 'sentiment' && <SentimentFeed />}
      </div>
    </div>
  );
}