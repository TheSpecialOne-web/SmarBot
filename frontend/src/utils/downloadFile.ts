export const createDownloadUrl = (data: File | Blob, fileExtension?: string) => {
  const BOM = new Uint8Array([0xef, 0xbb, 0xbf]);
  let blob: Blob;
  switch (fileExtension) {
    case "csv":
      blob = new Blob([BOM, data], { type: "text/csv;charset=utf-8;" });
      break;
    default:
      blob = new Blob([data]);
      break;
  }

  const url = window.URL.createObjectURL(blob);
  return url;
};

export const downloadFile = (fileName: string, data: File | Blob) => {
  const fileExtension = fileName.split(".").length > 1 ? fileName.split(".").pop() : undefined;
  const url = createDownloadUrl(data, fileExtension);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a); // Firefoxではこのステップが必要
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};
