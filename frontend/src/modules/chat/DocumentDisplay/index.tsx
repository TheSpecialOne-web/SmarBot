import DownloadIcon from "@mui/icons-material/Download";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import { Box, IconButton, Link, Stack, Typography } from "@mui/material";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { CircularLoading } from "@/components/loadings/CircularLoading";
import { CONVERTIBLE_TO_PDF } from "@/const";
import { DocumentToDisplay } from "@/types/document";

import { FolderMenu } from "./FolderMenu";

const TITLE_STACK_HEIGHT = "55px";

type Props = {
  loading: boolean;
  error: boolean;
  documentToDisplay: DocumentToDisplay | null;
  onMoveToFolder?: (folderId: string | null) => void;
  displayLinkAsText?: boolean;
};

export const DocumentDisplay = ({
  documentToDisplay,
  loading,
  error,
  onMoveToFolder,
  displayLinkAsText = false,
}: Props) => {
  const downloadFile = (url: string) => {
    const a = document.createElement("a");
    a.href = url;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  if (loading || documentToDisplay === null) {
    return (
      <Stack height="100%" justifyContent="center" alignItems="center">
        <CircularLoading />
      </Stack>
    );
  }

  if (error) {
    return (
      <Typography
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%,-50%)",
        }}
        variant="h4"
      >
        ドキュメントの読み込みに失敗しました。
      </Typography>
    );
  }

  return (
    <Box height="100%" overflow="hidden">
      <Box height={`calc(100% - ${TITLE_STACK_HEIGHT})`}>
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          px={2}
          height={TITLE_STACK_HEIGHT}
        >
          <Typography variant="h6" py={2}>
            {documentToDisplay.name}.{documentToDisplay.extension}
          </Typography>
          <Stack direction="row" alignItems="center">
            {documentToDisplay.downloadUrl &&
              documentToDisplay.documentFolderDetail &&
              onMoveToFolder && (
                <FolderMenu
                  documentToDisplay={{
                    ...documentToDisplay,
                    documentFolderDetail: documentToDisplay.documentFolderDetail,
                  }}
                  onMoveToFolder={onMoveToFolder}
                />
              )}
            {documentToDisplay.displayUrl && (
              <>
                {displayLinkAsText ? (
                  <Link
                    href={documentToDisplay.displayUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    variant="h6"
                  >
                    該当ページ参照はこちら
                  </Link>
                ) : (
                  <IconButtonWithTooltip
                    tooltipTitle={documentToDisplay.externalUrl ? "外部データソースを開く" : "別タブで開く"}
                    icon={<OpenInNewIcon fontSize="small" />}
                    iconButtonSx={{ fontsize: "small" }}
                    onClick={() => {
                      window.open(
                        documentToDisplay.externalUrl ?? documentToDisplay.displayUrl,
                        "_blank",
                        "noopener noreferrer",
                      );
                    }}
                  />
                )}
              </>
            )}
            {CONVERTIBLE_TO_PDF.includes(documentToDisplay.extension) && (
              <Stack direction="row" alignItems="center">
                <IconButton
                  onClick={() => {
                    downloadFile(documentToDisplay.downloadUrl);
                  }}
                  sx={{ borderRadius: 4, gap: 1 }}
                >
                  <DownloadIcon fontSize="small" />
                  <Typography variant="caption" sx={{ whiteSpace: "nowrap" }}>
                    元ファイルをダウンロード
                  </Typography>
                </IconButton>
              </Stack>
            )}
          </Stack>
        </Stack>
        {documentToDisplay.displayUrl ? (
          <iframe
            title="Citation"
            src={documentToDisplay.displayUrl + "#view=FitH"}
            width="100%"
            height="100%"
          />
        ) : (
          <Stack
            p={2}
            spacing={1}
            sx={{ borderTopStyle: "solid", borderWidth: 1.5, borderColor: "drawerBackground.main" }}
          >
            <Typography variant="h5">
              このドキュメントはプレビューが作成中のため、表示できません。
            </Typography>
            <Typography variant="caption" fontSize={14}>
              ※2024年06月22日以前に追加された xlsx, pptx, docx
              のドキュメントはプレビュー表示に対応していません。
              <br />
              プレビューを利用したい場合はドキュメントを再追加していただく必要があります。
            </Typography>
          </Stack>
        )}
      </Box>
    </Box>
  );
};
