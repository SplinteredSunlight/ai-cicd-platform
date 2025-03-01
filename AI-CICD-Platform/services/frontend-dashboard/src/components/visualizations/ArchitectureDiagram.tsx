import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, CircularProgress, useTheme, useMediaQuery, Tabs, Tab } from '@mui/material';
import mermaid from 'mermaid';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: true,
  theme: 'neutral',
  securityLevel: 'loose',
  fontFamily: 'Roboto, sans-serif',
});

interface ArchitectureDiagramProps {
  data: {
    diagrams: DiagramData[];
    currentService?: string;
    lastUpdated?: string;
  };
  isLoading?: boolean;
  height?: number | string;
  width?: number | string;
}

export interface DiagramData {
  id: string;
  name: string;
  description?: string;
  definition: string;
  type: 'system' | 'service' | 'component' | 'sequence' | 'class';
  service?: string;
  lastUpdated?: string;
}

const ArchitectureDiagram: React.FC<ArchitectureDiagramProps> = ({
  data,
  isLoading = false,
  height = '100%',
  width = '100%',
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  
  const [activeTab, setActiveTab] = useState(0);
  const [renderedSvg, setRenderedSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const diagramRef = useRef<HTMLDivElement>(null);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Render mermaid diagram
  useEffect(() => {
    const renderDiagram = async () => {
      if (!data?.diagrams || data.diagrams.length === 0 || isLoading) {
        return;
      }

      try {
        setError(null);
        const currentDiagram = data.diagrams[activeTab];
        
        if (!currentDiagram) {
          setError('Diagram not found');
          return;
        }

        // Generate unique ID for this render
        const id = `diagram-${currentDiagram.id}-${Date.now()}`;
        
        // Create temporary container
        const tempContainer = document.createElement('div');
        tempContainer.id = id;
        tempContainer.style.display = 'none';
        document.body.appendChild(tempContainer);
        
        // Add the diagram definition
        tempContainer.innerHTML = `<div class="mermaid">${currentDiagram.definition}</div>`;
        
        // Render the diagram
        await mermaid.run();
        
        // Get the SVG content
        const svgContent = tempContainer.querySelector('.mermaid svg');
        if (svgContent) {
          // Add responsive attributes to SVG
          svgContent.setAttribute('width', '100%');
          svgContent.setAttribute('height', '100%');
          svgContent.setAttribute('preserveAspectRatio', 'xMidYMid meet');
          
          // Set the rendered SVG
          setRenderedSvg(tempContainer.innerHTML);
        } else {
          setError('Failed to render diagram');
        }
        
        // Clean up
        document.body.removeChild(tempContainer);
      } catch (err) {
        console.error('Error rendering diagram:', err);
        setError(`Error rendering diagram: ${err instanceof Error ? err.message : String(err)}`);
      }
    };

    renderDiagram();
  }, [data, activeTab, isLoading]);

  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height,
          width,
        }}
      >
        <CircularProgress size={isMobile ? 30 : 40} />
      </Box>
    );
  }

  if (!data?.diagrams || data.diagrams.length === 0) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height,
          width,
          p: 2,
        }}
      >
        <Typography color="text.secondary" variant={isMobile ? 'body2' : 'body1'}>
          No architecture diagrams available
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height, width, display: 'flex', flexDirection: 'column' }}>
      {data.diagrams.length > 1 && (
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant={isMobile ? 'scrollable' : 'standard'}
          scrollButtons={isMobile ? 'auto' : false}
          sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}
        >
          {data.diagrams.map((diagram, index) => (
            <Tab
              key={diagram.id}
              label={diagram.name}
              id={`diagram-tab-${index}`}
              aria-controls={`diagram-tabpanel-${index}`}
              sx={{ 
                fontSize: isMobile ? '0.75rem' : '0.875rem',
                minWidth: isMobile ? 'auto' : 120
              }}
            />
          ))}
        </Tabs>
      )}

      {error ? (
        <Box
          sx={{
            p: 2,
            border: '1px solid',
            borderColor: 'error.main',
            borderRadius: 1,
            bgcolor: 'error.light',
            color: 'error.dark',
            flexGrow: 1,
            overflow: 'auto',
          }}
        >
          <Typography variant="body2" fontFamily="monospace" whiteSpace="pre-wrap">
            {error}
          </Typography>
        </Box>
      ) : (
        <Box
          ref={diagramRef}
          sx={{
            flexGrow: 1,
            overflow: 'auto',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            p: 1,
          }}
          dangerouslySetInnerHTML={{ __html: renderedSvg || '' }}
        />
      )}

      {data.diagrams[activeTab]?.description && (
        <Box sx={{ mt: 2, p: 1, borderTop: 1, borderColor: 'divider' }}>
          <Typography variant={isMobile ? 'caption' : 'body2'} color="text.secondary">
            {data.diagrams[activeTab].description}
          </Typography>
        </Box>
      )}

      {data.diagrams[activeTab]?.lastUpdated && (
        <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
          <Typography variant="caption" color="text.secondary">
            Last updated: {new Date(data.diagrams[activeTab].lastUpdated).toLocaleString()}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default ArchitectureDiagram;
