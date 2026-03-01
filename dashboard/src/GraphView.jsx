import { useState, useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

const NODE_COLORS = {
    file: '#3B82F6',
    function: '#F59E0B',
    component: '#EC4899',
    variable: '#10B981',
    entity: '#8B5CF6',
    unknown: '#6B7280',
};

const EDGE_COLORS = {
    CO_OCCURS: '#D1D5DB',
    CALLS: '#3B82F6',
    READS: '#10B981',
    WRITES: '#F59E0B',
    IMPORTS: '#8B5CF6',
    CONTAINS: '#6366F1',
    LOCATED_IN: '#6B7280',
    SENDS_TO: '#EC4899',
    TRIGGERS: '#EF4444',
    RETURNS: '#14B8A6',
    LOCKS: '#DC2626',
    CREATES: '#22C55E',
    FIXES: '#F97316',
    USES: '#A855F7',
    DEPENDS_ON: '#0EA5E9',
    EXTENDS: '#6366F1',
};

export default function GraphView({ projectId, api, apiKey }) {
    const containerRef = useRef(null);
    const cyRef = useRef(null);
    const [graphData, setGraphData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selected, setSelected] = useState(null);
    const [showDeprecated, setShowDeprecated] = useState(true);

    useEffect(() => {
        setLoading(true);
        fetch(`${api}/api/graph?project_id=${projectId}`, {
            headers: { 'X-Api-Key': apiKey }
        })
            .then(r => r.json())
            .then(data => { setGraphData(data); setLoading(false); })
            .catch(err => { setError(err.message); setLoading(false); });
    }, [projectId, api, apiKey]);

    useEffect(() => {
        if (!graphData || !containerRef.current || !cytoscape) return;

        const nodes = (graphData.nodes || []).map(n => ({
            data: {
                id: n.id || n.name,
                label: n.name || n.id,
                type: n.type || 'unknown',
                deprecated: !!n.invalidated_at,
                ...n,
            }
        }));

        const edges = (graphData.links || graphData.edges || []).map((e, i) => ({
            data: {
                id: `edge-${i}`,
                source: e.source,
                target: e.target,
                relationship: e.relationship || 'RELATED',
            }
        }));

        if (cyRef.current) cyRef.current.destroy();

        cyRef.current = cytoscape({
            container: containerRef.current,
            elements: [...nodes, ...edges],
            style: [
                {
                    selector: 'node',
                    style: {
                        label: 'data(label)',
                        'font-size': '11px',
                        'font-family': 'Inter, sans-serif',
                        color: '#111827',
                        'text-valign': 'bottom',
                        'text-margin-y': 8,
                        'background-color': (ele) => NODE_COLORS[ele.data('type')] || NODE_COLORS.unknown,
                        width: 32,
                        height: 32,
                        'border-width': 2,
                        'border-color': '#fff',
                    },
                },
                {
                    selector: 'node[?deprecated]',
                    style: { opacity: 0.3 },
                },
                {
                    selector: 'edge',
                    style: {
                        width: (ele) => ele.data('relationship') === 'CO_OCCURS' ? 1 : 2,
                        'line-color': (ele) => EDGE_COLORS[ele.data('relationship')] || '#D1D5DB',
                        'target-arrow-color': (ele) => EDGE_COLORS[ele.data('relationship')] || '#D1D5DB',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        label: 'data(relationship)',
                        'font-size': '8px',
                        color: (ele) => EDGE_COLORS[ele.data('relationship')] || '#9CA3AF',
                        'text-rotation': 'autorotate',
                        'text-margin-y': -10,
                        opacity: (ele) => ele.data('relationship') === 'CO_OCCURS' ? 0.4 : 0.85,
                    },
                },
            ],
            layout: {
                name: nodes.length > 20 ? 'cose' : 'cose',
                animate: true,
                animationDuration: 500,
                nodeRepulsion: 4500,
                idealEdgeLength: 100,
                padding: 40,
            },
        });

        cyRef.current.on('tap', 'node', (evt) => {
            const node = evt.target;
            const connections = node.connectedEdges().map(edge => ({
                relationship: edge.data('relationship'),
                source: edge.data('source'),
                target: edge.data('target'),
                direction: edge.data('source') === node.data('id') ? 'outgoing' : 'incoming',
                neighbor: edge.data('source') === node.data('id') ? edge.data('target') : edge.data('source'),
            }));
            setSelected({ ...node.data(), connections });
        });

        cyRef.current.on('tap', (evt) => {
            if (evt.target === cyRef.current) setSelected(null);
        });

        return () => { if (cyRef.current) cyRef.current.destroy(); };
    }, [graphData, showDeprecated]);

    if (loading) return <div className="loading">Loading graph…</div>;

    if (error || !graphData) {
        return (
            <div className="empty-state">
                <div className="empty-icon">🕸️</div>
                <div className="empty-title">No graph data yet</div>
                <div className="empty-desc">
                    The knowledge graph builds automatically from entity co-occurrence.<br />
                    Add observations with entities to see connections appear.
                </div>
            </div>
        );
    }

    const nodeCount = graphData.nodes?.length || 0;
    const edgeCount = (graphData.links || graphData.edges || []).length;

    if (nodeCount === 0) {
        return (
            <div className="empty-state">
                <div className="empty-icon">🕸️</div>
                <div className="empty-title">No entities yet</div>
                <div className="empty-desc">
                    Entities are extracted from observations automatically.<br />
                    Record observations with entity names to build the graph.
                </div>
            </div>
        );
    }

    const nodeTypes = [...new Set((graphData.nodes || []).map(n => n.type || 'unknown'))];

    return (
        <div className="graph-layout">
            <div className="graph-canvas">
                <div ref={containerRef} style={{ width: '100%', height: '100%', minHeight: 500 }} />

                {/* Legend */}
                <div className="graph-legend">
                    <div className="graph-legend-title">Legend</div>
                    {nodeTypes.map(type => (
                        <div key={type} className="graph-legend-item">
                            <div className="graph-legend-dot" style={{ background: NODE_COLORS[type] || NODE_COLORS.unknown }} />
                            <span className="graph-legend-label">{type}</span>
                        </div>
                    ))}
                    <div style={{ fontSize: 10, color: 'var(--text-secondary)', marginTop: 6 }}>
                        {nodeCount} nodes · {edgeCount} edges
                    </div>
                </div>

                {/* Hint */}
                {!selected && (
                    <div className="graph-hint">
                        💡 Click any node to inspect
                    </div>
                )}
            </div>

            {/* Inspector Panel */}
            <div className={`graph-inspector ${selected ? 'open' : ''}`}>
                {selected && (
                    <div className="inspector-inner">
                        <div className="inspector-header">
                            <span className="inspector-title">Node Inspector</span>
                            <button className="inspector-close" onClick={() => setSelected(null)}>✕</button>
                        </div>
                        <div className="inspector-body">
                            <div className="inspector-node-name">{selected.label || selected.name}</div>
                            <span className="badge" style={{
                                background: (NODE_COLORS[selected.type] || NODE_COLORS.unknown) + '18',
                                color: NODE_COLORS[selected.type] || NODE_COLORS.unknown,
                            }}>{selected.type}</span>

                            {selected.created_at && (
                                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 10 }}>
                                    Created: {new Date(selected.created_at).toLocaleString()}
                                </div>
                            )}

                            {selected.invalidated_at && (
                                <div style={{ fontSize: 12, color: 'var(--error)', marginTop: 4 }}>
                                    ⚠️ Deprecated: {new Date(selected.invalidated_at).toLocaleString()}
                                </div>
                            )}

                            {selected.connections?.length > 0 && (
                                <>
                                    <div className="inspector-section-label">
                                        Connections ({selected.connections.length})
                                    </div>
                                    {selected.connections.map((c, i) => (
                                        <div key={i} className="inspector-connection">
                                            <div className="inspector-conn-dir">
                                                {c.direction === 'outgoing' ? '→ Outgoing' : '← Incoming'}
                                            </div>
                                            <div className="inspector-conn-name">{c.neighbor}</div>
                                            <span className="badge" style={{ fontSize: 10 }}>{c.relationship}</span>
                                        </div>
                                    ))}
                                </>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
