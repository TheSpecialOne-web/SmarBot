import { SharepointLogoIcon } from "@fluentui/react-icons-mdl2-branded";
import CloudSyncRoundedIcon from "@mui/icons-material/CloudSyncRounded";
import { SiGoogledrive } from "react-icons/si";

import { BoxLogoIcon } from "@/components/icons/BoxLogoIcon";
import { ExternalDataConnectionType } from "@/orval/models/backend-api";
import { theme } from "@/theme";

type Props = {
  externalDataConnectionType?: ExternalDataConnectionType;
};

export const ExternalDocumentFolderIcon = ({ externalDataConnectionType }: Props) => {
  switch (externalDataConnectionType) {
    case ExternalDataConnectionType.sharepoint:
      return <SharepointLogoIcon style={{ fontSize: 24, color: theme.palette.secondary.main }} />;
    case ExternalDataConnectionType.box:
      return <BoxLogoIcon color="secondary" />;
    case ExternalDataConnectionType.google_drive:
      return <SiGoogledrive size={20} color={theme.palette.secondary.main} />;
    default:
      return <CloudSyncRoundedIcon color="secondary" />;
  }
};
