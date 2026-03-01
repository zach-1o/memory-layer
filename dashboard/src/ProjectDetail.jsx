import { useState, useEffect } from 'react';

export default function ProjectDetail({ project, apiKey, onNavigate, onOpenLayer }) {
    const API = import.meta.env.VITE_API_URL || window.location.origin;
    const [stats, setStats] = useState({ obs: project.obs_count, entities: project.entity_count, sessions: project.session_count });

    const health = Math.min(100, Math.round((stats.obs * 3 + stats.entities * 5)));
    const healthColor = health > 70 ? 'var(--success)' : health > 40 ? 'var(--warning)' : 'var(--error)';

    const layers = [
        {
            key: 'episodic',
            icon: '📝',
            title: 'Episodic Log',
            techBadge: 'SQLite + FTS5',
            desc: 'Append-only diary of every agent action — file reads, edits, decisions, and bug fixes.',
            stat1: `${stats.obs} observations`,
            stat2: `${stats.sessions} sessions`,
            color: 'var(--episodic)',
            bg: 'var(--episodic-light)',
        },
        {
            key: 'semantic',
            icon: '🔍',
            title: 'Semantic Layer',
            techBadge: 'ChromaDB',
            desc: 'Vector embeddings for meaning-based search. Find memories by what they mean, not exact words.',
            stat1: `${stats.obs} vectors`,
            stat2: 'Cosine similarity',
            color: 'var(--semantic)',
            bg: 'var(--semantic-light)',
        },
        {
            key: 'graph',
            icon: '🕸️',
            title: 'Knowledge Graph',
            techBadge: 'NetworkX',
            desc: 'Entity relationships: what files, functions, and components connect. Trace data flow.',
            stat1: `${stats.entities} entities`,
            stat2: 'CO_OCCURS edges',
            color: 'var(--graph)',
            bg: 'var(--graph-light)',
        },
    ];

    return (
        <>
            {/* Page Header */}
            <div className="page-header">
                <div className="breadcrumb">
                    <span className="breadcrumb-link" onClick={() => onNavigate('home')}>Projects</span>
                    <span className="breadcrumb-sep">›</span>
                    <span className="breadcrumb-current">{project.project_id}</span>
                </div>
                <div className="page-header-row">
                    <div>
                        <h1>{project.project_id}</h1>
                        <p className="page-header-subtitle">Project overview and memory layers</p>
                    </div>
                    <span className="badge primary">Active</span>
                </div>
            </div>

            <div className="page-content fade-in">
                {/* Stats bar */}
                <div className="card no-pad" style={{ marginBottom: 24 }}>
                    <div className="stat-bar">
                        <div className="stat-bar-item">
                            <div className="stat-bar-label">Sessions</div>
                            <div className="stat-bar-value">{stats.sessions}</div>
                        </div>
                        <div className="stat-bar-item">
                            <div className="stat-bar-label">Observations</div>
                            <div className="stat-bar-value">{stats.obs}</div>
                        </div>
                        <div className="stat-bar-item">
                            <div className="stat-bar-label">Entities</div>
                            <div className="stat-bar-value">{stats.entities}</div>
                        </div>
                        <div className="stat-bar-item">
                            <div className="stat-bar-label">Health</div>
                            <div className="stat-bar-value" style={{ color: healthColor }}>{health}%</div>
                        </div>
                    </div>
                </div>

                {/* MCP Config */}
                <div className="card config-block" style={{ marginBottom: 24 }}>
                    <div className="config-header">
                        <div>
                            <div className="config-title">MCP Connection</div>
                            <div className="config-desc">Add this to your IDE's MCP configuration to connect</div>
                        </div>
                        <button className="btn btn-sm btn-secondary" onClick={() => {
                            navigator.clipboard.writeText(JSON.stringify({
                                mcpServers: {
                                    "memory-layer": {
                                        serverUrl: `${API}/mcp`,
                                        headers: { "x-api-key": "YOUR_KEY" }
                                    }
                                }
                            }, null, 2));
                        }}>
                            📋 Copy
                        </button>
                    </div>
                    <div className="config-code">{`{
  "mcpServers": {
    "memory-layer": {
      "serverUrl": "${API}/mcp",
      "headers": { "x-api-key": "YOUR_KEY" }
    }
  }
}`}</div>
                </div>

                {/* Memory Layers */}
                <div className="section-label">Memory Layers</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {layers.map(layer => (
                        <div key={layer.key} className="card hoverable layer-card" onClick={() => onOpenLayer(layer.key)}>
                            <div className="layer-card-inner">
                                <div className="layer-strip" style={{ background: layer.color }} />
                                <div className="layer-card-content">
                                    <div className="layer-icon" style={{ background: layer.bg, color: layer.color }}>
                                        {layer.icon}
                                    </div>
                                    <div className="layer-info">
                                        <div className="layer-title">
                                            {layer.title}
                                            <span className="badge" style={{ background: layer.bg, color: layer.color }}>{layer.techBadge}</span>
                                        </div>
                                        <div className="layer-desc">{layer.desc}</div>
                                        <div className="layer-stats">
                                            <span className="layer-stat-primary">{layer.stat1}</span>
                                            <span className="layer-stat-sep">·</span>
                                            <span className="layer-stat-secondary">{layer.stat2}</span>
                                        </div>
                                    </div>
                                    <span className="layer-arrow">›</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
}
