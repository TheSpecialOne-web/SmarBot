import { getFileNameAndExtensionFromBlobName } from "@/libs/files";
import { DataConsolePanel } from "@/modules/assistants/DocumentManagement/DocumentDisplayPanel/DataConsolePanel";
import { useGetCommonDocumentTemplateUrl } from "@/orval/administrator-api";
import { BotTemplate, CommonDocumentTemplate } from "@/orval/models/administrator-api";
import { DocumentToDisplay } from "@/types/document";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  botTemplateId: BotTemplate["id"];
  document: CommonDocumentTemplate;
};

export const CommonDocumentTemplateDataConsolePanel = ({
  isOpen,
  onClose,
  botTemplateId,
  document,
}: Props) => {
  const {
    data,
    error: getUrlError,
    isValidating: isLoadingGetUrl,
  } = useGetCommonDocumentTemplateUrl(botTemplateId, document.id);

  const url = data?.url;
  if (!url) {
    return null;
  }

  // ドキュメント名と拡張子を分割
  const { name: documentName, extension: documentExtension } = getFileNameAndExtensionFromBlobName(
    document.blob_name,
  );

  const documentToDisplay: DocumentToDisplay = {
    name: documentName,
    extension: documentExtension,
    displayUrl: url,
    downloadUrl: url,
  };

  return (
    <DataConsolePanel
      open={isOpen}
      onClose={onClose}
      isLoading={isLoadingGetUrl}
      documentToDisplay={documentToDisplay}
      readPdfError={Boolean(getUrlError)}
    />
  );
};
