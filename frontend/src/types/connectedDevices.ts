export interface ConnectedDevice {
  id: string;
  device: string;
  ipFingerprint: string;
  createdAt: string;
  lastSeenAt: string;
  isCurrent: boolean;
}
