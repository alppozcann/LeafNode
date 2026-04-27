
const STATUS_MAP = {
  pending: { label: 'Waiting', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' },
  sent:    { label: 'Sent',    color: 'bg-blue-100 text-blue-700 border-blue-200' },
  acked:   { label: 'Done',    color: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
}

function timeAgo(date) {
  const seconds = Math.floor((new Date() - new Date(date)) / 1000);
  if (seconds < 60) return `${seconds} seconds ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return `Yesterday at ${new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  return `${new Date(date).toLocaleDateString([], { month: 'short', day: 'numeric' })} at ${new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}

function formatAckTime(date) {
  const d = new Date(date);
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();
  const yesterday = new Date(now); yesterday.setDate(now.getDate() - 1);
  const isYesterday = d.toDateString() === yesterday.toDateString();
  const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (isToday) return `Today at ${time}`;
  if (isYesterday) return `Yesterday at ${time}`;
  return `${d.toLocaleDateString([], { month: 'short', day: 'numeric' })} at ${time}`;
}

export default function CommandHistory({ commands }) {
  if (!commands || commands.length === 0) return null

  return (
    <div className="card p-6">
      <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-4">Command History</h3>
      <div className="space-y-2">
        {commands.map((cmd) => {
          const status = STATUS_MAP[cmd.status] || { label: cmd.status, color: '' }
          return (
            <div key={cmd.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30">
              <div className="flex flex-col">
                <span className="font-mono text-sm font-bold text-gray-700 dark:text-gray-300 uppercase">
                  {cmd.cmd} {cmd.params?.times ? `(x${cmd.params.times})` : ''}
                </span>
                <span className="text-[10px] text-gray-400">
                  {timeAgo(cmd.created_at)}
                </span>
              </div>
              
              <div className="flex flex-col items-end gap-1">
                <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold uppercase tracking-wider ${status.color}`}>
                  {status.label}
                </span>
                {cmd.acked_at && (
                  <span className="text-[9px] text-gray-400">
                    Ack: {formatAckTime(cmd.acked_at)}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
