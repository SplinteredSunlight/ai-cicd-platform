import React, { useEffect, useRef, useState } from 'react';
import { ForceGraph2D } from 'react-force-graph';
import { Select, Slider, Switch, Card, Row, Col, Button, Tooltip, Spin, Typography } from 'antd';
import { DownloadOutlined, FullscreenOutlined, FilterOutlined, ReloadOutlined } from '@ant-design/icons';
import { DependencyGraphData, DependencyNode, DependencyLink } from '../../types/dependency-types';

const { Option } = Select;
const { Title, Text } = Typography;

interface DependencyGraphProps {
  projectPath: string;
  data?: DependencyGraphData;
  loading?: boolean;
  onRefresh?: () => void;
  onFilterChange?: (filters: DependencyGraphFilters) => void;
}

export interface DependencyGraphFilters {
  nodeTypes: string[];
  edgeTypes: string[];
  maxNodes: number;
  groupBy?: string;
  layout: string;
}

const NODE_COLORS: Record<string, string> = {
  file: '#4CAF50',      // Green
  package: '#2196F3',   // Blue
  class: '#FFC107',     // Yellow
  function: '#F44336',  // Red
  component: '#9C27B0', // Purple
  custom: '#607D8B',    // Gray
  default: '#607D8B'    // Default Gray
};

