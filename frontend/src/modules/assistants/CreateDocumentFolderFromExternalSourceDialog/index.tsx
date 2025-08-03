import { SharepointLogoIcon } from "@fluentui/react-icons-mdl2-branded";
import CancelOutlinedIcon from "@mui/icons-material/CancelOutlined";
import { IconButton, Tab, Tabs } from "@mui/material";
import { useState } from "react";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { BoxLogoIcon } from "@/components/icons/BoxLogoIcon";
import { Spacer } from "@/components/spacers/Spacer";
import { DocumentFolder, ExternalDataConnectionType } from "@/orval/models/backend-api";

import { ExternalDocumentFolderForm } from "./ExternalDocumentFolderForm";

type Props = {
  botId: number;
  open: boolean;
  parentDocumentFolderId: DocumentFolder["id"] | null;
  onClose: () => void;
  refetch: () => void;
};

export const CreateDocumentFolderFromExternalSourceDialog = ({
  botId,
  open,
  parentDocumentFolderId,
  onClose,
  refetch,
}: Props) => {
  const [selectedExternalDataSource, setSelectedExternalDataSource] =
    useState<ExternalDataConnectionType>(ExternalDataConnectionType.sharepoint);

  return (
    <CustomDialog
      open={open}
      onClose={onClose}
      title="外部データソースからフォルダを追加"
      titleActions={
        <IconButton onClick={onClose} sx={{ p: 0 }}>
          <CancelOutlinedIcon fontSize="small" />
        </IconButton>
      }
    >
      <CustomDialogContent>
        <Tabs
          value={selectedExternalDataSource}
          onChange={(_, value) => setSelectedExternalDataSource(value)}
        >
          <Tab
            label="SharePoint"
            value={ExternalDataConnectionType.sharepoint}
            icon={<SharepointLogoIcon style={{ height: 25, width: 25 }} />}
          />
          <Tab
            label="Box"
            value={ExternalDataConnectionType.box}
            icon={<BoxLogoIcon fontSize="large" />}
          />
        </Tabs>
        <Spacer px={16} />
        <ExternalDocumentFolderForm
          key={selectedExternalDataSource} // Force re-render and reset form when switching tabs
          externalDataConnectionType={selectedExternalDataSource}
          botId={botId}
          parentDocumentFolderId={parentDocumentFolderId}
          refetch={refetch}
          onClose={onClose}
        />
      </CustomDialogContent>
    </CustomDialog>
  );
};
