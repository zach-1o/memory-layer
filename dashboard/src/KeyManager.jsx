import { useState, useEffect } from 'react';

export default function KeyManager({ api, apiKey, onApiKeyChange }) {
    const [keys, setKeys] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newName, setNewName] = useState('');
    const [generating, setGenerating] = useState(false);
    const [copiedId, setCopiedId] = useState(null);

    const fetchKeys = () => {
        setLoading(true);
        fetch(`${api}/api/keys`, { headers: { 'X-Api-Key': apiKey } })
            .then(r => r.json())
            .then(data => { setKeys(Array.isArray(data) ? data : []); setLoading(false); })
            .catch(() => { setKeys([]); setLoading(false); });
    };

    useEffect(() => { fetchKeys(); }, [apiKey]);

    const generateKey = async () => {
        if (!newName.trim()) return;
        setGenerating(true);
        try {
            const resp = await fetch(`${api}/api/keys`, {
                method: 'POST',
                headers: { 'X-Api-Key': apiKey, 'Content-Type': 'application/json' },
                body: JSON.stringify({ key_name: newName }),
            });
            const data = await resp.json();
            setNewName('');
            fetchKeys();
            if (data.api_key) {
                navigator.clipboard.writeText(data.api_key).catch(() => { });
                alert(`Key generated and copied to clipboard:\n${data.api_key}`);
            }
        } catch (err) {
            console.error(err);
        }
        setGenerating(false);
    };

    const revokeKey = async (keyId) => {
        if (!confirm('Revoke this key? This cannot be undone.')) return;
        try {
            await fetch(`${api}/api/keys/${keyId}`, {
                method: 'DELETE',
                headers: { 'X-Api-Key': apiKey },
            });
            fetchKeys();
        } catch (err) {
            console.error(err);
        }
    };

    const copyConfig = () => {
        navigator.clipboard.writeText(JSON.stringify({
            mcpServers: {
                "memory-layer": {
                    serverUrl: `${api}/mcp`,
                    headers: { "x-api-key": apiKey }
                }
            }
        }, null, 2));
        setCopiedId('config');
        setTimeout(() => setCopiedId(null), 2000);
    };

    return (
        <div>
            {/* Config snippet */}
            <div className="card config-block" style={{ marginBottom: 24 }}>
                <div className="config-header">
                    <div>
                        <div className="config-title">IDE Configuration</div>
                        <div className="config-desc">Paste this into your IDE's MCP settings to connect</div>
                    </div>
                    <button className="btn btn-secondary btn-sm" onClick={copyConfig}>
                        {copiedId === 'config' ? '✓ Copied' : '📋 Copy'}
                    </button>
                </div>
                <div className="config-code">{`{
  "mcpServers": {
    "memory-layer": {
      "serverUrl": "${api}/mcp",
      "headers": { "x-api-key": "${apiKey}" }
    }
  }
}`}</div>
            </div>

            {/* Generate new key */}
            <div className="section-label">Generate New Key</div>
            <div className="card keys-form" style={{ marginBottom: 24 }}>
                <div className="keys-form-row">
                    <div className="input-group" style={{ flex: 1 }}>
                        <span className="input-icon">🏷️</span>
                        <input
                            placeholder="Key name (e.g., 'vscode-dev')"
                            value={newName}
                            onChange={e => setNewName(e.target.value)}
                            onKeyDown={e => { if (e.key === 'Enter') generateKey(); }}
                        />
                    </div>
                    <button className="btn btn-primary" onClick={generateKey} disabled={generating || !newName.trim()}>
                        {generating ? 'Generating…' : '🔑 Generate Key'}
                    </button>
                </div>
            </div>

            {/* Key list */}
            <div className="section-label">Your Keys</div>
            {loading ? (
                <div className="loading">Loading keys…</div>
            ) : keys.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">🔑</div>
                    <div className="empty-title">No API keys</div>
                    <div className="empty-desc">Generate a key above to authenticate your AI assistant.</div>
                </div>
            ) : (
                keys.map((k, i) => {
                    const status = k.revoked_at ? 'revoked' : 'active';
                    return (
                        <div key={i} className="card key-card">
                            <div className="key-card-row">
                                <div style={{ display: 'flex', alignItems: 'center' }}>
                                    <span className="key-prefix">{k.key_prefix || '••••'}</span>
                                    <span className="key-name">{k.key_name || 'Unnamed'}</span>
                                </div>
                                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                    {status !== 'revoked' && (
                                        <button className="btn btn-secondary btn-sm btn-danger" onClick={() => revokeKey(k.key_hash)}>
                                            Revoke
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="key-meta">
                                <div className="key-meta-item">
                                    <div className="key-meta-label">Status</div>
                                    <div className={`key-meta-value key-status ${status}`}>
                                        {status === 'revoked' ? 'Revoked' : 'Active'}
                                    </div>
                                </div>
                                <div className="key-meta-item">
                                    <div className="key-meta-label">Created</div>
                                    <div className="key-meta-value">
                                        {k.created_at ? new Date(k.created_at).toLocaleDateString() : '—'}
                                    </div>
                                </div>
                                <div className="key-meta-item">
                                    <div className="key-meta-label">User</div>
                                    <div className="key-meta-value">{k.user_id || '—'}</div>
                                </div>
                            </div>
                        </div>
                    );
                })
            )}
        </div>
    );
}
