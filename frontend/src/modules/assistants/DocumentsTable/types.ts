import {
  Document,
  DocumentFolder,
  DocumentFolderWithDocumentProcessingStats,
} from "@/orval/models/backend-api";
import { Diff } from "@/types/object";

type DocumentUniqueProps = Diff<Document, DocumentFolder>;
type DocumentFolderUniqueProps = Diff<DocumentFolder, Document>;

type NullifiedDocumentUniqueProps = { [k in keyof Required<DocumentUniqueProps>]: null };
type NullifiedDocumentFolderUniqueProps = {
  [k in keyof Required<DocumentFolderUniqueProps>]: null;
};

type DocumentRow = NullifiedDocumentFolderUniqueProps &
  Document & {
    type: "document";
  };

type DocumentFolderRow = NullifiedDocumentUniqueProps &
  DocumentFolderWithDocumentProcessingStats & {
    type: "documentFolder";
  };
type ExternalDocumentFolderRow = Required<
  Pick<DocumentFolder, "external_id" | "external_data_connection_type">
> &
  NullifiedDocumentUniqueProps &
  DocumentFolder & {
    type: "externalDocumentFolder";
  };

export type TableRow = DocumentRow | DocumentFolderRow | ExternalDocumentFolderRow;

export const isDocument = (row: TableRow): row is DocumentRow => row.type === "document";
export const isDocumentFolder = (row: TableRow): row is DocumentFolderRow =>
  row.type === "documentFolder";
export const isExternalDocumentFolder = (row: TableRow): row is ExternalDocumentFolderRow =>
  row.type === "externalDocumentFolder";

export const createNullifiedDocument = (): NullifiedDocumentUniqueProps =>
  Object.fromEntries(
    Object.keys({} as DocumentUniqueProps).map(key => [key, null]),
  ) as NullifiedDocumentUniqueProps;

export const createNullifiedDocumentFolder = (): NullifiedDocumentFolderUniqueProps =>
  Object.fromEntries(
    Object.keys({} as DocumentFolderUniqueProps).map(key => [key, null]),
  ) as NullifiedDocumentFolderUniqueProps;
