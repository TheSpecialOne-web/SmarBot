const BYTES_PER_KB = 1024;
const BYTES_PER_MB = BYTES_PER_KB * 1024;
const BYTES_PER_GB = BYTES_PER_MB * 1024;

export const formatBytes = (bytes: number, decimals = 2) => {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
};

export const bytesToGb = (bytes: number) => {
  return bytes / BYTES_PER_GB;
};

export const gbToBytes = (gb: number) => {
  return gb * BYTES_PER_GB;
};

export const formatStorageUsage = (bytes: number, decimals = 2) => {
  const ranges = [
    100 * BYTES_PER_KB, // 100KB
    500 * BYTES_PER_KB,
    1 * BYTES_PER_MB, // 1MB
    5 * BYTES_PER_MB,
    10 * BYTES_PER_MB,
    100 * BYTES_PER_MB,
    500 * BYTES_PER_MB,
    1 * BYTES_PER_GB, // 1GB
  ];

  for (let i = 0; i < ranges.length; i++) {
    if (bytes < ranges[i]) {
      return `${formatBytes(ranges[i], decimals)} 未満`;
    }
  }
  return `${formatBytes(ranges[ranges.length - 1], decimals)} 以上`;
};
