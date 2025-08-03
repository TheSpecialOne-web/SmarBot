import { ALLOWED_FILE_EXTENSIONS } from "@/const";

export const getFileExtension = (fileName: string): string => {
  if (!fileName || typeof fileName !== "string") {
    console.error("invalid file name");
    return "";
  }

  for (const ext of Object.values(ALLOWED_FILE_EXTENSIONS)) {
    if (fileName.endsWith(ext)) {
      return ext;
    }
  }
  console.error("unsupported file extension");
  return "";
};