const DependencyGraph: React.FC<DependencyGraphProps> = ({
  projectPath,
  data,
  loading = false,
  onRefresh,
  onFilterChange
}) => {
  const graphRef = useRef<any>();
  const [filters, setFilters] = useState<DependencyGraphFilters>({
    nodeTypes: ['all'],
    edgeTypes: ['all'],
    maxNodes: 100,
    layout: 'force'
  });
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<DependencyNode | null>(null);
  const [graphWidth, setGraphWidth] = useState<number>(800);
  const [graphHeight, setGraphHeight] = useState<number>(600);
  const containerRef = useRef<HTMLDivElement>(null);

  // Update graph dimensions when container size changes
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setGraphWidth(containerRef.current.clientWidth);
        setGraphHeight(containerRef.current.clientHeight);
      }
    };

    window.addEventListener('resize', updateDimensions);
    updateDimensions();

    return () => {
      window.removeEventListener('resize', updateDimensions);
    };
  }, []);

  // Handle filter changes
  const handleFilterChange = (newFilters: Partial<DependencyGraphFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    
    if (onFilterChange) {
      onFilterChange(updatedFilters);
    }
  };

  // Handle node click
  const handleNodeClick = (node: DependencyNode) => {
    setSelectedNode(node === selectedNode ? null : node);
    
    if (node) {
      // Highlight connected nodes and links
      const connectedNodes = new Set<string>();
      const connectedLinks = new Set<string>();
      
      connectedNodes.add(node.id);
      
      // Add dependencies
      if (data) {
        data.links.forEach(link => {
          if (link.source === node.id || (link.source as any).id === node.id) {
            connectedNodes.add(typeof link.target === 'string' ? link.target : link.target.id);
            connectedLinks.add(`${link.source}-${link.target}`);
          }
          if (link.target === node.id || (link.target as any).id === node.id) {
            connectedNodes.add(typeof link.source === 'string' ? link.source : link.source.id);
            connectedLinks.add(`${link.source}-${link.target}`);
          }
        });
      }
      
      setHighlightNodes(connectedNodes);
      setHighlightLinks(connectedLinks);
    } else {
      // Clear highlights
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  };

  // Handle node right-click
  const handleNodeRightClick = (node: DependencyNode) => {
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 1000);
      graphRef.current.zoom(2, 1000);
    }
  };

  // Handle graph reset
  const handleResetGraph = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
    setSelectedNode(null);
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
  };

  // Get node color based on type and highlight status
  const getNodeColor = (node: DependencyNode) => {
    const isHighlighted = highlightNodes.size === 0 || highlightNodes.has(node.id);
    const baseColor = NODE_COLORS[node.type] || NODE_COLORS.default;
    
    return isHighlighted ? baseColor : `${baseColor}33`; // Add transparency if not highlighted
  };

  // Get link color based on type and highlight status
  const getLinkColor = (link: DependencyLink) => {
    const source = typeof link.source === 'string' ? link.source : link.source.id;
    const target = typeof link.target === 'string' ? link.target : link.target.id;
    const linkId = `${source}-${target}`;
    
    const isHighlighted = highlightLinks.size === 0 || highlightLinks.has(linkId);
    
    return isHighlighted ? '#666' : '#66666633'; // Gray with transparency if not highlighted
  };

  // Get node label
  const getNodeLabel = (node: DependencyNode) => {
    return node.label || node.id.split(':').pop() || node.id;
  };

  // Get available node types from data
  const getNodeTypes = () => {
    if (!data) return [];
    
    const types = new Set<string>();
    data.nodes.forEach(node => {
      if (node.type) {
        types.add(node.type);
      }
    });
    
    return Array.from(types);
  };

  // Get available edge types from data
  const getEdgeTypes = () => {
    if (!data) return [];
    
    const types = new Set<string>();
    data.links.forEach(link => {
      if (link.type) {
        types.add(link.type);
      }
    });
    
    return Array.from(types);
  };

  // Export graph as image
  const exportAsImage = () => {
    if (graphRef.current) {
      const canvas = document.querySelector('canvas');
      if (canvas) {
        const link = document.createElement('a');
        link.download = 'dependency-graph.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
      }
    }
  };

  return (
    <div className="dependency-graph-container" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Card size="small" style={{ marginBottom: '16px' }}>
        <Row gutter={16} align="middle">
          <Col span={24} md={12} lg={16}>
            <Title level={4} style={{ margin: 0 }}>Dependency Graph: {projectPath}</Title>
          </Col>
          <Col span={24} md={12} lg={8} style={{ textAlign: 'right' }}>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={onRefresh} 
              style={{ marginRight: '8px' }}
              disabled={loading}
            >
              Refresh
            </Button>
            <Button 
              icon={<DownloadOutlined />} 
              onClick={exportAsImage}
              style={{ marginRight: '8px' }}
              disabled={!data || loading}
            >
              Export
            </Button>
            <Button 
              icon={<FullscreenOutlined />} 
              onClick={handleResetGraph}
              disabled={!data || loading}
            >
              Reset
            </Button>
          </Col>
        </Row>
      </Card>
      
      <Row gutter={16}>
        <Col span={24} lg={18}>
          <Card 
            size="small" 
            style={{ height: 'calc(100vh - 200px)', minHeight: '500px', position: 'relative' }}
            bodyStyle={{ padding: 0, height: '100%' }}
            ref={containerRef}
          >
            {loading ? (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <Spin size="large" tip="Loading dependency graph..." />
              </div>
            ) : data ? (
              <ForceGraph2D
                ref={graphRef}
                graphData={data}
                nodeId="id"
                nodeLabel={getNodeLabel}
                nodeColor={getNodeColor}
                nodeRelSize={6}
                linkColor={getLinkColor}
                linkDirectionalArrowLength={3}
                linkDirectionalArrowRelPos={1}
                linkCurvature={0.25}
                linkWidth={link => highlightLinks.has(`${link.source}-${link.target}`) ? 2 : 1}
                onNodeClick={handleNodeClick}
                onNodeRightClick={handleNodeRightClick}
                width={graphWidth}
                height={graphHeight}
                cooldownTicks={100}
                onEngineStop={() => graphRef.current?.zoomToFit(400)}
              />
            ) : (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <Text type="secondary">No dependency data available</Text>
              </div>
            )}
          </Card>
        </Col>
        
        <Col span={24} lg={6}>
          <Card size="small" title="Filters" style={{ marginBottom: '16px' }}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>Node Types:</label>
              <Select
                mode="multiple"
                style={{ width: '100%' }}
                placeholder="Select node types"
                value={filters.nodeTypes}
                onChange={value => handleFilterChange({ nodeTypes: value })}
                disabled={loading}
              >
                <Option value="all">All Types</Option>
                {getNodeTypes().map(type => (
                  <Option key={type} value={type}>
                    <span style={{ 
                      display: 'inline-block', 
                      width: '12px', 
                      height: '12px', 
                      backgroundColor: NODE_COLORS[type] || NODE_COLORS.default,
                      marginRight: '8px',
                      borderRadius: '2px'
                    }}></span>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </Option>
                ))}
              </Select>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>Edge Types:</label>
              <Select
                mode="multiple"
                style={{ width: '100%' }}
                placeholder="Select edge types"
                value={filters.edgeTypes}
                onChange={value => handleFilterChange({ edgeTypes: value })}
                disabled={loading}
              >
                <Option value="all">All Types</Option>
                {getEdgeTypes().map(type => (
                  <Option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
                  </Option>
                ))}
              </Select>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>Max Nodes: {filters.maxNodes}</label>
              <Slider
                min={10}
                max={500}
                step={10}
                value={filters.maxNodes}
                onChange={value => handleFilterChange({ maxNodes: value as number })}
                disabled={loading}
              />
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>Group By:</label>
              <Select
                style={{ width: '100%' }}
                placeholder="Group nodes by"
                value={filters.groupBy}
                onChange={value => handleFilterChange({ groupBy: value })}
                allowClear
                disabled={loading}
              >
                <Option value="type">Type</Option>
                <Option value="language">Language</Option>
              </Select>
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '8px' }}>Layout:</label>
              <Select
                style={{ width: '100%' }}
                value={filters.layout}
                onChange={value => handleFilterChange({ layout: value })}
                disabled={loading}
              >
                <Option value="force">Force-Directed</Option>
                <Option value="radial">Radial</Option>
                <Option value="dagre">Hierarchical</Option>
              </Select>
            </div>
          </Card>
          
          {selectedNode && (
            <Card size="small" title="Node Details">
              <div style={{ marginBottom: '8px' }}>
                <Text strong>ID:</Text> {selectedNode.id}
              </div>
              <div style={{ marginBottom: '8px' }}>
                <Text strong>Type:</Text> {selectedNode.type}
              </div>
              {selectedNode.attributes && (
                <>
                  {selectedNode.attributes.name && (
                    <div style={{ marginBottom: '8px' }}>
                      <Text strong>Name:</Text> {selectedNode.attributes.name}
                    </div>
                  )}
                  {selectedNode.attributes.language && (
                    <div style={{ marginBottom: '8px' }}>
                      <Text strong>Language:</Text> {selectedNode.attributes.language}
                    </div>
                  )}
                  {selectedNode.attributes.path && (
                    <div style={{ marginBottom: '8px' }}>
                      <Text strong>Path:</Text> {selectedNode.attributes.path}
                    </div>
                  )}
                  {selectedNode.attributes.version && (
                    <div style={{ marginBottom: '8px' }}>
                      <Text strong>Version:</Text> {selectedNode.attributes.version}
                    </div>
                  )}
                </>
              )}
            </Card>
          )}
          
          {data && (
            <Card size="small" title="Statistics" style={{ marginTop: '16px' }}>
              <div style={{ marginBottom: '8px' }}>
                <Text strong>Total Nodes:</Text> {data.nodes.length}
              </div>
              <div style={{ marginBottom: '8px' }}>
                <Text strong>Total Links:</Text> {data.links.length}
              </div>
              {data.stats && (
                <>
                  {data.stats.nodeTypes && (
                    <div style={{ marginBottom: '8px' }}>
                      <Text strong>Node Types:</Text>
                      <ul style={{ margin: '4px 0 0 0', paddingLeft: '20px' }}>
                        {Object.entries(data.stats.nodeTypes).map(([type, count]) => (
                          <li key={type}>
                            {type}: {count}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {data.stats.edgeTypes && (
                    <div>
                      <Text strong>Edge Types:</Text>
                      <ul style={{ margin: '4px 0 0 0', paddingLeft: '20px' }}>
                        {Object.entries(data.stats.edgeTypes).map(([type, count]) => (
                          <li key={type}>
                            {type}: {count}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              )}
            </Card>
          )}
        </Col>
      </Row>
    </div>
  );
};

export default DependencyGraph;
