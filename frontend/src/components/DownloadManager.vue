<template>
  <div class="download-manager">
    <div class="upload-section">
      <h2>Upload NZB</h2>
      <div class="upload-form">
        <input type="file" @change="handleFileSelect" accept=".nzb" ref="fileInput">
        <button @click="uploadFile" :disabled="!selectedFile">Upload</button>
      </div>
    </div>

    <div class="downloads-section">
      <h2>Downloads</h2>
      <div v-if="downloads.length === 0" class="no-downloads">
        No downloads yet
      </div>
      <div v-else class="downloads-list">
        <div v-for="download in downloads" :key="download.id" class="download-item">
          <div class="download-info">
            <span class="filename">{{ download.filename }}</span>
            <span class="status" :class="download.status.toLowerCase()">{{ download.status }}</span>
            <span class="progress">{{ download.progress.toFixed(1) }}%</span>
          </div>
          <div class="download-controls">
            <button @click="pauseDownload(download.id)" v-if="download.status === 'DOWNLOADING'">Pause</button>
            <button @click="resumeDownload(download.id)" v-if="download.status === 'PAUSED'">Resume</button>
            <button @click="deleteDownload(download.id)" class="delete">Delete</button>
          </div>
          
          <!-- Add download logs component -->
          <DownloadLogs 
            v-if="download.status === 'DOWNLOADING'"
            :download-id="download.id"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import DownloadLogs from './DownloadLogs.vue'
import { getDownloads, uploadNzb, pauseDownload, resumeDownload, deleteDownload, getSystemConfig, Download } from '../lib/api'

export default defineComponent({
  name: 'DownloadManager',
  components: {
    DownloadLogs
  },
  data() {
    return {
      downloads: [] as Download[],
      selectedFile: null as File | null,
      uploadProgress: 0
    }
  },
  async mounted() {
    await this.loadConfig()
    await this.fetchDownloads()
    // Poll for updates every 5 seconds
    setInterval(this.fetchDownloads, 5000)
  },
  methods: {
    async loadConfig() {
      try {
        const config = await getSystemConfig()
        console.log('System config loaded:', config)
      } catch (error) {
        console.error('Error loading config:', error)
      }
    },
    async fetchDownloads() {
      try {
        this.downloads = await getDownloads()
      } catch (error) {
        console.error('Error fetching downloads:', error)
      }
    },
    handleFileSelect(event: Event) {
      const target = event.target as HTMLInputElement
      if (target.files && target.files.length > 0) {
        this.selectedFile = target.files[0]
      }
    },
    async uploadFile() {
      if (!this.selectedFile) return
      
      try {
        await uploadNzb(this.selectedFile)
        this.selectedFile = null
        if (this.$refs.fileInput) {
          (this.$refs.fileInput as HTMLInputElement).value = ''
        }
        await this.fetchDownloads()
      } catch (error) {
        console.error('Error uploading file:', error)
      }
    },
    async pauseDownload(id: number) {
      try {
        await pauseDownload(id)
        await this.fetchDownloads()
      } catch (error) {
        console.error('Error pausing download:', error)
      }
    },
    async resumeDownload(id: number) {
      try {
        await resumeDownload(id)
        await this.fetchDownloads()
      } catch (error) {
        console.error('Error resuming download:', error)
      }
    },
    async deleteDownload(id: number) {
      try {
        await deleteDownload(id)
        await this.fetchDownloads()
      } catch (error) {
        console.error('Error deleting download:', error)
      }
    }
  }
})
</script>

<style scoped>
.download-manager {
  padding: 20px;
}

.upload-section {
  margin-bottom: 30px;
}

.upload-form {
  display: flex;
  gap: 10px;
  align-items: center;
}

.downloads-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.no-downloads {
  text-align: center;
  padding: 20px;
  background: #2d2d2d;
  border-radius: 4px;
  color: #666;
}

.download-item {
  background: #2d2d2d;
  padding: 15px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.download-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.filename {
  flex: 1;
  font-weight: 500;
}

.status {
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 0.9em;
}

.status.downloading { background: #17a2b8; }
.status.completed { background: #28a745; }
.status.paused { background: #ffc107; }
.status.failed { background: #dc3545; }

.download-controls {
  display: flex;
  gap: 10px;
}

button {
  padding: 5px 15px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  background: #4a4a4a;
  color: white;
}

button:hover {
  background: #5a5a5a;
}

button.delete {
  background: #dc3545;
}

button.delete:hover {
  background: #c82333;
}

button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}
</style>
