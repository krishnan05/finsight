import React, { useEffect, useState } from 'react';
import axios from 'axios';


const API = 'http://localhost:8000/api';

export default function SentimentFeed() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/sentiment`)
      .then(r => { setData(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Analysing news sentiment...</div>;
  if (!data)   return <div className="loading">Failed to load sentiment.</div>;

  const { summary, articles, adjusted_target, note } = data;

  const Icon = ({ label }) =>
  label?.includes('Positive') ? <span>🟢</span> :
  label?.includes('Negative') ? <span>🔴</span> :
                                 <span>⚪</span>;
  const scoreColor = s =>
    s >= 0.05 ? '#10b981' : s <= -0.05 ? '#ef4444' : '#f59e0b';

  return (
    <div>
      <div style={{ display:'flex', alignItems:'center',
                    gap:12, marginBottom:20 }}>
        📰
        <h2 style={{ fontSize:16, fontWeight:700 }}>Sentiment Analysis</h2>
      </div>

      {/* Summary bar */}
      <div className="card" style={{ marginBottom:16,
           background:'linear-gradient(135deg,#1c1a0f,#111827)',
           borderColor:'#854d0e' }}>
        <div style={{ display:'flex', justifyContent:'space-between',
                      alignItems:'center', flexWrap:'wrap', gap:12 }}>
          <div>
            <div style={{ fontSize:13, color:'#6b7280' }}>
              Overall Signal
            </div>
            <div style={{ fontSize:18, fontWeight:700,
                          color:'#f59e0b', marginTop:4 }}>
              {summary?.signal}
            </div>
            <div style={{ fontSize:12, color:'#6b7280', marginTop:4 }}>
              {note}
            </div>
          </div>
          <div style={{ textAlign:'right' }}>
            <div style={{ fontSize:12, color:'#6b7280' }}>
              Sentiment-Adjusted Target
            </div>
            <div style={{ fontSize:28, fontWeight:800,
                          color:'#10b981', marginTop:4 }}>
              ₹{adjusted_target?.toLocaleString('en-IN')}
            </div>
            <div style={{ fontSize:11, color:'#6b7280', marginTop:2 }}>
              Avg Score: {summary?.avg_score > 0 ? '+' : ''}
              {summary?.avg_score?.toFixed(3)}
            </div>
          </div>
        </div>

        {/* Sentiment breakdown bar */}
        <div style={{ marginTop:16 }}>
          <div style={{ display:'flex', gap:8, fontSize:12,
                        color:'#6b7280', marginBottom:6 }}>
            <span className="positive">
              ✓ {summary?.positive} Positive
            </span>
            <span style={{ color:'#4b5563' }}>·</span>
            <span className="negative">
              ✗ {summary?.negative} Negative
            </span>
            <span style={{ color:'#4b5563' }}>·</span>
            <span className="neutral">
              – {summary?.neutral} Neutral
            </span>
          </div>
          <div style={{ height:6, background:'#1f2937',
                        borderRadius:3, overflow:'hidden' }}>
            <div style={{
              height:'100%',
              width:`${(summary?.positive/summary?.total)*100}%`,
              background:'linear-gradient(90deg,#10b981,#059669)',
              borderRadius:3
            }} />
          </div>
        </div>
      </div>

      {/* Articles list */}
      <div className="card">
        <div className="card-title">
          Recent Headlines ({articles?.length} analysed)
        </div>
        <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
          {articles?.map((a, i) => (
            <div key={i} style={{
              display:'flex', alignItems:'flex-start', gap:10,
              padding:'10px 12px', borderRadius:8,
              background:'#0f172a',
              borderLeft:`3px solid ${scoreColor(a.score)}`
            }}>
              <Icon label={a.label} />
              <div style={{ flex:1, minWidth:0 }}>
                <div style={{ fontSize:13, color:'#e2e8f0',
                              lineHeight:1.4 }}>
                  {a.title}
                </div>
              </div>
              <div style={{ fontSize:12, fontWeight:700, flexShrink:0,
                            color: scoreColor(a.score) }}>
                {a.score > 0 ? '+' : ''}{a.score?.toFixed(3)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}