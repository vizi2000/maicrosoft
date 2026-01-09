/**
 * NodeConfigPanel - Right panel for configuring selected node
 * Shows primitive interface and allows editing inputs
 */

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { XMarkIcon, InformationCircleIcon } from '@heroicons/react/24/outline'
import { Node } from '@xyflow/react'
import { primitivesApi } from '../../api/client'
import { useWorkflowStore } from '../../stores/workflowStore'

interface NodeConfigPanelProps {
  node: Node | null
  onClose: () => void
}

interface PrimitiveInterface {
  inputs: Array<{
    name: string
    type: string
    required: boolean
    description?: string
    default?: any
    enum?: string[]
  }>
  outputs: Array<{
    name: string
    type: string
    description?: string
  }>
}

export default function NodeConfigPanel({ node, onClose }: NodeConfigPanelProps) {
  const { nodes, setNodes } = useWorkflowStore()
  const [inputs, setInputs] = useState<Record<string, any>>({})

  // Fetch primitive definition
  const { data: primitive, isLoading } = useQuery({
    queryKey: ['primitive', node?.data?.primitive_id],
    queryFn: async () => {
      if (!node?.data?.primitive_id) return null
      const response = await primitivesApi.get(node.data.primitive_id)
      return response.data
    },
    enabled: !!node?.data?.primitive_id,
  })

  // Initialize inputs from node data
  useEffect(() => {
    if (node?.data?.inputs) {
      setInputs(node.data.inputs)
    }
  }, [node?.id])

  // Update node when inputs change
  const updateNodeInputs = (name: string, value: any) => {
    const newInputs = { ...inputs, [name]: value }
    setInputs(newInputs)

    // Update store
    setNodes(
      nodes.map((n) =>
        n.id === node?.id
          ? { ...n, data: { ...n.data, inputs: newInputs } }
          : n
      )
    )
  }

  if (!node) {
    return (
      <div className="w-80 bg-white border-l border-gray-200 p-4 flex items-center justify-center">
        <p className="text-gray-500 text-sm text-center">
          Select a node to configure
        </p>
      </div>
    )
  }

  const interfaceData: PrimitiveInterface = primitive?.interface || { inputs: [], outputs: [] }

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div>
          <h3 className="font-medium text-gray-900">{node.data.name}</h3>
          <p className="text-sm text-gray-500">{node.data.primitive_id}</p>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <XMarkIcon className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="text-center py-4 text-gray-500">Loading...</div>
        ) : (
          <>
            {/* Description */}
            {primitive?.description && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                <div className="flex gap-2">
                  <InformationCircleIcon className="w-5 h-5 text-blue-500 flex-shrink-0" />
                  <p className="text-sm text-blue-700">{primitive.description}</p>
                </div>
              </div>
            )}

            {/* Inputs */}
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Inputs</h4>
              {interfaceData.inputs.length === 0 ? (
                <p className="text-sm text-gray-500">No inputs required</p>
              ) : (
                interfaceData.inputs.map((input) => (
                  <div key={input.name}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {input.name}
                      {input.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    {input.description && (
                      <p className="text-xs text-gray-500 mb-1">{input.description}</p>
                    )}
                    {input.enum ? (
                      <select
                        value={inputs[input.name] || input.default || ''}
                        onChange={(e) => updateNodeInputs(input.name, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="">Select...</option>
                        {input.enum.map((opt) => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    ) : input.type === 'boolean' ? (
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={inputs[input.name] ?? input.default ?? false}
                          onChange={(e) => updateNodeInputs(input.name, e.target.checked)}
                          className="rounded border-gray-300 text-blue-500 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-600">Enabled</span>
                      </label>
                    ) : input.type === 'object' || input.type === 'array' ? (
                      <textarea
                        value={typeof inputs[input.name] === 'string'
                          ? inputs[input.name]
                          : JSON.stringify(inputs[input.name] || input.default || {}, null, 2)}
                        onChange={(e) => {
                          try {
                            updateNodeInputs(input.name, JSON.parse(e.target.value))
                          } catch {
                            updateNodeInputs(input.name, e.target.value)
                          }
                        }}
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="JSON..."
                      />
                    ) : (
                      <input
                        type={input.type === 'number' || input.type === 'integer' ? 'number' : 'text'}
                        value={inputs[input.name] ?? input.default ?? ''}
                        onChange={(e) => updateNodeInputs(input.name, e.target.value)}
                        placeholder={`Enter ${input.name}...`}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Outputs info */}
            {interfaceData.outputs.length > 0 && (
              <div className="mt-6 space-y-2">
                <h4 className="font-medium text-gray-900">Outputs</h4>
                {interfaceData.outputs.map((output) => (
                  <div key={output.name} className="text-sm">
                    <span className="font-mono text-blue-600">{output.name}</span>
                    <span className="text-gray-400 ml-2">: {output.type}</span>
                    {output.description && (
                      <p className="text-xs text-gray-500">{output.description}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Reference syntax help */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <p className="text-xs text-gray-600 font-medium mb-1">Reference syntax:</p>
        <code className="text-xs text-gray-500 block">
          {'{{ ref: node_id.output }}'}
        </code>
      </div>
    </div>
  )
}
