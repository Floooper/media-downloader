<template>
  <div class="download-logs">
    <div class="log-header">
      <h3>Download Progress</h3>
      <div class="controls">
        <button @click="clearLogs">Clear</button>
        <button @click="toggleAutoscroll">
          {{ autoscroll ? 'Disable Autoscroll' : 'Enable Autoscroll' }}
        </button>
      </div>
    </div>
    <div ref="logContainer" class="log-container" @scroll="handleScroll">
      <div v-for="(log, index) in logs" :key="index" :class="['log-entry', log.level.toLowerCase()]">
        <span class="timestamp">{{ formatTimestamp(log.timestamp) }}</span>
        <span class="level">{{ log.level }}</span>
        <span class="message">{{ log.message }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DownloadLogs',
  props: {
    downloadId: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      logs: [],
      socket: null,
      autoscroll: true,
      maxLogs: 1000 // Maximum number of logs to keep
    }
  },
  mounted() {
    this.connectWebSocket()
  },
  beforeUnmount() {
    if (this.socket) {
      this.socket.close()
    }
  },
  methods: {
    connectWebSocket() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/${this.downloadId}`
      
      this.socket = new WebSocket(wsUrl)
      
      this.socket.onmessage = (event) => {
        const log = JSON.parse(event.data)
        this.addLog(log)
      }
      
      this.socket.onclose = () => {
        // Attempt to reconnect after 1 second
        setTimeout(() => this.connectWebSocket(), 1000)
      }
    },
    addLog(log) {
      this.logs.push(log)
      
      // Trim logs if they exceed maxLogs
      if (this.logs.length > this.maxLogs) {
        this.logs = this.logs.slice(-this.maxLogs)
      }
      
      // Scroll to bottom if autoscroll is enabled
      this.$nextTick(() => {
        if (this.autoscroll) {
          this.scrollToBottom()
        }
      })
    },
    clearLogs() {
      this.logs = []
    },
    toggleAutoscroll() {
      this.autoscroll = !this.autoscroll
      if (this.autoscroll) {
        this.scrollToBottom()
      }
    },
    scrollToBottom() {
      const container = this.$refs.logContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },
    handleScroll(event) {
      const container = event.target
      const atBottom = container.scrollHeight - container.scrollTop === container.clientHeight
      this.autoscroll = atBottom
    },
    formatTimestamp(timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    }
  }
}
</script>

<style scoped>
.download-logs {
  background-color: #1e1e1e;
  border-radius: 4px;
  margin: 10px 0;
  height: 400px;
  display: flex;
  flex-direction: column;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #2d2d2d;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
}

.log-header h3 {
  margin: 0;
  color: #fff;
}

.controls button {
  margin-left: 10px;
  padding: 5px 10px;
  background-color: #363636;
  border: 1px solid #4a4a4a;
  color: #fff;
  border-radius: 3px;
  cursor: pointer;
}

.controls button:hover {
  background-color: #4a4a4a;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  font-family: monospace;
  font-size: 12px;
}

.log-entry {
  padding: 2px 5px;
  margin: 2px 0;
  display: flex;
  align-items: flex-start;
  color: #d4d4d4;
}

.log-entry .timestamp {
  color: #666;
  margin-right: 10px;
  flex-shrink: 0;
}

.log-entry .level {
  width: 70px;
  margin-right: 10px;
  flex-shrink: 0;
}

.log-entry .message {
  white-space: pre-wrap;
  word-break: break-word;
}

.log-entry.debug .level { color: #6c757d; }
.log-entry.info .level { color: #17a2b8; }
.log-entry.warning .level { color: #ffc107; }
.log-entry.error .level { color: #dc3545; }
</style>
