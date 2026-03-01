import { useState, useEffect } from 'react';

const TYPE_COLORS = {
    file_read: '#3B82F6',
    file_edit: '#F59E0B',
    search: '#8B5CF6',
    decision: '#EC4899',
    bug_fix: '#EF4444',
    session_start: '#6B7280',
    session_end: '#6B7280',
    observation: '#10B981',
};

const TYPE_ICONS = {
    file_read: '📖',
    file_edit: '✏️',
    search: '🔎',
    decision: '🤔',
    bug_fix: '🐛',
    session_start: '▶️',
    session_end: '⏹️',
    observation: '👁️',
};

export default function MemoryList({ projectId, api, apiKey }) {
    const [memories, setMemories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [search, setSearch] = useState('');
    const [expanded, setExpanded] = useState({});
    const [editId, setEditId] = useState(null);
    const [editText, setEditText] = useState('');

    useEffect(() => {
        setLoading(true);
        fetch(`${api}/api/observations?project_id=${projectId}&limit=200`, {
            headers: { 'X-Api-Key': apiKey }
        })
            .then(r => r.json())
            .then(data => { setMemories(Array.isArray(data) ? data : []); setLoading(false); })
            .catch(() => { setMemories([]); setLoading(false); });
    }, [projectId, api, apiKey]);

    const toggle = (id) => setExpanded(prev => ({ ...prev, [id]: !prev[id] }));

    // Group by session
    const sessions = {};
    memories.forEach(m => {
        const sid = m.session_id || 'unknown';
        if (!sessions[sid]) sessions[sid] = [];
        sessions[sid].push(m);
    });

    // Filter
    const types = [...new Set(memories.map(m => m.action_type))].filter(Boolean);

    const filtered = memories.filter(m => {
        if (filter !== 'all' && m.action_type !== filter) return false;
        if (search && !m.raw_content?.toLowerCase().includes(search.toLowerCase())) return false;
        return true;
    });

    // Re-group filtered
    const filteredSessions = {};
    filtered.forEach(m => {
        const sid = m.session_id || 'unknown';
        if (!filteredSessions[sid]) filteredSessions[sid] = [];
        filteredSessions[sid].push(m);
    });

    const invalidate = async (obsId) => {
        try {
            await fetch(`${api}/api/observations/${obsId}/invalidate`, {
                method: 'POST',
                headers: { 'X-Api-Key': apiKey },
            });
            setMemories(prev => prev.map(m => m.obs_id === obsId ? { ...m, invalidated_at: new Date().toISOString() } : m));
        } catch (err) { console.error(err); }
    };

    const saveSummary = async (obsId) => {
        try {
            await fetch(`${api}/api/observations/${obsId}/summary`, {
                method: 'POST',
                headers: { 'X-Api-Key': apiKey, 'Content-Type': 'application/json' },
                body: JSON.stringify({ summary: editText }),
            });
            setMemories(prev => prev.map(m => m.obs_id === obsId ? { ...m, compressed_summary: editText } : m));
            setEditId(null);
        } catch (err) { console.error(err); }
    };

    if (loading) return <div className="loading">Loading observations…</div>;

    return (
        <div>
            {/* Controls */}
            <div className="controls-row">
                <div className="input-group" style={{ flex: 1 }}>
                    <span className="input-icon">🔍</span>
                    <input placeholder="Filter observations…" value={search} onChange={e => setSearch(e.target.value)} />
                    {search && <span style={{ cursor: 'pointer', color: 'var(--text-secondary)' }} onClick={() => setSearch('')}>✕</span>}
                </div>
                <select className="select" value={filter} onChange={e => setFilter(e.target.value)}>
                    <option value="all">All types</option>
                    {types.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
            </div>

            {filtered.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">📝</div>
                    <div className="empty-title">No observations yet</div>
                    <div className="empty-desc">
                        Observations appear here when an AI assistant records actions via MCP.<br />
                        Start a coding session to see the timeline fill up.
                    </div>
                </div>
            ) : (
                Object.entries(filteredSessions).map(([sessionId, entries]) => (
                    <div key={sessionId} style={{ marginBottom: 28 }}>
                        {/* Session header */}
                        <div className="session-banner">
                            <div className="session-tag">
                                <span className="session-tag-name">Session {sessionId.slice(0, 8)}</span>
                                <span className="session-tag-meta">{entries.length} observations</span>
                            </div>
                            <div className="session-line" />
                        </div>

                        {/* Timeline */}
                        <div className="timeline">
                            <div className="timeline-line" />
                            {entries.map(m => {
                                const isOpen = expanded[m.obs_id];
                                const isEditing = editId === m.obs_id;
                                const dotColor = TYPE_COLORS[m.action_type] || '#6B7280';
                                const entities = m.entities_mentioned ? (typeof m.entities_mentioned === 'string' ? JSON.parse(m.entities_mentioned) : m.entities_mentioned) : [];
                                const timeStr = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

                                return (
                                    <div key={m.obs_id} className="timeline-entry">
                                        <div className="timeline-time">{timeStr}</div>
                                        <div className="timeline-dot" style={{ background: dotColor }} />

                                        <div className={`card timeline-card ${m.invalidated_at ? 'deprecated' : ''}`}>
                                            <div className="timeline-card-header" onClick={() => toggle(m.obs_id)}>
                                                <div className="timeline-card-left">
                                                    <span>{TYPE_ICONS[m.action_type] || '📌'}</span>
                                                    <span className="badge" style={{
                                                        background: dotColor + '18',
                                                        color: dotColor,
                                                    }}>{m.action_type}</span>
                                                    <span className="timeline-card-title">
                                                        {m.compressed_summary || m.raw_content?.slice(0, 80) || 'No content'}
                                                    </span>
                                                </div>
                                                <div className="timeline-card-right">
                                                    {m.token_count > 0 && <span className="timeline-tokens">{m.token_count} tok</span>}
                                                    <span className={`timeline-chevron ${isOpen ? 'open' : ''}`}>▸</span>
                                                </div>
                                            </div>

                                            {isOpen && (
                                                <div className="timeline-card-body">
                                                    {isEditing ? (
                                                        <div>
                                                            <textarea
                                                                style={{
                                                                    width: '100%', padding: 10, borderRadius: 8,
                                                                    border: '1px solid var(--border)', fontFamily: 'var(--font)',
                                                                    fontSize: 13, resize: 'vertical', minHeight: 80,
                                                                }}
                                                                value={editText}
                                                                onChange={e => setEditText(e.target.value)}
                                                            />
                                                            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                                                                <button className="btn btn-primary btn-sm" onClick={() => saveSummary(m.obs_id)}>Save</button>
                                                                <button className="btn btn-secondary btn-sm" onClick={() => setEditId(null)}>Cancel</button>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <>
                                                            <div className="timeline-summary">
                                                                {m.raw_content || 'No content recorded'}
                                                            </div>
                                                            {entities.length > 0 && (
                                                                <div className="timeline-entities">
                                                                    {entities.map(e => <span key={e} className="badge graph-badge">{e}</span>)}
                                                                </div>
                                                            )}
                                                            <div className="timeline-actions">
                                                                <button className="btn btn-secondary btn-sm" onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setEditId(m.obs_id);
                                                                    setEditText(m.compressed_summary || m.raw_content || '');
                                                                }}>✏️ Edit Summary</button>
                                                                {!m.invalidated_at && (
                                                                    <button className="btn btn-secondary btn-sm btn-danger" onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        invalidate(m.obs_id);
                                                                    }}>🗑️ Invalidate</button>
                                                                )}
                                                            </div>
                                                        </>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ))
            )}
        </div>
    );
}
