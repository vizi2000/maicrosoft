/**
 * ParticleNode - Custom node component for particles (P001-P018)
 * Displays particle info with validation status
 */

import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import {
  GlobeAltIcon,
  CircleStackIcon,
  DocumentIcon,
  ArrowPathIcon,
  ArrowsRightLeftIcon,
  ArrowPathRoundedSquareIcon,
  CpuChipIcon,
  ArchiveBoxIcon,
  QueueListIcon,
  DocumentTextIcon,
  CodeBracketIcon,
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

// Icons for each particle type
const particleIcons: Record<string, React.ComponentType<any>> = {
  P001: GlobeAltIcon,        // http_call
  P002: CircleStackIcon,     // db_query
  P003: DocumentIcon,        // file_op
  P004: ArrowPathIcon,       // transform
  P005: ArrowsRightLeftIcon, // branch
  P006: ArrowPathRoundedSquareIcon, // loop
  P007: CpuChipIcon,         // llm_call
  P008: ArchiveBoxIcon,      // cache
  P009: QueueListIcon,       // queue
  P010: DocumentTextIcon,    // log
  // Scaffold primitives
  P011: CodeBracketIcon,     // scaffold_backend
  P012: CodeBracketIcon,     // scaffold_frontend
  P013: CircleStackIcon,     // db_model
  P014: GlobeAltIcon,        // api_route
  P015: DocumentIcon,        // ui_component
  P016: DocumentIcon,        // ui_page
  P017: GlobeAltIcon,        // websocket_handler
  P018: CodeBracketIcon,     // compile_app
}

interface ParticleNodeData {
  primitive_id: string
  name: string
  category: string
  inputs: Record<string, any>
  color?: string
  isValid?: boolean
  validationErrors?: string[]
}

function ParticleNode({ data, selected }: NodeProps<ParticleNodeData>) {
  const Icon = particleIcons[data.primitive_id] || CodeBracketIcon
  const hasErrors = data.validationErrors && data.validationErrors.length > 0

  return (
    <div
      className={clsx(
        'px-4 py-3 rounded-lg shadow-md min-w-[160px] border-2 transition-all',
        selected ? 'ring-2 ring-blue-500 ring-offset-2' : '',
        hasErrors ? 'border-red-500' : 'border-transparent'
      )}
      style={{ backgroundColor: data.color || '#6b7280' }}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-white border-2 border-gray-400"
      />

      {/* Node Content */}
      <div className="flex items-center gap-2 text-white">
        <Icon className="w-5 h-5" />
        <div>
          <div className="font-medium text-sm">{data.name}</div>
          <div className="text-xs opacity-75">{data.primitive_id}</div>
        </div>
      </div>

      {/* Validation indicator */}
      {hasErrors && (
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
          <span className="text-white text-xs font-bold">!</span>
        </div>
      )}

      {/* Valid indicator */}
      {data.isValid && !hasErrors && (
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
          <span className="text-white text-xs">✓</span>
        </div>
      )}

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-white border-2 border-gray-400"
      />
    </div>
  )
}

export default memo(ParticleNode)
