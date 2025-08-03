import { useState } from "react";

import { DocumentFolder, ExternalDataConnectionType } from "@/orval/models/backend-api";

import { GetExternalDocumentFolderForm } from "./GetExternalDocumentFolderForm";
import { StartExternalDataSyncForm } from "./StartExternalDataSyncForm";

type Props = {
  externalDataConnectionType: ExternalDataConnectionType;
  botId: number;
  parentDocumentFolderId: DocumentFolder["id"] | null;
  refetch: () => void;
  onClose: () => void;
};

export const ExternalDocumentFolderForm = ({
  externalDataConnectionType,
  botId,
  parentDocumentFolderId,
  refetch,
  onClose,
}: Props) => {
  const [folderName, setFolderName] = useState<string | null>(null);
  const [externalId, setExternalId] = useState<string | null>(null);

  return folderName === null || externalId === null ? (
    <GetExternalDocumentFolderForm
      externalDataConnectionType={externalDataConnectionType}
      botId={botId}
      parentDocumentFolderId={parentDocumentFolderId}
      setFolderName={setFolderName}
      setExternalId={setExternalId}
    />
  ) : (
    <StartExternalDataSyncForm
      externalDataConnectionType={externalDataConnectionType}
      parentDocumentFolderId={parentDocumentFolderId}
      botId={botId}
      folderName={folderName}
      externalId={externalId}
      refetch={refetch}
      onClose={onClose}
    />
  );
};
