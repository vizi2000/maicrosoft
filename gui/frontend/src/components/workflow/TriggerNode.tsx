/**
 * TriggerNode - Custom node for workflow triggers
 * Types: manual, webhook, schedule, event
 */

import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import {
  PlayIcon,
  BoltIcon,
  ClockIcon,
  BellIcon,
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

const triggerIcons: Record<string, React.ComponentType<any>> = {
  manual: PlayIcon,
  webhook: BoltIcon,
  schedule: ClockIcon,
  event: BellIcon,
}

const triggerColors: Record<string, string> = {
  manual: '#22c55e',    // green
  webhook: '#f59e0b',   // amber
  schedule: '#3b82f6',  // blue
  event: '#8b5cf6',     // purple
}

interface TriggerNodeData {
  trigger_type: 'manual' | 'webhook' | 'schedule' | 'event'
  config: Record<string, any>
}

function TriggerNode({ data, selected }: NodeProps<TriggerNodeData>) {
  const Icon = triggerIcons[data.trigger_type] || PlayIcon
  const color = triggerColors[data.trigger_type] || '#22c55e'

  const getLabel = () => {
    switch (data.trigger_type) {
      case 'manual':
        return 'Manual Start'
      case 'webhook':
        return `Webhook: ${data.config?.path || '/webhook'}`
      case 'schedule':
        return `Schedule: ${data.config?.cron || '* * * * *'}`
      case 'event':
        return `Event: ${data.config?.event_type || 'custom'}`
      default:
        return 'Trigger'
    }
  }

  return (
    <div
      className={clsx(
        'px-4 py-3 rounded-full shadow-md min-w-[140px] border-2 transition-all',
        selected ? 'ring-2 ring-blue-500 ring-offset-2' : 'border-transparent'
      )}
      style={{ backgroundColor: color }}
    >
      {/* Node Content */}
      <div className="flex items-center gap-2 text-white">
        <Icon className="w-5 h-5" />
        <div>
          <div className="font-medium text-sm">{getLabel()}</div>
          <div className="text-xs opacity-75">Trigger</div>
        </div>
      </div>

      {/* Output Handle only (triggers don't have inputs) */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-white border-2 border-gray-400"
      />
    </div>
  )
}

export default memo(TriggerNode)
