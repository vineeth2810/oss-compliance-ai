import { useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [projectPath, setProjectPath] = useState("examples");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  const scanProject = async () => {
    setLoading(true);
    setError("");
    setSummary(null);
    setResults([]);

    try {
      const response = await axios.post(`${API_BASE}/scan`, {
        project_path: projectPath,
      });

      setSummary(response.data.summary);
      setResults(response.data.results || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Scan failed.");
    } finally {
      setLoading(false);
    }
  };

  const riskClass = (risk) => {
    if (risk === "High") return "risk-high";
    if (risk === "Medium") return "risk-medium";
    if (risk === "Low") return "risk-low";
    return "risk-unknown";
  };

  return (
    <div className="app">
      <h1>OSS Compliance AI Dashboard</h1>

      <div className="scan-card">
        <label>Project Path or GitHub URL</label>

        <input
          value={projectPath}
          onChange={(e) => setProjectPath(e.target.value)}
          placeholder="examples or https://github.com/pallets/flask"
        />

        <button onClick={scanProject} disabled={loading}>
          {loading ? "Scanning..." : "Scan Project"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {summary && (
        <>
          <section className="summary">
            <div className={`metric ${riskClass(summary.overall_project_risk)}`}>
              <span>Overall Risk</span>
              <strong>{summary.overall_project_risk}</strong>
            </div>

            <div className="metric">
              <span>Total Dependencies</span>
              <strong>{summary.total_dependencies}</strong>
            </div>

            <div className="metric risk-low">
              <span>Low</span>
              <strong>{summary.risk_summary.Low}</strong>
            </div>

            <div className="metric risk-medium">
              <span>Medium</span>
              <strong>{summary.risk_summary.Medium}</strong>
            </div>

            <div className="metric risk-high">
              <span>High</span>
              <strong>{summary.risk_summary.High}</strong>
            </div>
          </section>

          <h2>Top Risky Packages</h2>

          <table>
            <thead>
              <tr>
                <th>Package</th>
                <th>Version</th>
                <th>License</th>
                <th>Family</th>
                <th>Risk</th>
                <th>Reason</th>
              </tr>
            </thead>

            <tbody>
              {summary.top_risky_packages.map((item, index) => (
                <tr key={index}>
                  <td>{item.package}</td>
                  <td>{item.version}</td>
                  <td>{item.license}</td>
                  <td>{item.license_family}</td>
                  <td>
                    <span className={`badge ${riskClass(item.risk)}`}>
                      {item.risk}
                    </span>
                  </td>
                  <td>{item.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h2>Full Dependency Report</h2>

          <table>
            <thead>
              <tr>
                <th>Package</th>
                <th>Version</th>
                <th>License</th>
                <th>Family</th>
                <th>Risk</th>
                <th>Reason</th>
              </tr>
            </thead>

            <tbody>
              {results.map((item, index) => (
                <tr key={index}>
                  <td>{item.package}</td>
                  <td>{item.version}</td>
                  <td>{item.license}</td>
                  <td>{item.license_family}</td>
                  <td>
                    <span className={`badge ${riskClass(item.risk)}`}>
                      {item.risk}
                    </span>
                  </td>
                  <td>{item.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

export default App;