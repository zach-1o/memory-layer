import { useState, useEffect, useCallback } from 'react';
import GraphView from './GraphView';
import MemoryList from './MemoryList';
import SearchView from './SearchView';
import KeyManager from './KeyManager';
import ProjectDetail from './ProjectDetail';
import './index.css';

const API = 'http://localhost:37777';

// ── Shared Components ──

function Badge({ children, type }) {
    return <span className={`badge ${type || ''}`}>{children}</span>;
}

function Btn({ children, onClick, variant = 'secondary', size, ...rest }) {
    return (
        <button className={`btn btn-${variant} ${size === 'sm' ? 'btn-sm' : ''}`} onClick={onClick} {...rest}>
            {children}
        </button>
    );
}

function PageHeader({ title, subtitle, breadcrumbs, actions, children }) {
    return (
        <div className="page-header">
            {breadcrumbs && (
                <div className="breadcrumb">
                    {breadcrumbs.map((b, i) => (
                        <span key={i}>
                            {i > 0 && <span className="breadcrumb-sep">›</span>}
                            {b.onClick
                                ? <span className="breadcrumb-link" onClick={b.onClick}>{b.label}</span>
                                : <span className="breadcrumb-current">{b.label}</span>}
                        </span>
                    ))}
                </div>
            )}
            <div className="page-header-row">
                <div>
                    <h1>{title}</h1>
                    {subtitle && <p className="page-header-subtitle">{subtitle}</p>}
                </div>
                {actions && <div className="page-header-actions">{actions}</div>}
            </div>
            {children}
        </div>
    );
}

// ── Sidebar ──

function Sidebar({ screen, onNavigate }) {
    const mainNav = [
        { id: 'home', label: 'Projects', icon: '📁' },
        { id: 'keys', label: 'API Keys', icon: '🔑' },
    ];

    return (
        <div className="sidebar">
            <div className="sidebar-logo">
                <div className="sidebar-logo-icon">ML</div>
                <div className="sidebar-logo-text">
                    <h2>Memory Layer</h2>
                    <p>AI Memory Dashboard</p>
                </div>
            </div>

            <nav className="sidebar-nav">
                <div className="sidebar-section-label">Navigation</div>
                {mainNav.map(item => (
                    <div
                        key={item.id}
                        className={`sidebar-item ${screen === item.id ? 'active' : ''}`}
                        onClick={() => onNavigate(item.id)}
                    >
                        <span className="sidebar-item-icon">{item.icon}</span>
                        {item.label}
                    </div>
                ))}
            </nav>

            <div className="sidebar-user">
                <div className="sidebar-avatar">U</div>
                <div>
                    <div className="sidebar-user-name">User</div>
                    <div className="sidebar-user-plan">Local Dev</div>
                </div>
            </div>
        </div>
    );
}

// ── Home Screen (Project List) ──

