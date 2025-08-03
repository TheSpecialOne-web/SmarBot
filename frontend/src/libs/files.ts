import {
  ALLOWED_FILE_EXTENSIONS,
  ALLOWED_FILE_EXTENSIONS_V2,
  ALLOWED_FILE_TYPES,
  ALLOWED_FILE_TYPES_V2,
} from "@/const";
import { Document } from "@/orval/models/backend-api";

export enum FileValidationType {
  Empty = "empty",
  Invalid = "invalid",
  Duplicated = "duplicated",
}

export const getFileNameAndExtension = (file: File) => {
  const extension = file.name.split(".").pop();
  if (!extension) {
    return {
      baseName: file.name.normalize("NFC"),
      extension: null,
    };
  }
  const baseName = file.name.slice(0, -extension.length - 1).normalize("NFC");
  return {
    baseName: baseName,
    extension: extension.toLowerCase(),
  };
};

export const getFileNameAndExtensionFromBlobName = (blobName: string) => {
  const extension = blobName.split(".").pop();
  if (!extension) {
    return {
      name: blobName.normalize("NFC"),
      extension: "",
    };
  }
  const name = blobName.slice(0, -extension.length - 1).normalize("NFC");
  return {
    name: name,
    extension,
  };
};

// ALLOWED_FILE_EXTENSIONS と ALLOWED_FILE_TYPES を使う
export const validateFile = (
  newFile: File,
  selectedFiles: File[],
  existingDocuments: Document[],
) => {
  const { extension, baseName } = getFileNameAndExtension(newFile);
  const fileType = newFile.type;

  if (!extension) {
    return {
      type: FileValidationType.Invalid,
    };
  }

  if (!Object.values(ALLOWED_FILE_EXTENSIONS).includes(extension)) {
    return {
      type: FileValidationType.Invalid,
    };
  }

  // ファイル名が空の場合
  if (baseName === "") {
    return {
      type: FileValidationType.Empty,
    };
  }

  // ファイルタイプチェック
  if (!Object.values(ALLOWED_FILE_TYPES).includes(fileType)) {
    return {
      type: FileValidationType.Invalid,
    };
  }

  // ファイル名の重複チェック
  if (selectedFiles.some(file => getFileNameAndExtension(file).baseName === baseName)) {
    return {
      type: FileValidationType.Duplicated,
    };
  }
  // 既存のファイル名との重複チェック
  if (existingDocuments.some(doc => doc.name.normalize("NFC") === baseName)) {
    return {
      type: FileValidationType.Duplicated,
    };
  }
};

// ALLOWED_FILE_EXTENSIONS_V2 と ALLOWED_FILE_TYPES_V2 を使う
export const validateFileV2 = (
  newFile: File,
  selectedFiles: File[],
  existingDocuments: Document[],
) => {
  const { extension, baseName } = getFileNameAndExtension(newFile);
  const fileType = newFile.type;

  if (!extension) {
    return {
      type: FileValidationType.Invalid,
    };
  }

  if (!Object.values(ALLOWED_FILE_EXTENSIONS_V2).includes(extension)) {
    return {
      type: FileValidationType.Invalid,
    };
  }

  // ファイル名が空の場合
  if (baseName === "" || newFile.size === 0) {
    return {
      type: FileValidationType.Empty,
    };
  }

  // ファイルタイプチェック
  if (
    !Object.values(ALLOWED_FILE_TYPES_V2).includes(fileType) &&
    extension !== ALLOWED_FILE_EXTENSIONS_V2.XDW
  ) {
    return {
      type: FileValidationType.Invalid,
    };
  }

  // ファイル名の重複チェック
  if (selectedFiles.some(file => getFileNameAndExtension(file).baseName === baseName)) {
    return {
      type: FileValidationType.Duplicated,
    };
  }
  // 既存のファイル名との重複チェック
  if (existingDocuments.some(doc => doc.name.normalize("NFC") === baseName)) {
    return {
      type: FileValidationType.Duplicated,
    };
  }
};
