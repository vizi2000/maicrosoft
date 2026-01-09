/**
 * WorkflowCanvas - Main React Flow canvas for visual workflow building
 * Primitives-first approach: drag particles from palette, connect them
 */

import { useCallback, useRef } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  useReactFlow,
  Connection,
  Edge,
  Node,
  NodeTypes,
  EdgeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { useWorkflowStore } from '../../stores/workflowStore'
import ParticleNode from './ParticleNode'
import TriggerNode from './TriggerNode'

// Custom node types
const nodeTypes: NodeTypes = {
  particle: ParticleNode,
  trigger: TriggerNode,
}

// Node colors by category
const categoryColors: Record<string, string> = {
  data: '#3b82f6',      // blue
  transform: '#8b5cf6', // purple
  control: '#f59e0b',   // amber
  storage: '#10b981',   // emerald
  messaging: '#ef4444', // red
  ai: '#6366f1',        // indigo
  observability: '#64748b', // slate
}

interface WorkflowCanvasProps {
  onNodeSelect?: (node: Node | null) => void
  readOnly?: boolean
}

export default function WorkflowCanvas({ onNodeSelect, readOnly = false }: WorkflowCanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition } = useReactFlow()

  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    selectNode,
    addNode,
  } = useWorkflowStore()

  // Handle node selection
  const handleNodeClick = useCallback((_: any, node: Node) => {
    selectNode(node)
    onNodeSelect?.(node)
  }, [selectNode, onNodeSelect])

  // Handle background click (deselect)
  const handlePaneClick = useCallback(() => {
    selectNode(null)
    onNodeSelect?.(null)
  }, [selectNode, onNodeSelect])

  // Handle drop from palette
  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault()

    const primitiveData = event.dataTransfer.getData('application/maicrosoft-primitive')
    if (!primitiveData) return

    const primitive = JSON.parse(primitiveData)

    // Get drop position
    const position = screenToFlowPosition({
      x: event.clientX,
      y: event.clientY,
    })

    // Create new node
    const newNode: Node = {
      id: `${primitive.id}-${Date.now()}`,
      type: 'particle',
      position,
      data: {
        primitive_id: primitive.id,
        name: primitive.name,
        category: primitive.category,
        inputs: {},
        color: categoryColors[primitive.category] || '#6b7280',
      },
    }

    addNode(newNode)
  }, [screenToFlowPosition, addNode])

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  // Validate connection
  const isValidConnection = useCallback((connection: Connection) => {
    // Prevent self-connections
    if (connection.source === connection.target) return false

    // Prevent duplicate connections
    const existingEdge = edges.find(
      (edge) =>
        edge.source === connection.source &&
        edge.target === connection.target
    )
    if (existingEdge) return false

    return true
  }, [edges])

  return (
    <div
      ref={reactFlowWrapper}
      className="w-full h-full"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={readOnly ? undefined : onNodesChange}
        onEdgesChange={readOnly ? undefined : onEdgesChange}
        onConnect={readOnly ? undefined : onConnect}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        isValidConnection={isValidConnection}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
        deleteKeyCode={readOnly ? null : ['Backspace', 'Delete']}
        className="bg-gray-50"
      >
        <Background gap={15} size={1} color="#e5e7eb" />
        <Controls />
        <MiniMap
          nodeColor={(node) => node.data?.color || '#6b7280'}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
        <Panel position="top-left">
          <div className="bg-white rounded-lg shadow px-3 py-2 text-sm text-gray-600">
            Drag particles from the palette to build your workflow
          </div>
        </Panel>
      </ReactFlow>
    </div>
  )
}
