export const ALLOWED_FILE_TYPES = {
  PDF: "application/pdf",
  DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  TXT: "text/plain",
  OTHER: "application/octet-stream",
};

export const ALLOWED_FILE_TYPES_V2 = {
  PDF: "application/pdf",
  DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  TXT: "text/plain",
  DOC: "application/msword",
  XLS: "application/vnd.ms-excel",
  PPT: "application/vnd.ms-powerpoint",
  XLSM: "application/vnd.ms-excel.sheet.macroenabled.12",
  XDW: "application/vnd.fujifilm.fb.docuworks",
  OTHER: "application/octet-stream",
};

export const ALLOWED_FILE_EXTENSIONS = {
  PDF: "pdf",
  DOCX: "docx",
  XLSX: "xlsx",
  PPTX: "pptx",
  TXT: "txt",
};

export const ALLOWED_FILE_EXTENSIONS_V2 = {
  PDF: "pdf",
  DOCX: "docx",
  XLSX: "xlsx",
  PPTX: "pptx",
  TXT: "txt",
  DOC: "doc",
  XLS: "xls",
  PPT: "ppt",
  XLSM: "xlsm",
  XDW: "xdw",
};

export const ALLOWED_ATTACHMENT_FILE_EXTENSIONS_FOR_PYPDF = {
  PDF: "pdf",
  DOCX: "docx",
  XLSX: "xlsx",
  PPTX: "pptx",
};

export const ALLOWED_ATTACHMENT_FILE_EXTENSIONS_IMAGE = {
  PNG: "png",
  JPG: "jpg",
  JPEG: "jpeg",
  BMP: "bmp",
  TIFF: "tiff",
  HEIF: "heif",
};

export const ALLOWED_ATTACHMENT_FILE_EXTENSIONS = {
  ...ALLOWED_ATTACHMENT_FILE_EXTENSIONS_FOR_PYPDF,
  ...ALLOWED_ATTACHMENT_FILE_EXTENSIONS_IMAGE,
};

export const SENSITIVE_CONTENTS = {
  phone_number: "電話番号",
  email: "メールアドレス",
  postal_code: "郵便番号",
  my_number: "マイナンバー",
  credit_card: "クレジットカード番号",
} as const;

export const TOPBAR_HEIGHT = 64;
export const MOBILE_WIDTH = 600;
export const TABLET_WIDTH = 900;
export const CHAT_LAYOUT_SIDEBAR_WIDTH = 260;
export const MANAGEMENT_SIDEBAR_WIDTH = 240;
export const BOTS_SEARCH_TABS_HEIGHT = 210;

export const FIRST_YEAR = 2023;

export const CONVERTIBLE_TO_PDF = ["xlsx", "pptx", "docx"];

export const BROWSER = {
  IE: "IE",
  Edge: "Edge",
  Chrome: "Chrome",
  Safari: "Safari",
  Firefox: "Firefox",
  Other: "Other",
} as const;

export const enum ERROR {
  UNAUTHORIZED = "UNAUTHORIZED",
  FORBIDDEN = "FORBIDDEN",
  NOT_FOUND = "NOT_FOUND",
  INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR",
  BAD_REQUEST = "BAD_REQUEST",
  UNPROCESSABLE_ENTITY = "UNPROCESSABLE_ENTITY",
  SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE",
  NETWORK_ERROR = "NETWORK_ERROR",
  UNKNOWN = "UNKNOWN",
}

export const DEFAULT_MAX_CONVERSATION_TURNS = 5;

export const INITIAL_ASSISTANTS_DISPLAY_COUNT = 18;