function HomeScreen({ onSelectProject, apiKey }) {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        fetch(`${API}/api/projects`, { headers: { 'X-Api-Key': apiKey } })
            .then(r => r.json())
            .then(data => { setProjects(Array.isArray(data) ? data : []); setLoading(false); })
            .catch(() => { setProjects([]); setLoading(false); });
    }, [apiKey]);

    const totalObs = projects.reduce((s, p) => s + p.obs_count, 0);
    const totalEntities = projects.reduce((s, p) => s + p.entity_count, 0);
    const totalSessions = projects.reduce((s, p) => s + p.session_count, 0);

    return (
        <>
            <PageHeader title="Projects" subtitle="All your memory-layer projects" />
            <div className="page-content fade-in">
                {/* Global Stats */}
                <div className="stats-grid" style={{ marginBottom: 24 }}>
                    <div className="card stat-card">
                        <div className="stat-icon">📁</div>
                        <div className="stat-value">{projects.length}</div>
                        <div className="stat-label">Projects</div>
                    </div>
                    <div className="card stat-card">
                        <div className="stat-icon">👁️</div>
                        <div className="stat-value">{totalObs}</div>
                        <div className="stat-label">Observations</div>
                    </div>
                    <div className="card stat-card">
                        <div className="stat-icon">🔗</div>
                        <div className="stat-value">{totalEntities}</div>
                        <div className="stat-label">Entities</div>
                    </div>
                    <div className="card stat-card">
                        <div className="stat-icon">⏱️</div>
                        <div className="stat-value">{totalSessions}</div>
                        <div className="stat-label">Sessions</div>
                    </div>
                </div>

                {/* Project Grid */}
                {loading ? (
                    <div className="loading">Loading projects…</div>
                ) : projects.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-icon">📂</div>
                        <div className="empty-title">No projects yet</div>
                        <div className="empty-desc">
                            Connect an AI assistant via MCP to start recording memory. <br />
                            Use the API Keys tab to generate credentials.
                        </div>
                    </div>
                ) : (
                    <div className="project-grid">
                        {projects.map(p => (
                            <ProjectCard key={p.tenant_hash} project={p} onClick={() => onSelectProject(p)} />
                        ))}
                    </div>
                )}
            </div>
        </>
    );
}

function ProjectCard({ project, onClick }) {
    const health = Math.min(100, Math.round((project.obs_count * 3 + project.entity_count * 5)));
    const healthColor = health > 70 ? 'var(--success)' : health > 40 ? 'var(--warning)' : 'var(--error)';

    return (
        <div className="card hoverable project-card" onClick={onClick}>
            <div className="project-bar active" />
            <div className="project-body">
                <div className="project-header">
                    <div>
                        <div className="project-name">{project.project_id}</div>
                        <div className="project-desc">Tenant: {project.tenant_hash}</div>
                    </div>
                    <Badge type="primary">Active</Badge>
                </div>

                <div className="layer-pills">
                    <div className="layer-pill" style={{ background: 'var(--episodic-light)' }}>
                        <div className="layer-pill-label" style={{ color: 'var(--episodic)' }}>Episodic</div>
                        <div className="layer-pill-value">{project.obs_count}</div>
                        <div className="layer-pill-unit">observations</div>
                    </div>
                    <div className="layer-pill" style={{ background: 'var(--semantic-light)' }}>
                        <div className="layer-pill-label" style={{ color: 'var(--semantic)' }}>Semantic</div>
                        <div className="layer-pill-value">{project.obs_count}</div>
                        <div className="layer-pill-unit">vectors</div>
                    </div>
                    <div className="layer-pill" style={{ background: 'var(--graph-light)' }}>
                        <div className="layer-pill-label" style={{ color: 'var(--graph)' }}>Graph</div>
                        <div className="layer-pill-value">{project.entity_count}</div>
                        <div className="layer-pill-unit">entities</div>
                    </div>
                </div>

                <div className="health-bar-header">
                    <span className="health-bar-label">Memory Health</span>
                    <span className="health-bar-value" style={{ color: healthColor }}>{health}%</span>
                </div>
                <div className="health-bar-track">
                    <div className="health-bar-fill" style={{ width: `${health}%`, background: healthColor }} />
                </div>

                {project.last_active && (
                    <div className="updated-text">
                        Last active: {new Date(project.last_active).toLocaleString()}
                    </div>
                )}
            </div>
        </div>
    );
}

// ── App Shell ──

