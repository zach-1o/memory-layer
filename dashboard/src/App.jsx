import React, { useState } from 'react';
import GraphView from './GraphView.jsx';
import MemoryList from './MemoryList.jsx';

const API_URL = '/api';

export default function App() {
    const [activeTab, setActiveTab] = useState('graph');
    const [apiKey, setApiKey] = useState('skp_dev_key_12345');
    const [projectId, setProjectId] = useState('');

    return (
        <div className="app">
            <header className="header">
                <div className="header-brand">
                    <span className="logo">🧠</span>
                    <div>
                        <h1>Memory Layer</h1>
                        <span className="subtitle">AI Brain Dashboard</span>
                    </div>
                </div>

                <div className="config-bar">
                    <label>Project:</label>
                    <input
                        type="text"
                        value={projectId}
                        onChange={(e) => setProjectId(e.target.value)}
                        placeholder="Enter project ID..."
                    />
                </div>

                <div className="tabs">
                    <button
                        className={`tab ${activeTab === 'graph' ? 'active' : ''}`}
                        onClick={() => setActiveTab('graph')}
                    >
                        🕸️ Knowledge Graph
                    </button>
                    <button
                        className={`tab ${activeTab === 'memories' ? 'active' : ''}`}
                        onClick={() => setActiveTab('memories')}
                    >
                        📓 Memories
                    </button>
                </div>
            </header>

            <main className="main-content">
                {!projectId ? (
                    <div className="graph-container">
                        <div className="empty-state">
                            <span className="icon">🔑</span>
                            <p>Enter a Project ID above to view its memory</p>
                        </div>
                    </div>
                ) : activeTab === 'graph' ? (
                    <GraphView apiKey={apiKey} projectId={projectId} apiUrl={API_URL} />
                ) : (
                    <MemoryList apiKey={apiKey} projectId={projectId} apiUrl={API_URL} />
                )}
            </main>
        </div>
    );
}
