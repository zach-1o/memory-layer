import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function MemoryList({ apiKey, projectId, apiUrl }) {
    const [observations, setObservations] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(null);

    const fetchObservations = async (query = '') => {
        setLoading(true);
        try {
            const endpoint = query
                ? `${apiUrl}/search`
                : `${apiUrl}/observations`;

            const params = { project_id: projectId };
            if (query) params.q = query;

            const res = await axios.get(endpoint, {
                params,
                headers: { 'X-Api-Key': apiKey },
            });

            setObservations(Array.isArray(res.data) ? res.data : []);
        } catch (err) {
            console.error('Failed to fetch observations:', err);
            setObservations([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (projectId) fetchObservations();
    }, [projectId]);

    const handleSearch = (e) => {
        e.preventDefault();
        fetchObservations(searchQuery);
    };

    const formatTime = (ts) => {
        if (!ts) return '';
        try {
            const d = new Date(ts);
            return d.toLocaleString();
        } catch {
            return ts;
        }
    };

    const parseEntities = (entities) => {
        if (!entities) return [];
        if (Array.isArray(entities)) return entities;
        try {
            return JSON.parse(entities);
        } catch {
            return [];
        }
    };

    return (
        <div className="memory-list fade-in">
            <form className="search-bar" onSubmit={handleSearch}>
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search memories... (e.g., 'authentication', 'mutex bug')"
                />
                <button type="submit">🔍 Search</button>
            </form>

            {loading ? (
                <div className="loading">Loading memories...</div>
            ) : observations.length === 0 ? (
                <div className="card" style={{ textAlign: 'center', padding: 48 }}>
                    <p style={{ fontSize: 32, marginBottom: 12 }}>📭</p>
                    <p style={{ color: 'var(--text-muted)' }}>
                        {searchQuery
                            ? 'No memories match your search'
                            : 'No memories recorded yet. Start a coding session!'}
                    </p>
                </div>
            ) : (
                observations.map((obs, i) => {
                    const entities = parseEntities(obs.entities_mentioned);
                    const isExpanded = expanded === obs.id;

                    return (
                        <div
                            key={obs.id || i}
                            className="obs-card fade-in"
                            style={{ animationDelay: `${i * 0.05}s` }}
                            onClick={() => setExpanded(isExpanded ? null : obs.id)}
                        >
                            <div className="obs-header">
                                <span className={`obs-type ${obs.action_type || ''}`}>
                                    {obs.action_type || 'observation'}
                                </span>
                                <span className="obs-time">{formatTime(obs.timestamp)}</span>
                            </div>

                            <div className="obs-content">
                                {isExpanded
                                    ? obs.raw_content || obs.compressed_summary || obs.snippet || ''
                                    : (obs.compressed_summary || obs.snippet || obs.raw_content || '').slice(0, 200)}
                                {!isExpanded &&
                                    (obs.raw_content || '').length > 200 &&
                                    '...'}
                            </div>

                            {entities.length > 0 && (
                                <div className="obs-entities">
                                    {entities.map((entity, j) => (
                                        <span key={j} className="entity-tag">
                                            {entity}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })
            )}
        </div>
    );
}
