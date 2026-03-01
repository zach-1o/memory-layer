import { useState } from 'react';

export default function SearchView({ projectId, api, apiKey }) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);

    const doSearch = async () => {
        if (!query.trim()) return;
        setLoading(true);
        try {
            const resp = await fetch(`${api}/api/search?project_id=${projectId}&q=${encodeURIComponent(query)}`, {
                headers: { 'X-Api-Key': apiKey }
            });
            const data = await resp.json();
            setResults(Array.isArray(data) ? data : data.results || []);
        } catch (err) {
            setResults([]);
        }
        setLoading(false);
    };

    const handleKey = (e) => { if (e.key === 'Enter') doSearch(); };

    return (
        <div>
            {/* Explainer */}
            <div className="card explainer-card" style={{ borderLeft: '3px solid var(--semantic)', marginBottom: 24 }}>
                <div className="explainer-inner">
                    <span className="explainer-icon">🧠</span>
                    <div>
                        <div className="explainer-title">How Semantic Search Works</div>
                        <div className="explainer-text">
                            Your query is converted to a vector embedding and compared against all stored memories using cosine similarity.
                            Results are ranked by semantic distance — the closer the match, the higher the score.
                            Unlike keyword search, this finds memories by <strong>meaning</strong>, not exact words.
                        </div>
                    </div>
                </div>
            </div>

            {/* Search bar */}
            <div style={{ display: 'flex', gap: 10, marginBottom: 24 }}>
                <div className="input-group" style={{ flex: 1 }}>
                    <span className="input-icon">🔍</span>
                    <input
                        placeholder="Search memories by meaning…"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        onKeyDown={handleKey}
                    />
                </div>
                <button className="btn btn-primary" onClick={doSearch} disabled={loading}>
                    {loading ? 'Searching…' : '🔎 Search Memory'}
                </button>
            </div>

            {/* Results */}
            {results !== null && (
                results.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-icon">🔍</div>
                        <div className="empty-title">No matches found</div>
                        <div className="empty-desc">Try different keywords or a broader query.</div>
                    </div>
                ) : (
                    <div>
                        <div className="search-results-label">
                            Found <strong>{results.length}</strong> results for "<span className="search-results-query">{query}</span>"
                        </div>
                        <div className="search-results-list">
                            {results.map((r, i) => {
                                // ChromaDB returns distance (0 = perfect), convert to % score
                                const distance = r.distance ?? r.score ?? 0.5;
                                const score = Math.max(0, Math.round((1 - distance) * 100));
                                const scoreColor = score > 75 ? 'var(--success)' : score > 50 ? 'var(--warning)' : 'var(--text-secondary)';
                                const type = r.action_type || r.metadata?.action_type || 'unknown';
                                const content = r.raw_content || r.content || r.text || '';
                                const summary = r.compressed_summary || content.slice(0, 120);

                                return (
                                    <div key={i} className="card search-result">
                                        <div className="search-result-inner">
                                            {/* Score column */}
                                            <div className="search-score">
                                                <div className="search-score-value" style={{ color: scoreColor }}>{score}</div>
                                                <div className="search-score-label">Match</div>
                                                <div className="search-score-bar">
                                                    <div className="search-score-fill" style={{ width: `${score}%`, background: scoreColor }} />
                                                </div>
                                            </div>

                                            {/* Content */}
                                            <div className="search-result-content">
                                                <div className="search-result-header">
                                                    <span className="badge">{type}</span>
                                                    <span className="search-result-title">{summary}</span>
                                                </div>
                                                <div className="search-result-meta">
                                                    {r.timestamp && new Date(r.timestamp).toLocaleString()}
                                                    {r.session_id && ` · Session ${r.session_id?.slice(0, 8)}`}
                                                </div>
                                            </div>

                                            {/* Actions */}
                                            <div className="search-result-actions">
                                                <button className="btn btn-secondary btn-sm" onClick={() => {
                                                    // Could expand to show full content
                                                    alert(content);
                                                }}>View Full</button>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )
            )}
        </div>
    );
}
