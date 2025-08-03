import FileDownloadOutlinedIcon from "@mui/icons-material/FileDownloadOutlined";
import { Box } from "@mui/material";

import { ChatIconButton } from "@/components/buttons/ChatIconButton";
import { CircularLoading } from "@/components/loadings/CircularLoading";

type Props = {
  tooltipTitle?: string;
  isDownloading?: boolean;
  onClickDownload: () => void;
};

export const DownloadButton = ({ tooltipTitle, isDownloading, onClickDownload }: Props) => {
  return isDownloading ? (
    <Box width="fit-content">
      <CircularLoading size={24} sx={{ p: 1 }} />
    </Box>
  ) : (
    <ChatIconButton
      tooltipTitle={tooltipTitle || "ダウンロード"}
      onClick={onClickDownload}
      icon={<FileDownloadOutlinedIcon />}
    />
  );
};
