import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import cytoscape from 'cytoscape';

// Node colors by type
const NODE_COLORS = {
    file: '#63b3ed',
    function: '#b794f4',
    component: '#68d391',
    variable: '#f6ad55',
    unknown: '#94a3b8',
};

// Edge colors by relationship
const EDGE_COLORS = {
    CALLS: '#63b3ed',
    IMPORTS: '#68d391',
    INVOKES_IPC: '#f6ad55',
    MODIFIES_STATE: '#fc8181',
    RENDERS: '#b794f4',
    DEPENDS_ON: '#76e4f7',
    DEPRECATED_BY: '#64748b',
};

export default function GraphView({ apiKey, projectId, apiUrl }) {
    const containerRef = useRef(null);
    const cyRef = useRef(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [stats, setStats] = useState({ nodes: 0, edges: 0 });

    useEffect(() => {
        if (!projectId) return;

        const fetchGraph = async () => {
            setLoading(true);
            setError(null);

            try {
                const res = await axios.get(`${apiUrl}/graph`, {
                    params: { project_id: projectId },
                    headers: { 'X-Api-Key': apiKey },
                });

                const { nodes, edges } = res.data;
                setStats({ nodes: nodes.length, edges: edges.length });

                // Convert to Cytoscape elements
                const elements = [];

                nodes.forEach((node) => {
                    const isInvalidated = node.invalidated_at !== null;
                    elements.push({
                        data: {
                            id: node.name,
                            label: node.name,
                            type: node.type || 'unknown',
                            isInvalidated,
                        },
                    });
                });

                edges.forEach((edge, i) => {
                    const isInvalidated = edge.invalidated_at !== null;
                    elements.push({
                        data: {
                            id: `e${i}`,
                            source: edge.source,
                            target: edge.target,
                            label: edge.relationship || '',
                            isInvalidated,
                        },
                    });
                });

                // Initialize Cytoscape
                if (cyRef.current) {
                    cyRef.current.destroy();
                }

                cyRef.current = cytoscape({
                    container: containerRef.current,
                    elements,
                    style: [
                        {
                            selector: 'node',
                            style: {
                                label: 'data(label)',
                                'background-color': (ele) =>
                                    NODE_COLORS[ele.data('type')] || NODE_COLORS.unknown,
                                color: '#e2e8f0',
                                'text-valign': 'bottom',
                                'text-margin-y': 8,
                                'font-size': 11,
                                'font-family': 'Inter, sans-serif',
                                width: 40,
                                height: 40,
                                'border-width': 2,
                                'border-color': (ele) =>
                                    ele.data('isInvalidated') ? '#64748b' : 'transparent',
                                'border-style': (ele) =>
                                    ele.data('isInvalidated') ? 'dashed' : 'solid',
                                opacity: (ele) => (ele.data('isInvalidated') ? 0.4 : 1),
                            },
                        },
                        {
                            selector: 'edge',
                            style: {
                                label: 'data(label)',
                                'line-color': (ele) =>
                                    EDGE_COLORS[ele.data('label')] || '#64748b',
                                'target-arrow-color': (ele) =>
                                    EDGE_COLORS[ele.data('label')] || '#64748b',
                                'target-arrow-shape': 'triangle',
                                'curve-style': 'bezier',
                                'font-size': 9,
                                color: '#94a3b8',
                                'text-rotation': 'autorotate',
                                'text-margin-y': -10,
                                width: 2,
                                opacity: (ele) => (ele.data('isInvalidated') ? 0.3 : 0.8),
                                'line-style': (ele) =>
                                    ele.data('isInvalidated') ? 'dashed' : 'solid',
                            },
                        },
                        {
                            selector: 'node:selected',
                            style: {
                                'border-width': 3,
                                'border-color': '#63b3ed',
                                'box-shadow': '0 0 20px rgba(99, 179, 237, 0.5)',
                            },
                        },
                    ],
                    layout: {
                        name: elements.length > 0 ? 'cose' : 'grid',
                        animate: true,
                        animationDuration: 500,
                        nodeRepulsion: 8000,
                        idealEdgeLength: 120,
                        padding: 40,
                    },
                });
            } catch (err) {
                if (err.response?.status !== 401) {
                    setError('Failed to load graph data');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchGraph();

        return () => {
            if (cyRef.current) {
                cyRef.current.destroy();
            }
        };
    }, [projectId, apiKey, apiUrl]);

    if (loading) {
        return (
            <div className="graph-container">
                <div className="loading">Loading knowledge graph...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="graph-container">
                <div className="empty-state">
                    <span className="icon">⚠️</span>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div style={{ position: 'relative' }}>
            <div
                style={{
                    position: 'absolute',
                    top: 12,
                    right: 16,
                    zIndex: 10,
                    fontSize: 12,
                    color: 'var(--text-muted)',
                    background: 'rgba(10, 14, 23, 0.8)',
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-sm)',
                    backdropFilter: 'blur(10px)',
                }}
            >
                {stats.nodes} nodes • {stats.edges} edges
            </div>
            <div ref={containerRef} className="graph-container" />
        </div>
    );
}
