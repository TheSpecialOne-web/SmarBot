import { DocumentFolderDetail } from "@/orval/models/backend-api";

export type DocumentToDisplay = {
  name: string;
  extension: string;
  displayUrl: string;
  downloadUrl: string;
  externalUrl?: string;
  documentFolderDetail?: DocumentFolderDetail;
};
