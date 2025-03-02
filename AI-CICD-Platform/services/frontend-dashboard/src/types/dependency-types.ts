/**
 * Types for dependency graph visualization
 */

/**
 * Dependency graph node
 */
export interface DependencyNode {
  id: string;
  label?: string;
  type: string;
  group?: number;
  attributes?: {
    name?: string;
    language?: string;
    path?: string;
    version?: string;
    [key: string]: any;
  };
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

/**
 * Dependency graph link
 */
export interface DependencyLink {
  source: string | DependencyNode;
  target: string | DependencyNode;
  type?: string;
  attributes?: {
    is_direct?: boolean;
    type?: string;
    [key: string]: any;
  };
}

/**
 * Dependency graph data
 */
export interface DependencyGraphData {
  nodes: DependencyNode[];
  links: DependencyLink[];
  stats?: {
    total_nodes?: number;
    total_edges?: number;
    nodeTypes?: Record<string, number>;
    edgeTypes?: Record<string, number>;
    connectivity?: {
      average_degree?: number;
      max_in_degree?: number;
      max_out_degree?: number;
      highly_connected_nodes?: Array<{
        node_id: string;
        in_degree: number;
        out_degree: number;
        total_degree: number;
      }>;
    };
    complexity?: {
      cyclomatic_complexity?: number;
      dependency_depth?: number;
      dependency_cycles?: string[][];
    };
  };
}

/**
 * Dependency analysis request
 */
export interface DependencyAnalysisRequest {
  project_path: string;
  languages?: string[];
  include_patterns?: string[];
  exclude_patterns?: string[];
  analyze_imports?: boolean;
  analyze_function_calls?: boolean;
  analyze_class_hierarchy?: boolean;
  analyze_packages?: boolean;
  max_depth?: number;
}

/**
 * Dependency analysis response
 */
export interface DependencyAnalysisResponse {
  dependency_graph: DependencyGraphData;
  code_dependencies: Record<string, any>;
  package_dependencies: Record<string, any>;
  metrics: {
    total_files: number;
    analyzed_files: number;
    import_count: number;
    function_call_count: number;
    class_count: number;
    total_packages: number;
    direct_dependencies: number;
    transitive_dependencies: number;
    dev_dependencies: number;
  };
}

/**
 * Impact analysis request
 */
export interface ImpactAnalysisRequest {
  project_path: string;
  changed_files: string[];
}

/**
 * Impact analysis response
 */
export interface ImpactAnalysisResponse {
  affected_files: string[];
  affected_packages: string[];
  affected_components: string[];
  impact_graph: {
    nodes: Array<{
      id: string;
      type: string;
      impact_level: 'direct' | 'indirect';
      attributes: Record<string, any>;
    }>;
    edges: Array<{
      source: string;
      target: string;
      type: string;
      attributes: Record<string, any>;
    }>;
  };
  metrics: {
    total_affected_files: number;
    total_affected_packages: number;
    total_affected_components: number;
    direct_impacts: number;
    indirect_impacts: number;
    high_risk_impacts: number;
  };
  risk_assessment: {
    overall_risk: 'low' | 'medium' | 'high';
    risk_factors: Array<{
      factor: string;
      description: string;
      severity: 'low' | 'medium' | 'high';
    }>;
    high_risk_nodes: Array<{
      id: string;
      name: string;
      type: string;
      dependents_count: number;
    }>;
  };
  test_recommendations: {
    recommended_tests: Array<{
      file: string;
      tests: string[];
    }>;
    test_coverage: {
      unit_tests: string[];
      integration_tests: string[];
      end_to_end_tests: string[];
    };
  };
}

/**
 * Build optimization request
 */
export interface BuildOptimizationRequest {
  project_path: string;
  changed_files?: string[];
  max_parallel_jobs?: number;
}

/**
 * Build order optimization response
 */
export interface BuildOrderOptimizationResponse {
  build_order: string[];
  critical_path: string[];
  metrics: {
    total_nodes: number;
    critical_path_length: number;
    max_depth: number;
  };
}

/**
 * Parallel execution optimization response
 */
export interface ParallelExecutionOptimizationResponse {
  parallel_groups: string[][];
  execution_plan: string[][];
  metrics: {
    total_nodes: number;
    total_groups: number;
    estimated_time: number;
  };
}

/**
 * Visualization options
 */
export interface VisualizationOptions {
  layout: string;
  include_node_types: string[];
  include_edge_types: string[];
  group_by?: string;
  max_nodes: number;
}

/**
 * Visualization response
 */
export interface VisualizationResponse {
  format: string;
  data: DependencyGraphData;
  layout: string;
  stats: {
    total_nodes: number;
    total_edges: number;
    visible_nodes: number;
    visible_edges: number;
  };
}
