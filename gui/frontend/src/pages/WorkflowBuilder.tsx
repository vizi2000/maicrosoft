/**
 * WorkflowBuilder - Main page for visual workflow building
 * Primitives-first approach: no YAML editing, pure visual
 */

import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ReactFlowProvider } from '@xyflow/react'
import {
  PlayIcon,
  CheckIcon,
  CloudArrowUpIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline'
import { Node } from '@xyflow/react'

import WorkflowCanvas from '../components/workflow/WorkflowCanvas'
import NodePalette from '../components/workflow/NodePalette'
import NodeConfigPanel from '../components/workflow/NodeConfigPanel'
import { useWorkflowStore } from '../stores/workflowStore'
import { plansApi, validationApi, compileApi } from '../api/client'

export default function WorkflowBuilder() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { nodes, edges, setNodes, setEdges } = useWorkflowStore()
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [planName, setPlanName] = useState('New Workflow')
  const [isSaving, setIsSaving] = useState(false)
  const [validationResult, setValidationResult] = useState<any>(null)

  // Load existing plan if editing
  useQuery({
    queryKey: ['plan', id],
    queryFn: async () => {
      if (!id || id === 'new') return null
      const response = await plansApi.get(id)
      const plan = response.data
      setPlanName(plan.plan?.name || plan.name || 'Workflow')
      if (plan.version?.canvas_json) {
        setNodes(plan.version.canvas_json.nodes || [])
        setEdges(plan.version.canvas_json.edges || [])
      }
      return plan
    },
    enabled: !!id && id !== 'new',
  })

  // Validate mutation
  const validateMutation = useMutation({
    mutationFn: async () => {
      const planJson = buildPlanJson()
      const response = await validationApi.validate(planJson)
      return response.data
    },
    onSuccess: (data) => setValidationResult(data),
  })

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async () => {
      if (id && id !== 'new') {
        await plansApi.update(id, { name: planName })
        return { id }
      } else {
        const response = await plansApi.create({
          name: planName,
          description: `Visual workflow with ${nodes.length} nodes`,
        })
        return response.data
      }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      if (!id || id === 'new') {
        navigate(`/workflows/${data.id || data.plan?.id}`)
      }
    },
  })

  // Compile mutation
  const compileMutation = useMutation({
    mutationFn: async () => {
      const planJson = buildPlanJson()
      const response = await compileApi.compile(planJson)
      return response.data
    },
  })

  // Build Plan JSON from canvas
  const buildPlanJson = useCallback(() => {
    const triggerNode = nodes.find((n) => n.type === 'trigger')
    return {
      metadata: {
        id: id || `plan-${Date.now()}`,
        name: planName,
        version: '1.0.0',
      },
      settings: { allow_fallback: false, risk_level: 'low' },
      trigger: {
        type: triggerNode?.data?.trigger_type || 'manual',
        config: triggerNode?.data?.config || {},
      },
      nodes: nodes
        .filter((n) => n.type !== 'trigger')
        .map((n) => ({
          id: n.id,
          primitive_id: n.data.primitive_id,
          inputs: n.data.inputs || {},
        })),
      edges: edges.map((e) => ({
        from_node: e.source,
        to_node: e.target,
      })),
    }
  }, [nodes, edges, id, planName])

  return (
    <ReactFlowProvider>
      <div className="h-screen flex flex-col bg-gray-100">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate('/workflows')} className="p-2 hover:bg-gray-100 rounded-lg">
              <ArrowLeftIcon className="w-5 h-5 text-gray-600" />
            </button>
            <input
              type="text"
              value={planName}
              onChange={(e) => setPlanName(e.target.value)}
              className="text-lg font-semibold bg-transparent border-none focus:ring-0 focus:outline-none"
              placeholder="Workflow name..."
            />
          </div>
          <div className="flex items-center gap-2">
            {validationResult && (
              <div className={`px-3 py-1.5 rounded-lg text-sm ${validationResult.valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                {validationResult.valid ? 'Valid' : `${validationResult.errors?.length || 0} errors`}
              </div>
            )}
            <button onClick={() => validateMutation.mutate()} disabled={validateMutation.isPending} className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50">
              <CheckIcon className="w-4 h-4" />
              {validateMutation.isPending ? 'Validating...' : 'Validate'}
            </button>
            <button onClick={() => { setIsSaving(true); saveMutation.mutate(undefined, { onSettled: () => setIsSaving(false) }) }} disabled={isSaving} className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50">
              <CloudArrowUpIcon className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save'}
            </button>
            <button onClick={() => compileMutation.mutate()} disabled={compileMutation.isPending} className="flex items-center gap-2 px-4 py-2 text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50">
              <PlayIcon className="w-4 h-4" />
              {compileMutation.isPending ? 'Compiling...' : 'Run'}
            </button>
          </div>
        </header>

        {/* Main content */}
        <div className="flex-1 flex overflow-hidden">
          <NodePalette />
          <div className="flex-1">
            <WorkflowCanvas onNodeSelect={setSelectedNode} />
          </div>
          <NodeConfigPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
        </div>

        {/* Validation errors */}
        {validationResult && !validationResult.valid && (
          <div className="bg-red-50 border-t border-red-200 p-4">
            <h4 className="font-medium text-red-800 mb-2">Validation Errors:</h4>
            <ul className="space-y-1">
              {validationResult.errors?.map((err: any, i: number) => (
                <li key={i} className="text-sm text-red-700">[{err.code}] {err.message}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Compiled output modal */}
        {compileMutation.isSuccess && compileMutation.data && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-hidden">
              <div className="p-4 border-b flex items-center justify-between">
                <h3 className="font-semibold">Compiled N8N Workflow</h3>
                <button onClick={() => compileMutation.reset()} className="text-gray-500 hover:text-gray-700">Close</button>
              </div>
              <pre className="p-4 overflow-auto max-h-[60vh] text-sm bg-gray-50">
                {JSON.stringify(compileMutation.data, null, 2)}
              </pre>
              <div className="p-4 border-t flex justify-end">
                <button onClick={() => navigator.clipboard.writeText(JSON.stringify(compileMutation.data, null, 2))} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Copy to Clipboard
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ReactFlowProvider>
  )
}
