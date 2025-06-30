import axios from 'axios';

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: '/api',  // Use proxy instead of direct backend URL
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create a separate axios instance for database operations with longer timeout
export const dbApi = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 minutes for database operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create a separate axios instance for matching operations with longer timeout
export const matchingApi = axios.create({
  baseURL: '/api',
  timeout: 180000, // 3 minutes for matching operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create a separate axios instance for cancellation operations with shorter timeout
export const cancellationApi = axios.create({
  baseURL: '/api',
  timeout: 5000, // 5 seconds for cancellation requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// SSE Event types
export interface SSEEvent {
  type: 'start' | 'website_start' | 'project' | 'website_complete' | 'complete' | 'error' | 'info' | 'progress' | 'deduplication' | 'cancelled';
  message?: string;
  website?: string;
  data?: any;
  projects?: number;
  total_projects?: number;
  errors?: string[];
  result?: any;
  scan_id?: string;
}

// SSE Event handler type
export type SSEEventHandler = (event: SSEEvent) => void;

// SSE Streaming class
export class SSEStream {
  private eventSource: EventSource | null = null;
  private isConnected = false;
  private hasCompleted = false;
  private isDisconnecting = false;
  private preventReconnect = false; // New flag to prevent reconnection after completion
  private connectionAttempts = 0;
  private maxReconnectAttempts = 3;

  constructor(private url: string, private onEvent: SSEEventHandler) {}

  connect(): void {
    if (this.isConnected) {
      this.disconnect();
    }

    // Don't reconnect if we've completed normally
    if (this.preventReconnect) {
      console.log('SSE: Preventing reconnection after normal completion');
      return;
    }

    // Don't reconnect if we've exceeded max attempts
    if (this.connectionAttempts >= this.maxReconnectAttempts) {
      console.log('SSE: Max reconnection attempts reached, not reconnecting');
      return;
    }

    console.log('SSE: Connecting to:', this.url);
    this.eventSource = new EventSource(this.url);
    this.isConnected = true;
    this.hasCompleted = false;
    this.isDisconnecting = false;
    this.connectionAttempts++;

    this.eventSource.onmessage = (event) => {
      console.log('SSE: Raw message received:', event.data);
      try {
        const data: SSEEvent = JSON.parse(event.data);
        console.log('SSE: Parsed event data:', data);

        // Track completion status
        if (data.type === 'complete') {
          this.hasCompleted = true;
          this.preventReconnect = true; // Prevent future reconnections
          console.log('SSE: Scan completed, will close connection and prevent reconnection');
        }

        this.onEvent(data);
      } catch (error) {
        console.error('SSE: Error parsing SSE event:', error);
        console.error('SSE: Raw data was:', event.data);
      }
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE: Connection error:', error);
      this.isConnected = false;

      // Only treat as error if we haven't completed normally and aren't disconnecting
      if (!this.hasCompleted && !this.isDisconnecting) {
        // Check if we should attempt reconnection
        if (this.connectionAttempts < this.maxReconnectAttempts) {
          console.log(`SSE: Connection lost, attempting reconnection (${this.connectionAttempts}/${this.maxReconnectAttempts})`);
          // Don't immediately reconnect, let the browser handle it
          setTimeout(() => {
            if (!this.preventReconnect && !this.hasCompleted) {
              this.connect();
            }
          }, 1000);
        } else {
          console.log('SSE: Max reconnection attempts reached, treating as error');
          this.onEvent({ type: 'error', message: 'Connection lost after multiple attempts' });
        }
      } else {
        console.log('SSE: Connection closed after normal completion or manual disconnect');
      }
    };

    this.eventSource.onopen = () => {
      console.log('SSE: Connection established');
      // Reset connection attempts on successful connection
      this.connectionAttempts = 0;
    };
  }

  disconnect(): void {
    console.log('SSE: Disconnecting...');
    this.isDisconnecting = true;
    this.isConnected = false;

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    console.log('SSE: Disconnected');
  }

  // Method to reset the stream for a new scan
  reset(): void {
    console.log('SSE: Resetting stream for new scan');
    this.preventReconnect = false;
    this.hasCompleted = false;
    this.isDisconnecting = false;
    this.isConnected = false;
    this.connectionAttempts = 0;
  }

  // Method to force disconnect and prevent reconnection
  forceDisconnect(): void {
    console.log('SSE: Force disconnecting and preventing reconnection');
    this.preventReconnect = true;
    this.hasCompleted = true;
    this.isDisconnecting = true;
    this.isConnected = false;
    this.connectionAttempts = this.maxReconnectAttempts; // Prevent any reconnection attempts

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    console.log('SSE: Force disconnected');
  }

  isConnectedStatus(): boolean {
    return this.isConnected;
  }
}

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    // Only log non-GET requests or important GET requests
    if (config.method !== 'get' || config.url?.includes('/scan/') || config.url?.includes('/deduplication')) {
      console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    if (error.response) {
      // Server responded with error status
      console.error('Error data:', error.response.data);
    } else if (error.request) {
      // Request was made but no response received
      console.error('No response received');
    } else {
      // Something else happened
      console.error('Error setting up request:', error.message);
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  // Health
  health: '/health',

  // Projects
  projects: '/projects',
  project: (id: number) => `/projects/${id}`,

  // Employees
  employees: '/employees',
  employee: (id: number) => `/employees/${id}`,

  // App State
  appState: (key: string) => `/state/${key}`,

  // Scanning
  scan: (timeRange: number) => `/scan/${timeRange}`,
  scanStream: (timeRange: number) => `/scan/stream/${timeRange}`,
  scanStatus: '/scan/status',
  cancelScan: (scanId: string) => `/scan/cancel/${scanId}`,

  // Matching
  matches: (employeeId: number) => `/matches/${employeeId}`,

  // Embeddings
  rebuildEmbeddings: '/embeddings/rebuild',

  // Database Inspection
  databaseTables: '/database/tables',
  databaseTable: (tableName: string) => `/database/table/${tableName}`,

  // Deduplication
  deduplication: '/deduplication',

  // Test Data
  testData: '/test-data',
};

export default api;