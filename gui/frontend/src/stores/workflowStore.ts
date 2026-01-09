import { create } from 'zustand'
import { Node, Edge, addEdge, applyNodeChanges, applyEdgeChanges } from '@xyflow/react'

interface WorkflowState {
  nodes: Node[]
  edges: Edge[]
  selectedNode: Node | null
  setNodes: (nodes: Node[]) => void
  setEdges: (edges: Edge[]) => void
  onNodesChange: (changes: any) => void
  onEdgesChange: (changes: any) => void
  onConnect: (connection: any) => void
  selectNode: (node: Node | null) => void
  addNode: (node: Node) => void
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNode: null,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  onNodesChange: (changes) => {
    set({ nodes: applyNodeChanges(changes, get().nodes) })
  },

  onEdgesChange: (changes) => {
    set({ edges: applyEdgeChanges(changes, get().edges) })
  },

  onConnect: (connection) => {
    set({ edges: addEdge(connection, get().edges) })
  },

  selectNode: (node) => set({ selectedNode: node }),

  addNode: (node) => set({ nodes: [...get().nodes, node] }),
}))