export default function App() {
    const [screen, setScreen] = useState('home');
    const [project, setProject] = useState(null);
    const [isServerDown, setIsServerDown] = useState(false);

    // Check if server is reachable periodically
    useEffect(() => {
        const checkServer = () => {
            fetch(`${API}/api/projects`, { method: 'HEAD' })
                .then(() => setIsServerDown(false))
                .catch(() => setIsServerDown(true));
        };
        checkServer();
        const interval = setInterval(checkServer, 5000);
        return () => clearInterval(interval);
    }, []);

    const [apiKey, setApiKey] = useState(() => {
        const stored = localStorage.getItem('ml_api_key');
        if (!stored || stored === 'dev-key-123') {
            return 'skp_dev_key_12345';
        }
        return stored;
    });

    const navigate = useCallback((target) => {
        if (target === 'home') { setProject(null); }
        setScreen(target);
    }, []);

    const selectProject = useCallback((p) => {
        if (isServerDown) return;
        setProject(p);
        setScreen('project-detail');
    }, [isServerDown]);

    const openLayer = useCallback((layer) => {
        if (isServerDown && layer !== 'keys') return;
        setScreen(layer);
    }, [isServerDown]);

    // Save apiKey to localStorage
    useEffect(() => { localStorage.setItem('ml_api_key', apiKey); }, [apiKey]);

    const renderScreen = () => {
        switch (screen) {
            case 'home':
                return <HomeScreen onSelectProject={selectProject} apiKey={apiKey} setServerDown={setIsServerDown} />;

            case 'project-detail':
                return project ? (
                    <ProjectDetail
                        project={project}
                        apiKey={apiKey}
                        onNavigate={navigate}
                        onOpenLayer={openLayer}
                    />
                ) : null;

            case 'episodic':
                return project ? (
                    <>
                        <PageHeader
                            title="Episodic Log"
                            subtitle="Timeline of all agent actions"
                            breadcrumbs={[
                                { label: 'Projects', onClick: () => navigate('home') },
                                { label: project.project_id, onClick: () => navigate('project-detail') },
                                { label: 'Episodic Log' },
                            ]}
                        />
                        <div className="page-content fade-in">
                            <MemoryList projectId={project.tenant_hash} api={API} apiKey={apiKey} />
                        </div>
                    </>
                ) : null;

            case 'semantic':
                return project ? (
                    <>
                        <PageHeader
                            title="Semantic Search"
                            subtitle="Find memories by meaning"
                            breadcrumbs={[
                                { label: 'Projects', onClick: () => navigate('home') },
                                { label: project.project_id, onClick: () => navigate('project-detail') },
                                { label: 'Semantic Search' },
                            ]}
                        />
                        <div className="page-content fade-in">
                            <SearchView projectId={project.tenant_hash} api={API} apiKey={apiKey} />
                        </div>
                    </>
                ) : null;

            case 'graph':
                return project ? (
                    <>
                        <PageHeader
                            title="Knowledge Graph"
                            subtitle="Entity relationships and connections"
                            breadcrumbs={[
                                { label: 'Projects', onClick: () => navigate('home') },
                                { label: project.project_id, onClick: () => navigate('project-detail') },
                                { label: 'Knowledge Graph' },
                            ]}
                        />
                        <div className="page-content fade-in" style={{ padding: 0, flex: 1 }}>
                            <GraphView projectId={project.tenant_hash} api={API} apiKey={apiKey} />
                        </div>
                    </>
                ) : null;

            case 'keys':
                return (
                    <>
                        <PageHeader
                            title="API Keys"
                            subtitle="Manage authentication credentials"
                            breadcrumbs={[{ label: 'API Keys' }]}
                        />
                        <div className="page-content fade-in">
                            <KeyManager api={API} apiKey={apiKey} onApiKeyChange={setApiKey} />
                        </div>
                    </>
                );

            default:
                return <HomeScreen onSelectProject={selectProject} apiKey={apiKey} />;
        }
    };

    return (
        <div className="app-shell">
            <Sidebar screen={screen} onNavigate={navigate} />
            <div className="main-area">
                {isServerDown && (
                    <div style={{ backgroundColor: 'var(--error, #e53e3e)', color: 'white', padding: '12px 24px', textAlign: 'center', fontWeight: 600 }}>
                        ⚠️ Cannot connect to Memory Layer backend. The server might be down.
                    </div>
                )}
                {renderScreen()}
            </div>
        </div>
    );
}
