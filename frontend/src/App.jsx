import { useState } from "react";
import axios from "axios";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

const COLORS = {
  Low: "#16a34a",
  Medium: "#f59e0b",
  High: "#dc2626",
  Unknown: "#6b7280",
};

function App() {
  const [projectPath, setProjectPath] = useState("examples");
  const [uploadFile, setUploadFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scanStage, setScanStage] = useState("");
  const [summary, setSummary] = useState(null);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  const resetResults = () => {
    setError("");
    setSummary(null);
    setResults([]);
  };

  const scanProject = async () => {
    setLoading(true);
    resetResults();
    setScanStage("Preparing scan...");

    const stageTimers = [
      setTimeout(() => setScanStage("Cloning or preparing project source..."), 700),
      setTimeout(() => setScanStage("Discovering dependency files..."), 1800),
      setTimeout(() => setScanStage("Resolving package licenses..."), 3200),
      setTimeout(() => setScanStage("Running AI compliance analysis..."), 5000),
      setTimeout(() => setScanStage("Generating reports and charts..."), 7000),
    ];

    try {
      const response = await axios.post(`${API_BASE}/scan`, {
        project_path: projectPath,
      });

      setSummary(response.data.summary);
      setResults(response.data.results || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Scan failed.");
    } finally {
      stageTimers.forEach((timer) => clearTimeout(timer));
      setLoading(false);
      setScanStage("");
    }
  };

  const uploadAndScan = async () => {
    if (!uploadFile) {
      setError("Please select a .zip, .tar.gz, or .tgz archive file.");
      return;
    }

    setLoading(true);
    resetResults();
    setScanStage("Uploading project archive...");

    const stageTimers = [
      setTimeout(() => setScanStage("Extracting uploaded archive..."), 900),
      setTimeout(() => setScanStage("Discovering dependency files..."), 1800),
      setTimeout(() => setScanStage("Resolving package licenses..."), 3200),
      setTimeout(() => setScanStage("Running AI compliance analysis..."), 5000),
      setTimeout(() => setScanStage("Generating reports and charts..."), 7000),
    ];

    const formData = new FormData();
    formData.append("file", uploadFile);

    try {
      const response = await axios.post(`${API_BASE}/upload-scan`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setSummary(response.data.summary);
      setResults(response.data.results || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload scan failed.");
    } finally {
      stageTimers.forEach((timer) => clearTimeout(timer));
      setLoading(false);
      setScanStage("");
    }
  };

  const riskClass = (risk) => {
    if (risk === "High") return "risk-high";
    if (risk === "Medium") return "risk-medium";
    if (risk === "Low") return "risk-low";
    return "risk-unknown";
  };

  const riskRows = summary
    ? [
        { name: "Low", value: summary.risk_summary.Low || 0 },
        { name: "Medium", value: summary.risk_summary.Medium || 0 },
        { name: "High", value: summary.risk_summary.High || 0 },
        { name: "Unknown", value: summary.risk_summary.Unknown || 0 },
      ].filter((item) => item.value > 0)
    : [];

  const renderTable = (title, rows, emptyText) => (
    <>
      <h2>{title}</h2>

      {rows.length === 0 ? (
        <div className="empty-state">{emptyText}</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Package</th>
              <th>Version</th>
              <th>Ecosystem</th>
              <th>License</th>
              <th>Family</th>
              <th>Risk</th>
              <th>Reason</th>
              <th>Link</th>
            </tr>
          </thead>

          <tbody>
            {rows.map((item, index) => (
              <tr key={index}>
                <td>{item.package}</td>
                <td>{item.version}</td>
                <td>{item.ecosystem}</td>
                <td>{item.license}</td>
                <td>{item.license_family}</td>
                <td>
                  <span className={`badge ${riskClass(item.risk)}`}>
                    {item.risk}
                  </span>
                </td>
                <td>{item.reason}</td>
                <td>
                  {item.package_url ? (
                    <a href={item.package_url} target="_blank" rel="noreferrer">
                      View
                    </a>
                  ) : (
                    "-"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );

  const lowRiskRows = results.filter((item) => item.risk === "Low");

  return (
    <div className="app">
      <h1>OSS Compliance AI Dashboard</h1>

      <div className="scan-card">
        <div className="input-section">
          <label>Project Path or Repository URL</label>

          <input
            value={projectPath}
            onChange={(e) => setProjectPath(e.target.value)}
            placeholder="https://github.com/pallets/flask"
          />

          <div className="supported-inputs">
            <p>Supported inputs:</p>
            <ul>
              <li>GitHub / GitLab repository URLs</li>
              <li>Generic .git repository URLs</li>
              <li>.zip / .tar.gz / .tgz project archive URLs</li>
              <li>Local project paths available to the backend</li>
            </ul>
          </div>
        </div>

        <button onClick={scanProject} disabled={loading}>
          {loading ? "Scanning..." : "Scan Project"}
        </button>
      </div>

      <div className="upload-card">
        <div className="input-section">
          <label>Upload Project Archive</label>

          <input
            type="file"
            accept=".zip,.tar.gz,.tgz"
            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
          />

          <p className="upload-help">
            Upload a compressed project archive to scan private or local projects.
          </p>
        </div>

        <button onClick={uploadAndScan} disabled={loading}>
          {loading ? "Scanning..." : "Upload & Scan"}
        </button>
      </div>

      {loading && (
        <div className="loading-card">
          <div className="spinner"></div>
          <p>{scanStage}</p>
        </div>
      )}

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

          <section className="chart-card">
            <h2>Risk Distribution</h2>

            {riskRows.length === 0 ? (
              <div className="empty-state">No risk data available.</div>
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={riskRows}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={110}
                    label
                  >
                    {riskRows.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={COLORS[entry.name] || "#6b7280"}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </section>

          <div className="actions">
            <a href={`${API_BASE}/download/excel`} className="download-button">
              Download Excel Report
            </a>

            <a href={`${API_BASE}/download/pdf`} className="download-button">
              Download PDF Report
            </a>
          </div>

          {renderTable(
            "High Risk Packages",
            summary.top_risky_packages || [],
            "No high-risk packages found."
          )}

          {renderTable(
            "Medium Risk Packages",
            summary.medium_risk_packages || [],
            "No medium-risk packages found."
          )}

          {renderTable(
            "Low Risk Packages",
            summary.low_risk_packages || lowRiskRows.slice(0, 10),
            "No low-risk packages found."
          )}

          {renderTable("Full Dependency Report", results, "No dependencies found.")}
        </>
      )}
    </div>
  );
}

export default App;