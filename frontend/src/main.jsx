import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { Activity, ShieldAlert, TrendingUp, DatabaseZap } from "lucide-react";
import "./style.css";
const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
function Card({ title, icon, children }) {
  return (
    <div className="card">
      <div className="cardTitle">
        {icon}
        <h2>{title}</h2>
      </div>
      {children}
    </div>
  );
}
function App() {
  const [summary, setSummary] = useState(null);
  const [err, setErr] = useState("");
  async function load() {
    try {
      const r = await fetch(`${API}/api/v1/dashboard/summary`);
      setSummary(await r.json());
      setErr("");
    } catch (e) {
      setErr("Backend offline");
    }
  }
  async function gen() {
    await fetch(`${API}/api/v1/demo/generate-events?count=8`, {
      method: "POST",
    });
    await fetch(`${API}/api/v1/market/simulate?count=6`, { method: "POST" });
    load();
  }
  useEffect(() => {
    load();
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, []);
  const tx = (summary?.transactions || [])
    .map((t, i) => ({
      name: `T${i + 1}`,
      amount: t.amount,
      score: t.anomaly_score,
    }))
    .reverse();
  return (
    <main>
      <header>
        <div>
          <h1>Real-Time Financial Analytics Platform</h1>
          <p>
            Event-driven fintech analytics: transactions, portfolios, market
            data, fraud, risk and anomaly detection.
          </p>
        </div>
        <span className={summary ? "pill ok" : "pill bad"}>
          {summary?.status || err || "loading"}
        </span>
      </header>
      <section className="hero">
        <div>
          <p>Total Portfolio Value</p>
          <h2>${Number(summary?.portfolio_value || 0).toLocaleString()}</h2>
        </div>
        <button onClick={gen}>Generate Live Events</button>
      </section>
      <section className="grid">
        <Card title="Portfolio Performance" icon={<TrendingUp />}>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={tx}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="amount" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Anomaly Scores" icon={<Activity />}>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={tx}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="score" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Risk & Fraud Alerts" icon={<ShieldAlert />}>
          <div className="list">
            {(summary?.alerts || []).map((a) => (
              <div className="row" key={a.id}>
                <b>{a.severity.toUpperCase()}</b>
                <span>{a.alert_type}</span>
                <p>{a.message}</p>
              </div>
            ))}
          </div>
        </Card>
        <Card title="Market Prices" icon={<DatabaseZap />}>
          <div className="prices">
            {(summary?.prices || []).map((p) => (
              <div>
                <b>{p.symbol}</b>
                <span>${p.price}</span>
              </div>
            ))}
          </div>
        </Card>
      </section>
      <section className="table">
        <h2>Live Transaction Feed</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Amount</th>
              <th>Anomaly</th>
            </tr>
          </thead>
          <tbody>
            {(summary?.transactions || []).map((t) => (
              <tr>
                <td>{t.id}</td>
                <td>{t.transaction_type}</td>
                <td>{t.quantity}</td>
                <td>${t.price}</td>
                <td>${t.amount}</td>
                <td>{t.anomaly_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
createRoot(document.getElementById("root")).render(<App />);
