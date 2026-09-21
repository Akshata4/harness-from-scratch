import { Context } from '@deepseek-ai/cordis'

/**
 * Plugin configuration interface
 */
export interface BreakReminderConfig {
  /** Interval in minutes between break reminders (default: 20) */
  intervalMinutes?: number
}

/**
 * Break Reminder Plugin
 * 
 * A friendly plugin that reminds you to take breaks at regular intervals
 * while the harness is running.
 */
export const name = 'break-reminder'

export const inject = ['timer']

export function apply(ctx: Context, config: BreakReminderConfig = {}) {
  // Set default configuration
  const intervalMinutes = config.intervalMinutes ?? 20
  const intervalMs = intervalMinutes * 60 * 1000

  // Log startup message
  console.log(`[break-reminder] Plugin activated. Reminding every ${intervalMinutes} minutes.`)

  // Create the repeating timer using ctx.interval for automatic cleanup
  ctx.interval(() => {
    const now = new Date()
    const timestamp = now.toLocaleTimeString()
    
    console.log(`\n💡 [${timestamp}] Break Reminder:`)
    console.log("   Time to take a short break!")
    console.log("   • Stand up and stretch")
    console.log("   • Look away from the screen")
    console.log("   • Hydrate and refresh")
    console.log("   • You've earned it! 🌟\n")
  }, intervalMs)
}

